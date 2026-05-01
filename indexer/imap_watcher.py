"""IMAP Watcher for Tessera AI Indexer.

Connects to an IMAP mailbox, polls for new UNSEEN emails, extracts body text
and PDF attachments, runs them through the RuleEngine, and pushes results
into the dashboard state for live display.

Uses only Python stdlib (imaplib, email) — zero additional dependencies.
"""
from __future__ import annotations

import email
import email.policy
import imaplib
import os
import re
import threading
import time
import uuid
from email.header import decode_header
from pathlib import Path
from typing import Any, Callable, Optional

INBOX_DIR = Path("data/inbox")


def _decode_header_value(raw: str | None) -> str:
    """Decode an RFC-2047 encoded header into a plain string."""
    if not raw:
        return ""
    parts = decode_header(raw)
    decoded = []
    for fragment, charset in parts:
        if isinstance(fragment, bytes):
            decoded.append(fragment.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(fragment)
    return " ".join(decoded)


def _extract_sender_name(from_header: str) -> tuple[str, str]:
    """Parse 'Display Name <email@addr>' into (name, email)."""
    match = re.match(r'^"?(.+?)"?\s*<(.+?)>$', from_header.strip())
    if match:
        return match.group(1).strip().strip('"'), match.group(2).strip()
    # Bare email address
    return from_header.strip(), from_header.strip()


def _extract_body(msg: email.message.Message) -> str:
    """Walk a MIME message and return the best plain-text body."""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            disp = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in disp:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or "utf-8"
                    return payload.decode(charset, errors="replace")
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or "utf-8"
            return payload.decode(charset, errors="replace")
    return ""


def _save_pdf_attachments(msg: email.message.Message, dest_dir: Path) -> list[dict[str, Any]]:
    """Extract PDF attachments from a MIME message and save to disk."""
    attachments: list[dict[str, Any]] = []
    for part in msg.walk():
        ct = part.get_content_type()
        disp = str(part.get("Content-Disposition", ""))
        filename = part.get_filename()

        if filename:
            filename = _decode_header_value(filename)

        if ct == "application/pdf" or (filename and filename.lower().endswith(".pdf")):
            if not filename:
                filename = f"attachment_{len(attachments) + 1}.pdf"

            payload = part.get_payload(decode=True)
            if not payload:
                continue

            dest_dir.mkdir(parents=True, exist_ok=True)
            save_path = dest_dir / filename
            save_path.write_bytes(payload)

            attachments.append({
                "name": filename,
                "path": str(save_path),
                "size_bytes": len(payload),
            })

    return attachments


def _format_size(size_bytes: int) -> str:
    """Human-readable file size."""
    if size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.1f} MB"
    return f"{size_bytes // 1024} KB"


