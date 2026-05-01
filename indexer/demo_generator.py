"""Lightweight demo email generator for the Tessera dashboard.

Produces a configurable batch of synthetic emails with realistic metadata
that can be fed directly into the dashboard's inbox. Each email has a sender,
subject, body, mock attachment reference, and a pre-assigned routing target
(used by the dashboard to simulate the indexing pipeline without needing
the full RuleEngine for the UI demo).
"""
from __future__ import annotations

import random
import string
import uuid
from typing import Any


# ── Sender pool ──────────────────────────────────────────────────────────────
_SENDERS = [
    ("Priya Naidoo", "priya.naidoo@bluefern-advisors.co.za"),
    ("James van der Merwe", "jvdm@capitalbridge.co.za"),
    ("Lerato Moloi", "lerato@goldcrest-wealth.co.za"),
    ("Chen Wei", "chen.wei@pacificrim-financial.hk"),
    ("Fatima Al-Rashid", "fatima@crescentgroup.ae"),
    ("Marcus Lévesque", "marcus.l@northstar-advisors.ca"),
    ("Anika Patel", "anika@sunbirdcorp.co.za"),
    ("David Okonkwo", "d.okonkwo@lagospartners.ng"),
    ("Sophie Tremblay", "sophie.t@meridian-wealth.ca"),
    ("Ravi Krishnamurthy", "ravi.k@bangaloretrust.in"),
    ("Elena Vasquez", "elena.v@summitcapital.mx"),
    ("Thabo Sithole", "thabo@silvertree-fin.co.za"),
    ("Yuki Tanaka", "y.tanaka@sakuralife.jp"),
    ("Anele Dlamini", "anele.d@kwazulubrokerage.co.za"),
    ("Pierre Dubois", "p.dubois@geneve-assurance.ch"),
]

# ── Email templates per queue type ───────────────────────────────────────────
_TEMPLATES: dict[str, list[dict[str, Any]]] = {
    "NEW BUSINESS": [
        {
            "subject_tpl": "{product} application — {client}",
            "body_tpl": (
                "Dear Indexing Team,\n\n"
                "Please find attached the new business documentation for our client {client}. "
                "This is a {product} application, all signatures have been verified.\n\n"
                "The package contains:\n"
                "  - Account opening form (pages 1–3)\n"
                "  - Source-of-funds declaration (page 4)\n"
                "  - Beneficiary designation (page 5)\n\n"
                "Kindly process at your earliest convenience.\n\n"
                "Best regards,\n{sender}"
            ),
            "type": "repurchase",
            "tier": "1 (QR)",
            "pages": 5,
        },
        {
            "subject_tpl": "{product} group plan — onboarding",
            "body_tpl": (
                "New plan onboarding for {client}, please ingest. "
                "Census of {member_count} members, contribution sheet included."
            ),
            "type": "group-onboarding",
            "tier": "2",
            "pages": 14,
        },
        {
            "subject_tpl": "Beneficiary update — {client}",
            "body_tpl": (
                "Hello,\n\n"
                "Attached is an updated beneficiary designation form for policy {policy}. "
                "Please apply to the existing file.\n\n"
                "— {sender}"
            ),
            "type": "amendment",
            "tier": "1 (QR)",
            "pages": 2,
        },
    ],
    "MAINTENANCE": [
        {
            "subject_tpl": "{product} withdrawal — partial",
            "body_tpl": (
                "Partial withdrawal request, please process per attached instructions. "
                "Client {client} confirmed via phone."
            ),
            "type": "withdrawal",
            "tier": "1 (QR)",
            "pages": 3,
        },
        {
            "subject_tpl": "Address change — {client}",
            "body_tpl": (
                "Envelope completed. Address change for client {client} "
                "signed by all parties. Audit trail attached."
            ),
            "type": "address-change",
            "tier": "1 (QR)",
            "pages": 2,
        },
        {
            "subject_tpl": "Banking details update — {client}",
            "body_tpl": (
                "Hi team,\n\nPlease update the banking details for {client} as per "
                "the attached confirmation letter from {bank}.\n\nThanks,\n{sender}"
            ),
            "type": "banking-update",
            "tier": "4 (ML)",
            "pages": 1,
        },
    ],
    "CLAIMS": [
        {
            "subject_tpl": "Life claim — {client}",
            "body_tpl": (
                "Hi team,\n\n"
                "Submitting the life claim for client {client}. "
                "Death certificate is attached. I believe the physician's statement "
                "may still be outstanding — please flag if so.\n\n"
                "Thanks,\n{sender}"
            ),
            "type": "life-claim",
            "tier": "3",
            "pages": 4,
            "low_confidence": True,
        },
        {
            "subject_tpl": "Disability claim submission — {client}",
            "body_tpl": (
                "Please process the attached disability claim for {client}. "
                "Medical report from Dr. {doctor} is included.\n\n"
                "Policy: {policy}\n\n— {sender}"
            ),
            "type": "disability-claim",
            "tier": "4 (ML)",
            "pages": 6,
        },
    ],
}

