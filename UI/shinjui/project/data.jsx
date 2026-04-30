// Mock data for the Tessera demo dashboard.
const INBOX = [
  {
    id: "m-8842",
    from: "rachel.tan@northbridge-advisors.ca",
    fromName: "Rachel Tan",
    subject: "New TFSA application — Jane Smith",
    preview: "Dear Sir, please find attached the new business documentation for TFSA account opening...",
    body: `Dear Indexing Team,

Please find attached the new business documentation for our client Jane Smith. This is a TFSA repurchase request, all signatures have been verified at our end.

The package contains:
  • Account opening form (pages 1–3)
  • Source-of-funds declaration (page 4)
  • Beneficiary designation (page 5)

Kindly process at your earliest convenience.

Best regards,
Rachel Tan
Northbridge Advisors`,
    received: "09:42",
    attachments: [{ name: "AAA_CSP_TFSA_smith.pdf", pages: 5, size: "412 KB" }],
    routedTo: { queue: "NEW BUSINESS", item: "AAA CSP TFSA" },
    classification: {
      type: "repurchase", tier: "1 (QR)", confidence: 100, status: "pending",
      policy: "POL-12345678", client: "Jane Smith", pages: "1–5 (complete)",
    },
  },
  {
    id: "m-8843",
    from: "ops@meridian-wealth.com",
    fromName: "Meridian Ops",
    subject: "XYZ — additional beneficiary form",
    preview: "Attached please find the updated beneficiary designation for policy POL-44120031...",
    body: `Hello,

Attached is an updated beneficiary designation form for policy POL-44120031. Please apply to the existing file.

— Meridian Ops`,
    received: "09:17",
    attachments: [{ name: "XYZ_beneficiary.pdf", pages: 2, size: "188 KB" }],
    routedTo: { queue: "NEW BUSINESS", item: "XYZ" },
    classification: {
      type: "amendment", tier: "1 (QR)", confidence: 96, status: "pending",
      policy: "POL-44120031", client: "Marcus Lévesque", pages: "1–2 (complete)",
    },
  },
  {
    id: "m-8844",
    from: "kim.park@finchgrove.ca",
    fromName: "Kim Park",
    subject: "ZQY group plan — onboarding pkg",
    preview: "New plan onboarding for ZQY Holdings, full census attached, 31 members...",
    body: "New plan onboarding for ZQY Holdings, please ingest. Census of 31 members, contribution sheet included.",
    received: "08:58",
    attachments: [{ name: "ZQY_onboarding.pdf", pages: 14, size: "1.8 MB" }],
    routedTo: { queue: "NEW BUSINESS", item: "ZQY" },
    classification: {
      type: "group-onboarding", tier: "2", confidence: 88, status: "pending",
      policy: "POL-78812440", client: "ZQY Holdings", pages: "1–14 (complete)",
    },
  },
  {
    id: "m-8845",
    from: "claims@harborline.ca",
    fromName: "Harborline Claims",
    subject: "BBB CSP withdrawal — partial",
    preview: "Partial withdrawal request for BBB CSP, please process per attached instructions...",
    body: "Partial withdrawal request, please process per attached instructions. Client confirmed via phone 04/29.",
    received: "08:31",
    attachments: [{ name: "BBB_CSP_WD.pdf", pages: 3, size: "240 KB" }],
    routedTo: { queue: "MAINTENANCE", item: "BBB CSP WD" },
    classification: {
      type: "withdrawal", tier: "1 (QR)", confidence: 99, status: "pending",
      policy: "POL-23990041", client: "B. Banerjee", pages: "1–3 (complete)",
    },
  },
  {
    id: "m-8846",
    from: "noreply@docusign.net",
    fromName: "DocuSign",
    subject: "Completed: address change — DDD",
    preview: "Completed envelope — address change form for client DDD has been signed by all parties...",
    body: "Envelope completed. Address change for client DDD signed by all parties. Audit trail attached.",
    received: "08:14",
    attachments: [{ name: "DDD_addrchg.pdf", pages: 2, size: "164 KB" }],
    routedTo: { queue: "MAINTENANCE", item: "DDD address change" },
    classification: {
      type: "address-change", tier: "1 (QR)", confidence: 100, status: "pending",
      policy: "POL-50221809", client: "D. Dhaliwal", pages: "1–2 (complete)",
    },
  },
  {
    id: "m-8847",
    from: "sandra@everett-claims.ca",
    fromName: "Sandra Everett",
    subject: "EEE life claim — incomplete?",
    preview: "Submitting life claim for client EEE — death certificate attached, may be missing physician's...",
    body: `Hi team,

Submitting the life claim for client EEE. Death certificate is attached. I believe the physician's statement may still be outstanding — please flag if so.

Thanks,
Sandra`,
    received: "07:49",
    attachments: [{ name: "EEE_life_claim.pdf", pages: 4, size: "320 KB" }],
    routedTo: { queue: "CLAIMS", item: "EEE life claim", needsReview: true },
    classification: {
      type: "life-claim", tier: "3", confidence: 71, status: "needs-review",
      policy: "POL-66104412", client: "E. Edwards (estate)", pages: "1–4 (missing physician statement)",
      note: "Confidence below threshold • physician's statement page expected",
    },
  },
];

const QUEUE_GROUPS = [
  {
    name: "NEW BUSINESS",
    color: "var(--accent)",
    items: [
      { id: "q-nb-1", label: "AAA CSP TFSA", source: "m-8842", count: 1 },
      { id: "q-nb-2", label: "XYZ", source: "m-8843", count: 1 },
      { id: "q-nb-3", label: "ZQY", source: "m-8844", count: 1 },
    ],
  },
  {
    name: "MAINTENANCE",
    color: "var(--violet)",
    items: [
      { id: "q-mt-1", label: "BBB CSP WD", source: "m-8845", count: 1 },
      { id: "q-mt-2", label: "DDD address change", source: "m-8846", count: 1 },
    ],
  },
  {
    name: "CLAIMS",
    color: "var(--amber)",
    items: [
      { id: "q-cl-1", label: "EEE life claim", source: "m-8847", count: 1, note: true },
    ],
  },
];

window.TESSERA_DATA = { INBOX, QUEUE_GROUPS };
