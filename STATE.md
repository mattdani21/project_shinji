# State

## Current state

Core pipeline works: Tier 1 (QR routing) + Tier 4 (XLM-RoBERTa ONNX, local inference) implemented, HITL exporter (`indexer/hitl/exporter.py`), work queues (`indexer/workqueue.py`), synthetic corpus generator (10k-scale, `generator/scale_corpus.py`), eval harness (`eval/`), and taxonomy (now bundled in-package at `indexer/taxonomy/`). The 30-day plan in `tessera_indexer_roadmap_v2.md` (phases 0–6) exists and was largely executed. Two test files exist.

Packaged as an installable wheel (`tessera-indexer`, pyproject.toml, pinned compatible-release deps, extras: `onnx` / `gen` / `dev`) with a `tessera-indexer` CLI (`check` / `classify` / `ingest-batch`) and a `Dockerfile` for on-prem containers. Verified 2026-08-06: wheel built, installed into a fresh venv, full suite passes against the installed package from a scratch dir (9 passed, 1 skipped), CLI smoke-tested, container image builds.

CI added (`.github/workflows/ci.yml`): runs the full suite on every PR/push to main across Python 3.9 / 3.11 / 3.12 (editable `[dev]` install), plus a wheel-build check.

Installs are config-driven (`indexer/config.py`): one YAML file controls taxonomy/schema paths, ONNX + TF-IDF model paths, queue/review/inbox dirs, and the HITL confidence threshold. Resolution: `--config` → `$TESSERA_INDEXER_CONFIG` → `./tessera_indexer.yaml` → built-in defaults; relative paths resolve against the config file's directory. CLI gained `config` (print effective config) and `--config` on all subcommands; annotated example ships in the wheel (`indexer/config/example.yaml`).

M1 (productize) complete: wheel + container + CI + config + on-prem install checklist (`docs/on_prem_install.md`, incl. firewall/egress verification for the data-sovereignty guarantee — verified: the routing pipeline makes zero network calls; the only HTTP client is the unreferenced benchmark baseline).

## Broken / incomplete

- Tier 2 (OCR & template matching) and Tier 3 (NER & taxonomy) are stubbed: README marks them "Stubbed" and `indexer/tiers/` contains only `tier1_qr.py`, `tier4.py`, `baselines.py`, `train.py`
- No recorded pilot on real inbound documents; demo runs on the synthetic corpus (`main_demo.py` needs `data/corpus_10k/manifest_10k.parquet`)

## Blockers

- None technical blocking. Productization (packaging, CI) and Tier 2/3 completion are the gap between a working demo and a sellable install.

## Test command

`python3 -m pytest tests/ -q` (from repo root; no CI runs it today)

> Verified 2026-08-06 (orchestrator Step-4): 9 passed, 1 skipped. `test_scenario_d_legacy_form`
> skips when `models/tier4_model.joblib` is absent — train it via `indexer/tiers/train.py`.
> Two test-side fixes landed with this PR: `mailbox_watcher` honors a module-level `watch_dir`
> override, and scenario E scans all queue files (routed items may land in `unknown.jsonl`
> when the tier-4 model is missing).

## Run command

`python3 main_demo.py` (README; requires the generated corpus — run `PYTHONPATH=. python3 generator/scale_corpus.py` first if missing)
