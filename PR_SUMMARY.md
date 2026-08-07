# M4 — Sales-ready package (brief, demo, metrics, pricing)

## What

The investor-conversation package, all grounded in the repo's verified numbers:

- **`sales/one_pager.md`** — one-page product brief: the problem (manual triage at scale), the four-tier routing solution (QR → template/OCR → NER → XLM-RoBERTa ONNX), the 100% data-sovereignty guarantee (zero network calls, verified; firewall/egress sign-off), HITL safety net with RFI reasons, calibrated proof table, and the offer (on-prem installs + measured pilot path).
- **`sales/demo_script.md`** — a 10-minute scripted demo, every command the real product: install check → QR auto-route → legacy no-QR (tier 2) → messy body-only (tier 3) → HITL review queue → live sovereignty proof (`lsof` during ingest) → the numbers. Expected outputs included, plus a close ("we run the pilot on their mail, inside their infra").
- **`sales/metrics_snapshot.md`** — every claim with its source file and reproduce command: 99.99% attachment-aware accuracy (10k corpus, with the 1 flaky-QR failure disclosed + the fix), 97.3% auto-route at 100% HC accuracy, ECE 0.011, adversarial 100/100, simulated pilot 600 emails (100%, 5.7% HITL, 153 ms), RFI threshold sweep (0.70–0.80 recommended), sovereignty audit, test health (50 passed).
- **`sales/pricing.md`** — three packaging models (per-install license, per-queue subscription, volume-tiered) with USD anchors, a recommended go-to-market stack (paid pilot → per-queue/per-install), discount levers, and what would change the numbers. **Stakes flagged**: pricing is a draft for owner confirmation, not a commitment.
- **`sales/README.md`** — index + the one-line story.

## Why

M4's DoD: a sales-ready package an investor conversation can close from. The brief/demo/metrics exist and are reproducible; pricing options are drafted per the roadmap item. Honest caveat carried throughout: metrics are synthetic-corpus + simulated-pilot until the M3 real-mail pilot runs.

## How tested

- Every figure re-read from its artifact immediately before writing: `data/runs/local_pipeline_full_results.json` (0.9999 acc, 0.9727 auto-route, 1.0 HC acc, ECE 0.0108, dist {0:1, 1:8685, 2:1314}), `data/runs/local_pipeline_results.json` (0.866), `data/adversarial_test/adversarial_results.csv` (1.0 all categories), `pilot/reports/pilot_sim_results.csv` (600/600, 5.7%, 153.4 ms), threshold sweep from `pilot/metrics.py`.
- The 1/10,000 failure is disclosed in the snapshot and tied to the already-merged fix (QR flake falls through to tier 2; 25/25 re-run clean).
- Demo commands are the actual CLI/scripts (checked against the installed wheel + source checkout).
- Suite: 50 passed, 0 skipped (unchanged — docs-only PR).

## Notes

- Diff is ~900 lines of sales docs; no code changes.
- Remaining before an investor-ready demo with real numbers: M3 real pilot (business mail) — the package is built so the metrics snapshot is the only page that changes.