_PRODUCTS = [
    "CSP TFSA", "RA Maxima", "Living Annuity", "Endowment Plus",
    "Group Risk", "Provident Fund", "Offshore Wrapper", "Education Plan",
]
_CLIENTS = [
    "J. Smith", "A. van Niekerk", "T. Ndlovu", "M. Patel",
    "S. Williams", "K. Mokoena", "R. Chetty", "B. Nkosi",
    "L. Botha", "D. Govender", "F. Mahlangu", "E. Pretorius",
    "P. Mthembu", "N. Jacobs", "C. Pillay",
]
_BANKS = ["FNB", "Standard Bank", "Nedbank", "Absa", "Capitec", "Investec"]
_DOCTORS = ["van Zyl", "Moyo", "Naidoo", "Roberts", "Khumalo", "Singh"]
_SIZES = ["124 KB", "188 KB", "240 KB", "312 KB", "412 KB", "520 KB", "780 KB", "1.2 MB", "1.8 MB"]


def _policy_number() -> str:
    return f"POL-{''.join(random.choices(string.digits, k=8))}"


def _time_str(index: int, total: int) -> str:
    """Generate a plausible inbox timestamp, newest first."""
    base_hour = 9
    base_min = 45
    offset = index * (60 // max(total, 1))
    h = base_hour - (offset // 60)
    m = base_min - (offset % 60)
    if m < 0:
        m += 60
        h -= 1
    return f"{max(h, 6):02d}:{max(m, 0):02d}"


def generate_batch(count: int = 10) -> dict[str, Any]:
    """Generate a batch of *count* synthetic demo emails.

    Returns a dict with ``inbox`` (list of mail objects) and ``queueGroups``
    (list of queue group definitions) ready to be merged into dashboard state.
    """
    # Distribute roughly evenly across queues, with a claims bias for drama
    queue_names = list(_TEMPLATES.keys())
    distribution = []
    for i in range(count):
        if i < count * 0.45:
            distribution.append("NEW BUSINESS")
        elif i < count * 0.75:
            distribution.append("MAINTENANCE")
        else:
            distribution.append("CLAIMS")
    random.shuffle(distribution)

    used_senders: set[str] = set()
    inbox: list[dict[str, Any]] = []
    queue_items: dict[str, list[dict[str, Any]]] = {q: [] for q in queue_names}

    for idx, queue_name in enumerate(distribution):
        templates = _TEMPLATES[queue_name]
        tpl = random.choice(templates)

        # Pick a unique sender
        available = [s for s in _SENDERS if s[0] not in used_senders]
        if not available:
            available = list(_SENDERS)
        sender_name, sender_email = random.choice(available)
        used_senders.add(sender_name)

        client = random.choice(_CLIENTS)
        product = random.choice(_PRODUCTS)
        policy = _policy_number()
        bank = random.choice(_BANKS)
        doctor = random.choice(_DOCTORS)
        member_count = random.randint(12, 85)

        fmt = {
            "sender": sender_name, "client": client, "product": product,
            "policy": policy, "bank": bank, "doctor": doctor,
            "member_count": str(member_count),
        }

        subject = tpl["subject_tpl"].format(**fmt)
        body = tpl["body_tpl"].format(**fmt)
        preview = body.replace("\n", " ")[:100] + "..."

        mail_id = f"m-{uuid.uuid4().hex[:6]}"
        att_name = f"{client.replace(' ', '_').replace('.', '')}_{tpl['type'].replace('-', '_')}.pdf"
        pages = tpl["pages"]
        size = random.choice(_SIZES)
        is_low = tpl.get("low_confidence", False)
        confidence = random.randint(58, 74) if is_low else random.randint(88, 100)
        status = "needs-review" if confidence < 78 else "pending"

        mail = {
            "id": mail_id,
            "from": sender_email,
            "fromName": sender_name,
            "subject": subject,
            "preview": preview,
            "body": body,
            "received": _time_str(idx, count),
            "attachments": [{"name": att_name, "pages": pages, "size": size}],
            "routedTo": {
                "queue": queue_name,
                "item": f"{client} {tpl['type']}",
                "needsReview": status == "needs-review",
            },
            "classification": {
                "type": tpl["type"],
                "tier": tpl["tier"],
                "confidence": confidence,
                "status": status,
                "policy": policy,
                "client": client,
                "pages": f"1–{pages} ({'missing physician statement' if is_low else 'complete'})",
                "note": "Confidence below threshold • physician's statement page expected" if is_low else "",
            },
        }
        inbox.append(mail)

        queue_items[queue_name].append({
            "id": f"q-{mail_id}",
            "label": f"{client} {tpl['type']}",
            "source": mail_id,
            "count": 1,
            "note": status == "needs-review",
        })

    queue_groups = [
        {"name": "NEW BUSINESS", "color": "var(--accent)", "items": queue_items["NEW BUSINESS"]},
        {"name": "MAINTENANCE", "color": "var(--violet)", "items": queue_items["MAINTENANCE"]},
        {"name": "CLAIMS", "color": "var(--amber)", "items": queue_items["CLAIMS"]},
    ]

    return {"inbox": inbox, "queueGroups": queue_groups}


if __name__ == "__main__":
    import json
    batch = generate_batch(10)
    print(json.dumps(batch, indent=2, default=str))