class IMAPWatcher:
    """Background IMAP poller that feeds into DashboardState.

    Parameters
    ----------
    host : str
        IMAP server hostname (e.g. ``imap.gmail.com``).
    email_addr : str
        Login email address.
    password : str
        Login password or app-specific password.
    folder : str
        IMAP folder to watch (default ``INBOX``).
    poll_interval : int
        Seconds between polls (default 5).
    on_email : callable
        Callback ``(mail_dict, engine_result) -> None`` invoked for each new email.
        Typically ``DashboardState.push_email``.
    """

    def __init__(
        self,
        host: str,
        email_addr: str,
        password: str,
        folder: str = "INBOX",
        poll_interval: int = 5,
        on_email: Optional[Callable] = None,
    ):
        self.host = host
        self.email_addr = email_addr
        self.password = password
        self.folder = folder
        self.poll_interval = poll_interval
        self.on_email = on_email

        self._conn: Optional[imaplib.IMAP4_SSL] = None
        self._engine = None
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None

    # ── Connection management ──────────────────────────────────────────

    def _connect(self) -> None:
        """Establish (or re-establish) the IMAP connection."""
        try:
            if self._conn:
                try:
                    self._conn.logout()
                except Exception:
                    pass

            print(f"[imap] Connecting to {self.host} as {self.email_addr}…")
            self._conn = imaplib.IMAP4_SSL(self.host)
            self._conn.login(self.email_addr, self.password)
            self._conn.select(self.folder)
            print(f"[imap] Connected. Watching {self.folder}.")
        except Exception as exc:
            print(f"[imap] Connection failed: {exc}")
            self._conn = None
            raise

    def _ensure_engine(self) -> None:
        if self._engine is None:
            from indexer.rules.engine import RuleEngine
            self._engine = RuleEngine()

    # ── Polling loop ───────────────────────────────────────────────────

    def _poll_once(self) -> int:
        """Check for new UNSEEN messages. Returns count processed."""
        if not self._conn:
            self._connect()

        try:
            self._conn.noop()  # Keep-alive
            status, data = self._conn.search(None, "UNSEEN")
            if status != "OK":
                return 0

            msg_ids = data[0].split()
            if not msg_ids:
                return 0

            print(f"[imap] {len(msg_ids)} new email(s) found.")
            count = 0

            for msg_id in msg_ids:
                try:
                    self._process_message(msg_id)
                    count += 1
                except Exception as exc:
                    print(f"[imap] Error processing message {msg_id}: {exc}")

            return count

        except (imaplib.IMAP4.abort, imaplib.IMAP4.error, OSError) as exc:
            print(f"[imap] Connection lost: {exc}. Reconnecting…")
            self._conn = None
            return 0

    def _process_message(self, msg_id: bytes) -> None:
        """Fetch, parse, classify, and push a single message."""
        status, data = self._conn.fetch(msg_id, "(RFC822)")
        if status != "OK" or not data or not data[0]:
            return

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email, policy=email.policy.default)

        # Extract metadata
        from_header = _decode_header_value(msg.get("From", ""))
        sender_name, sender_email = _extract_sender_name(from_header)
        subject = _decode_header_value(msg.get("Subject", "(no subject)"))
        body = _extract_body(msg)
        received_time = time.strftime("%H:%M")

        # Generate unique ID
        mail_id = f"m-{uuid.uuid4().hex[:6]}"
        msg_dir = INBOX_DIR / mail_id

        # Save PDF attachments
        attachments = _save_pdf_attachments(msg, msg_dir)

        print(f"[imap] Processing: {sender_name} — {subject}")
        print(f"[imap]   Body: {len(body)} chars, {len(attachments)} PDF attachment(s)")

        # Run through the real RuleEngine
        self._ensure_engine()
        attachment_path = attachments[0]["path"] if attachments else None
        engine_result = self._engine.process_inbound(mail_id, body, attachment_path)

        # Build the dashboard mail object
        att_info = []
        for att in attachments:
            # Try to get page count from pypdf
            pages = 1
            try:
                import pypdf
                reader = pypdf.PdfReader(att["path"])
                pages = len(reader.pages)
            except Exception:
                pass
            att_info.append({
                "name": att["name"],
                "pages": pages,
                "size": _format_size(att["size_bytes"]),
            })

        if not att_info:
            att_info.append({"name": "(no attachment)", "pages": 0, "size": "0 KB"})

        # Extract classification from engine result
        tasks = engine_result.get("tasks", [])
        task = tasks[0] if tasks else {}

        confidence_raw = task.get("confidence", 0.0)
        confidence_pct = int(round(confidence_raw * 100)) if confidence_raw <= 1.0 else int(confidence_raw)
        sub_type = task.get("sub_type", "unknown")
        status_val = task.get("status", "pending")
        policy = task.get("policy_number", "UNKNOWN")
        client = task.get("client_name", "Unknown Client")
        pages_str = task.get("pages", "body only")
        method = engine_result.get("method", "unknown")

        # Map method to tier label
        tier_label = "4 (ML)"
        if "qr" in method.lower() or "tier1" in method.lower():
            tier_label = "1 (QR)"
        elif "tfidf" in method.lower():
            tier_label = "4 (TF-IDF)"
        elif "onnx" in method.lower() or "ml" in method.lower():
            tier_label = "4 (ML)"

        # Map sub_type to queue name
        queue_map = {
            "repurchase": "NEW BUSINESS",
            "new_business": "NEW BUSINESS",
            "maintenance_client": "MAINTENANCE",
            "maintenance_contrib": "MAINTENANCE",
            "claim_death": "CLAIMS",
            "claim_retirement": "CLAIMS",
            "bulk_instructions": "NEW BUSINESS",
        }
        queue_name = queue_map.get(sub_type, "NEW BUSINESS")

        note = ""
        if confidence_pct < 78:
            status_val = "needs-review"
            note = f"Confidence below threshold ({confidence_pct}%) — flagged for human review"

        mail_dict = {
            "id": mail_id,
            "from": sender_email,
            "fromName": sender_name,
            "subject": subject,
            "preview": body.replace("\n", " ")[:120] + "…" if len(body) > 120 else body.replace("\n", " "),
            "body": body,
            "received": received_time,
            "attachments": att_info,
            "routedTo": {
                "queue": queue_name,
                "item": f"{client} {sub_type}",
                "needsReview": status_val == "needs-review",
            },
            "classification": {
                "type": sub_type,
                "tier": tier_label,
                "confidence": confidence_pct,
                "status": status_val,
                "policy": policy,
                "client": client,
                "pages": pages_str,
                "note": note,
            },
        }

        # Mark as seen
        self._conn.store(msg_id, "+FLAGS", "\\Seen")

        # Push to dashboard
        if self.on_email:
            self.on_email(mail_dict)

        tier_info = f"Tier {tier_label}"
        print(f"[imap]   → {sub_type} ({confidence_pct}%) via {tier_info} → {queue_name}")

    # ── Thread control ─────────────────────────────────────────────────

    def _run(self) -> None:
        """Main loop for the background thread."""
        backoff = 5
        while not self._stop.is_set():
            try:
                self._poll_once()
                backoff = self.poll_interval  # Reset backoff on success
            except Exception as exc:
                print(f"[imap] Poll error: {exc}. Retrying in {backoff}s…")
                backoff = min(backoff * 2, 60)

            self._stop.wait(backoff)

        # Cleanup
        if self._conn:
            try:
                self._conn.logout()
            except Exception:
                pass
        print("[imap] Watcher stopped.")

    def start(self) -> None:
        """Start the watcher in a background daemon thread."""
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="imap-watcher")
        self._thread.start()

    def stop(self) -> None:
        """Signal the watcher to stop."""
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=10)


def load_credentials(env_path: str = "config/mailbox.env") -> dict[str, str]:
    """Load IMAP credentials from a .env file."""
    creds = {}
    path = Path(env_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Mailbox config not found at {env_path}. "
            f"Create it with TESSERA_IMAP_HOST, TESSERA_IMAP_EMAIL, "
            f"TESSERA_IMAP_PASSWORD, etc."
        )
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, _, value = line.partition("=")
        creds[key.strip()] = value.strip()
    return creds
