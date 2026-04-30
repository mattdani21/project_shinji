"""Local dashboard server for Tessera AI Indexer.

The dashboard is intentionally dependency-free: it uses Python's standard HTTP
server and static assets so the demo remains easy to run on an offline machine.
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import threading
import webbrowser
from copy import deepcopy
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


ROOT_DIR = Path(__file__).resolve().parents[1]
DASHBOARD_DIR = ROOT_DIR / "dashboard"

DEMO_INBOX: list[dict[str, Any]] = [
    {
        "id": "m-8842",
        "from": "rachel.tan@northbridge-advisors.ca",
        "fromName": "Rachel Tan",
        "subject": "New TFSA application - Jane Smith",
        "preview": "Dear Sir, please find attached the new business documentation for TFSA account opening...",
        "body": (
            "Dear Indexing Team,\n\n"
            "Please find attached the new business documentation for our client Jane Smith. "
            "This is a TFSA repurchase request, all signatures have been verified at our end.\n\n"
            "The package contains:\n"
            "  - Account opening form (pages 1-3)\n"
            "  - Source-of-funds declaration (page 4)\n"
            "  - Beneficiary designation (page 5)\n\n"
            "Kindly process at your earliest convenience.\n\n"
            "Best regards,\nRachel Tan\nNorthbridge Advisors"
        ),
        "received": "09:42",
        "attachments": [{"name": "AAA_CSP_TFSA_smith.pdf", "pages": 5, "size": "412 KB"}],
        "routedTo": {"queue": "NEW BUSINESS", "item": "AAA CSP TFSA"},
        "classification": {
            "type": "repurchase",
            "tier": "1 (QR)",
            "confidence": 100,
            "status": "pending",
            "policy": "POL-12345678",
            "client": "Jane Smith",
            "pages": "1-5 (complete)",
        },
    },
    {
        "id": "m-8843",
        "from": "ops@meridian-wealth.com",
        "fromName": "Meridian Ops",
        "subject": "XYZ - additional beneficiary form",
        "preview": "Attached please find the updated beneficiary designation for policy POL-44120031...",
        "body": (
            "Hello,\n\n"
            "Attached is an updated beneficiary designation form for policy POL-44120031. "
            "Please apply to the existing file.\n\n"
            "- Meridian Ops"
        ),
        "received": "09:17",
        "attachments": [{"name": "XYZ_beneficiary.pdf", "pages": 2, "size": "188 KB"}],
        "routedTo": {"queue": "NEW BUSINESS", "item": "XYZ"},
        "classification": {
            "type": "amendment",
            "tier": "1 (QR)",
            "confidence": 96,
            "status": "pending",
            "policy": "POL-44120031",
            "client": "Marcus Levesque",
            "pages": "1-2 (complete)",
        },
    },
    {
        "id": "m-8844",
        "from": "kim.park@finchgrove.ca",
        "fromName": "Kim Park",
        "subject": "ZQY group plan - onboarding pkg",
        "preview": "New plan onboarding for ZQY Holdings, full census attached, 31 members...",
        "body": "New plan onboarding for ZQY Holdings, please ingest. Census of 31 members, contribution sheet included.",
        "received": "08:58",
        "attachments": [{"name": "ZQY_onboarding.pdf", "pages": 14, "size": "1.8 MB"}],
        "routedTo": {"queue": "NEW BUSINESS", "item": "ZQY"},
        "classification": {
            "type": "group-onboarding",
            "tier": "2",
            "confidence": 88,
            "status": "pending",
            "policy": "POL-78812440",
            "client": "ZQY Holdings",
            "pages": "1-14 (complete)",
        },
    },
    {
        "id": "m-8845",
        "from": "claims@harborline.ca",
        "fromName": "Harborline Claims",
        "subject": "BBB CSP withdrawal - partial",
        "preview": "Partial withdrawal request for BBB CSP, please process per attached instructions...",
        "body": "Partial withdrawal request, please process per attached instructions. Client confirmed via phone 04/29.",
        "received": "08:31",
        "attachments": [{"name": "BBB_CSP_WD.pdf", "pages": 3, "size": "240 KB"}],
        "routedTo": {"queue": "MAINTENANCE", "item": "BBB CSP WD"},
        "classification": {
            "type": "withdrawal",
            "tier": "1 (QR)",
            "confidence": 99,
            "status": "pending",
            "policy": "POL-23990041",
            "client": "B. Banerjee",
            "pages": "1-3 (complete)",
        },
    },
    {
        "id": "m-8846",
        "from": "noreply@docusign.net",
        "fromName": "DocuSign",
        "subject": "Completed: address change - DDD",
        "preview": "Completed envelope - address change form for client DDD has been signed by all parties...",
        "body": "Envelope completed. Address change for client DDD signed by all parties. Audit trail attached.",
        "received": "08:14",
        "attachments": [{"name": "DDD_addrchg.pdf", "pages": 2, "size": "164 KB"}],
        "routedTo": {"queue": "MAINTENANCE", "item": "DDD address change"},
        "classification": {
            "type": "address-change",
            "tier": "1 (QR)",
            "confidence": 100,
            "status": "pending",
            "policy": "POL-50221809",
            "client": "D. Dhaliwal",
            "pages": "1-2 (complete)",
        },
    },
    {
        "id": "m-8847",
        "from": "sandra@everett-claims.ca",
        "fromName": "Sandra Everett",
        "subject": "EEE life claim - incomplete?",
        "preview": "Submitting life claim for client EEE - death certificate attached, may be missing physician's...",
        "body": (
            "Hi team,\n\n"
            "Submitting the life claim for client EEE. Death certificate is attached. "
            "I believe the physician's statement may still be outstanding - please flag if so.\n\n"
            "Thanks,\nSandra"
        ),
        "received": "07:49",
        "attachments": [{"name": "EEE_life_claim.pdf", "pages": 4, "size": "320 KB"}],
        "routedTo": {"queue": "CLAIMS", "item": "EEE life claim", "needsReview": True},
        "classification": {
            "type": "life-claim",
            "tier": "3",
            "confidence": 71,
            "status": "needs-review",
            "policy": "POL-66104412",
            "client": "E. Edwards (estate)",
            "pages": "1-4 (missing physician statement)",
            "note": "Confidence below threshold; physician's statement page expected",
        },
    },
]

QUEUE_GROUPS: list[dict[str, Any]] = [
    {
        "name": "NEW BUSINESS",
        "color": "var(--accent)",
        "items": [
            {"id": "q-nb-1", "label": "AAA CSP TFSA", "source": "m-8842", "count": 1},
            {"id": "q-nb-2", "label": "XYZ", "source": "m-8843", "count": 1},
            {"id": "q-nb-3", "label": "ZQY", "source": "m-8844", "count": 1},
        ],
    },
    {
        "name": "MAINTENANCE",
        "color": "var(--violet)",
        "items": [
            {"id": "q-mt-1", "label": "BBB CSP WD", "source": "m-8845", "count": 1},
            {"id": "q-mt-2", "label": "DDD address change", "source": "m-8846", "count": 1},
        ],
    },
    {
        "name": "CLAIMS",
        "color": "var(--amber)",
        "items": [
            {"id": "q-cl-1", "label": "EEE life claim", "source": "m-8847", "count": 1, "note": True},
        ],
    },
]


class DashboardState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.reset()

    def reset(self) -> dict[str, Any]:
        with getattr(self, "_lock", threading.Lock()):
            self.queue_state = {
                "NEW BUSINESS": ["m-8842"],
                "MAINTENANCE": [],
                "CLAIMS": [],
            }
            self.processed = {"m-8842"}
            return self.snapshot()

    def snapshot(self) -> dict[str, Any]:
        return {
            "inbox": deepcopy(DEMO_INBOX),
            "queueGroups": deepcopy(QUEUE_GROUPS),
            "queueState": deepcopy(self.queue_state),
            "processed": sorted(self.processed),
            "sovereignty": self.sovereignty_stats(),
        }

    def process_all(self) -> dict[str, Any]:
        with self._lock:
            for mail in DEMO_INBOX:
                if mail["id"] in self.processed:
                    continue
                queue = mail["routedTo"]["queue"]
                self.queue_state.setdefault(queue, []).append(mail["id"])
                self.processed.add(mail["id"])
            return self.snapshot()

    def sovereignty_stats(self) -> dict[str, Any]:
        return {
            "mailsProcessedToday": 1247 + len(self.processed),
            "externalApiCallsToday": 0,
            "customerDataEgress": "0 bytes",
            "averageInferenceLatencyMs": 187,
        }


STATE = DashboardState()


class DashboardHandler(BaseHTTPRequestHandler):
    server_version = "TesseraDashboard/0.1"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            self._send_json(STATE.snapshot())
            return
        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/process-all":
            self._read_request_body()
            self._send_json(STATE.process_all())
            return
        if parsed.path == "/api/reset":
            self._read_request_body()
            self._send_json(STATE.reset())
            return
        self.send_error(HTTPStatus.NOT_FOUND, "Unknown API route")

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[dashboard] {self.address_string()} - {fmt % args}")

    def _read_request_body(self) -> bytes:
        length = int(self.headers.get("content-length", "0"))
        return self.rfile.read(length) if length else b""

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, request_path: str) -> None:
        relative = "index.html" if request_path in {"", "/"} else unquote(request_path.lstrip("/"))
        file_path = (DASHBOARD_DIR / relative).resolve()
        if not file_path.is_file() or DASHBOARD_DIR.resolve() not in file_path.parents:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return

        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        body = file_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)


def run(host: str = "127.0.0.1", port: int = 8765, open_browser: bool = False) -> None:
    server = ThreadingHTTPServer((host, port), DashboardHandler)
    url = f"http://{host}:{port}"
    print(f"Tessera dashboard running at {url}")
    print("Press Ctrl+C to stop.")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Tessera local dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    parser.add_argument("--open", action="store_true", help="Open the dashboard in a browser.")
    args = parser.parse_args()
    run(host=args.host, port=args.port, open_browser=args.open)


if __name__ == "__main__":
    main()
