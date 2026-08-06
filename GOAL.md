# Goal

Sell large-scale email-indexing installs to large investors (Tessera AI Indexer as the product)

## Roadmap

### M1 — Productize for installs (packaging + deployment)

- [x] Package the indexer as an installable artifact (wheel/container) with pinned dependencies — README install is currently a bare 8-package `pip install` list
- [ ] Add CI (`.github/workflows`) that runs the existing suite (`tests/test_engine.py`, `tests/test_e2e_routing.py`) on every PR — no CI exists today
- [ ] Make installs config-driven: taxonomy path, model path, queue dirs, HITL confidence threshold in config rather than code
- [ ] Write the on-prem install checklist (the product's selling point is data sovereignty — no data leaves the local environment)
*Definition of done:* A fresh machine stands up a working install from the packaged artifact using only docs + one command, with CI green.

### M2 — Complete Tier 2 and Tier 3 (OCR + NER)

- [ ] Tier 2: OCR & template matching for standard forms without QR codes (stubbed in README; no tier2 module exists in `indexer/tiers/`)
- [ ] Tier 3: NER & taxonomy for keyword/policy/ID extraction from unstructured text (stubbed; feeds `taxonomy/taxonomy.yaml`)
- [ ] Extend the eval harness (`eval/`) and adversarial corpus (`generator/adversarial_test.py`, `generator/messy_generator.py`) to cover the new tiers
- [ ] Add tests for both tiers in `tests/`
*Definition of done:* All four tiers implemented; routing accuracy on the eval harness improves over the Tier-1+Tier-4-only pipeline with no regression on the QR or ONNX paths (calibration currently reports overall and auto-route accuracy via `training/calibrate.py`).

### M3 — Pilot installs

- [ ] Run a pilot against a real inbound-document queue in business operations: ingest → route → HITL review loop
- [ ] Measure and document routing accuracy, HITL rate, queue throughput, and RFI threshold behavior (`training/calibrate.py`)
- [ ] Fix pilot findings back into `indexer/`
*Definition of done:* At least one pilot processes real inbound documents with a documented accuracy/HITL/throughput report, with inference staying fully local.

### M4 — Sales materials

- [ ] One-page product brief: multi-tier routing (QR → OCR → NER → XLM-RoBERTa ONNX), 100% data sovereignty, HITL review, on-prem installs
- [ ] Demo script + calibrated metrics from the pilot (`eval/reports/`)
- [ ] Packaging/pricing options for installs (per-queue, per-install)
*Definition of done:* A sales-ready package (brief, demo, metrics) that an investor conversation can close from.
