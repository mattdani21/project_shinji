# Goal

Sell large-scale email-indexing installs to large investors (Tessera AI Indexer as the product)

## Roadmap

### M1 — Productize for installs (packaging + deployment)

- [x] Package the indexer as an installable artifact (wheel/container) with pinned dependencies — README install is currently a bare 8-package `pip install` list
- [x] Add CI (`.github/workflows`) that runs the existing suite (`tests/test_engine.py`, `tests/test_e2e_routing.py`) on every PR — no CI exists today
- [x] Make installs config-driven: taxonomy path, model path, queue dirs, HITL confidence threshold in config rather than code
- [x] Write the on-prem install checklist (the product's selling point is data sovereignty — no data leaves the local environment)
*Definition of done:* A fresh machine stands up a working install from the packaged artifact using only docs + one command, with CI green.

### M2 — Complete Tier 2 and Tier 3 (OCR + NER)

- [x] Tier 2: OCR & template matching for standard forms without QR codes (stubbed in README; no tier2 module exists in `indexer/tiers/`)
- [x] Tier 3: NER & taxonomy for keyword/policy/ID extraction from unstructured text (stubbed; feeds `taxonomy/taxonomy.yaml`)
- [x] Extend the eval harness (`eval/`) and adversarial corpus (`generator/adversarial_test.py`, `generator/messy_generator.py`) to cover the new tiers
- [x] Add tests for both tiers in `tests/`
*Definition of done:* All four tiers implemented; routing accuracy on the eval harness improves over the Tier-1+Tier-4-only pipeline with no regression on the QR or ONNX paths (calibration currently reports overall and auto-route accuracy via `training/calibrate.py`).

### M3 — Pilot installs

- [ ] Run a pilot against a real inbound-document queue in business operations: ingest → route → HITL review loop *(needs business mail access — owner handoff; simulated pilot machinery is ready: `pilot/`)*
- [x] Measure and document routing accuracy, HITL rate, queue throughput, and RFI threshold behavior (`training/calibrate.py`) — machinery + simulated pilot report delivered (`pilot/metrics.py`, `pilot/reports/pilot_report.md`); real-data numbers pending the pilot run
- [ ] Fix pilot findings back into `indexer/` *(two findings from the simulated pilot already fixed: flaky QR scan no longer errors the inbound; body-only route now reports its method)*
*Definition of done:* At least one pilot processes real inbound documents with a documented accuracy/HITL/throughput report, with inference staying fully local.

### M4 — Sales materials

- [x] One-page product brief: multi-tier routing (QR → OCR → NER → XLM-RoBERTa ONNX), 100% data sovereignty, HITL review, on-prem installs — `sales/one_pager.md`
- [x] Demo script + calibrated metrics from the pilot (`eval/reports/`) — `sales/demo_script.md` + `sales/metrics_snapshot.md` (all figures reproducible in-repo; real-pilot numbers pending M3)
- [x] Packaging/pricing options for installs (per-queue, per-install) — `sales/pricing.md` (draft options, owner to confirm)
*Definition of done:* A sales-ready package (brief, demo, metrics) that an investor conversation can close from. — met for synthetic-data metrics; real-mail metrics swap in when M3 pilot runs.
