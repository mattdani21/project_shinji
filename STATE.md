# State

## Current state

Dormant. Core pipeline works: Tier 1 (QR routing) + Tier 4 (XLM-RoBERTa ONNX, local inference) implemented, HITL exporter (`indexer/hitl/exporter.py`), work queues (`indexer/workqueue.py`), synthetic corpus generator (10k-scale, `generator/scale_corpus.py`), eval harness (`eval/`), and taxonomy. The 30-day plan in `tessera_indexer_roadmap_v2.md` (phases 0–6) exists and was largely executed. Two test files exist.

## Broken / incomplete

- Tier 2 (OCR & template matching) and Tier 3 (NER & taxonomy) are stubbed: README marks them "Stubbed" and `indexer/tiers/` contains only `tier1_qr.py`, `tier4.py`, `baselines.py`, `train.py`
- No CI: `.github/workflows` does not exist, so the two test files are never run automatically
- No packaging/deployment story (README install = bare pip list; ONNX binaries in `models/` are gitignored, so an install must rebuild or re-add them)
- No recorded pilot on real inbound documents; demo runs on the synthetic corpus (`main_demo.py` needs `data/corpus_10k/manifest_10k.parquet`)

## Blockers

- None technical blocking. Productization (packaging, CI) and Tier 2/3 completion are the gap between a working demo and a sellable install.

## Test command

`python3 -m pytest tests/ -q` (from repo root; no CI runs it today)

## Run command

`python3 main_demo.py` (README; requires the generated corpus — run `PYTHONPATH=. python3 generator/scale_corpus.py` first if missing)
