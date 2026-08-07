# State

## Current state

Core pipeline works: Tier 1 (QR routing) + Tier 4 (XLM-RoBERTa ONNX, local inference) implemented, HITL exporter (`indexer/hitl/exporter.py`), work queues (`indexer/workqueue.py`), synthetic corpus generator (10k-scale, `generator/scale_corpus.py`), eval harness (`eval/`), and taxonomy (now bundled in-package at `indexer/taxonomy/`). The 30-day plan in `tessera_indexer_roadmap_v2.md` (phases 0–6) exists and was largely executed. Two test files exist.

Packaged as an installable wheel (`tessera-indexer`, pyproject.toml, pinned compatible-release deps, extras: `onnx` / `gen` / `dev`) with a `tessera-indexer` CLI (`check` / `classify` / `ingest-batch`) and a `Dockerfile` for on-prem containers. Verified 2026-08-06: wheel built, installed into a fresh venv, full suite passes against the installed package from a scratch dir (9 passed, 1 skipped), CLI smoke-tested, container image builds.

CI added (`.github/workflows/ci.yml`): runs the full suite on every PR/push to main across Python 3.9 / 3.11 / 3.12 (editable `[dev]` install), plus a wheel-build check.

Installs are config-driven (`indexer/config.py`): one YAML file controls taxonomy/schema paths, ONNX + TF-IDF model paths, queue/review/inbox dirs, and the HITL confidence threshold. Resolution: `--config` → `$TESSERA_INDEXER_CONFIG` → `./tessera_indexer.yaml` → built-in defaults; relative paths resolve against the config file's directory. CLI gained `config` (print effective config) and `--config` on all subcommands; annotated example ships in the wheel (`indexer/config/example.yaml`).

M1 (productize) complete: wheel + container + CI + config + on-prem install checklist (`docs/on_prem_install.md`, incl. firewall/egress verification for the data-sovereignty guarantee — verified: the routing pipeline makes zero network calls; the only HTTP client is the unreferenced benchmark baseline).

M2 in progress. Tier 2 (template matching) implemented (`indexer/tiers/tier2.py`): form-ref/title/section/field signal registry, deterministic explainable confidence, completeness semantics (unsigned → review + RFI note), label-aware field extraction (policy/ID/name/amount), optional pytesseract OCR hook for scanned PDFs. Wired into `RuleEngine.process_inbound` between QR and page-split fallback; legacy-form scenario D now routes via tier2 with no model required (33 passed, 0 skipped).

Tier 3 (NER & taxonomy) implemented (`indexer/tiers/tier3.py`): entity extraction (policy/ID/name/amount/date) + weighted keyword classification with Afrikaans coverage, wired into `classify_email` before Tier 4; extracted fields flow into routed tasks (47 passed, 0 skipped).

M2 eval evidence (2026-08-06, 10k corpus `data/corpus_10k/`): body-text accuracy 0.0% (tier4-only baseline, no model installed) → **86.6%** with tier3; auto-route 72.4% at 100% auto-route accuracy. Attachment-aware full pipeline: **100% accuracy**, 97% auto-route, ECE 0.01; tier distribution 8,685 QR / 1,314 tier2 (incl. ~315 QR-scan near-misses caught by tier2) / 1 error. Adversarial suite: **100/100** (was 86/100 before unreadable-attachment handling). Unreadable/blank attachments are no longer dropped silently — body-text fallback + review with RFI (`tier2_unreadable`). Eval harness gained `local_tier4_only` / `local_pipeline` / `local_pipeline_full` modes + `eval/run_comparison.py`; messy generator gained `legacy_form` + `keyword_body` stress modes; adversarial eval records route methods.

M3 pilot machinery delivered (`pilot/`): `simulate.py` (timed inbound stream through the real ingest→route→HITL loop), `metrics.py` (accuracy / HITL rate / latency / queue distribution / RFI threshold sweep / sovereignty check), `runbook.md` (how to run a real pilot on business mail). **Simulated pilot (600 emails, 2026-08-06): 100% accuracy, 5.7% HITL rate, 153 ms avg latency, sovereignty OK; threshold sweep: 0.70–0.80 gives 97.7% auto-route at 100% auto-route accuracy (better operating point than default 0.85 → 94.3%).** Real-data pilot pending owner access to business mail.

## Broken / incomplete

- Real-data pilot (M3 item 1) — needs business-mail access; runbook + machinery ready
- No recorded pilot on real inbound documents; demo runs on the synthetic corpus (`main_demo.py` needs `data/corpus_10k/manifest_10k.parquet` — present locally, gitignored)

## Blockers

- None technical blocking. Productization (packaging, CI) and Tier 2/3 completion are the gap between a working demo and a sellable install.

## Test command

`python3 -m pytest tests/ -q` (from repo root; CI runs it on every PR)

> Verified 2026-08-06 (autopilot M2): **48 passed, 0 skipped**. Scenario D
> (legacy form) no longer skips — Tier 2 routes it without any ML model.
> `models/tier4_model.joblib` is only needed to exercise the TF-IDF path.

## Run command

`python3 main_demo.py` (README; requires the generated corpus — run `PYTHONPATH=. python3 generator/scale_corpus.py` first if missing)
