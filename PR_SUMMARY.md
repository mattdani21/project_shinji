# M1.1 — Package the indexer as an installable artifact (wheel + container)

## What

Replaced the bare 8-package `pip install` story with a proper packaging + deployment story:

- **`pyproject.toml`** — `tessera-indexer` wheel via setuptools, with **pinned compatible-release dependencies** (`~=`): pydantic, PyYAML, pypdf, PyMuPDF, opencv-python-headless, numpy, pandas, pyarrow, scikit-learn, joblib, requests. Optional extras:
  - `[onnx]` — deep-learning Tier 4 (onnxruntime + transformers; no torch needed for inference)
  - `[gen]` — synthetic corpus generation (reportlab + qrcode)
  - `[dev]` — pytest + build tooling + gen deps (what CI will install)
- **`indexer/__init__.py` + subpackage `__init__.py` files** (rules, tiers, hitl, generator) — the code previously relied on implicit namespace packages; a wheel needs explicit packages.
- **Taxonomy bundled as package data** — `taxonomy/` moved into the package (`indexer/taxonomy/`). `RuleEngine` defaults now resolve taxonomy relative to the package (`Path(__file__).parent.parent / "taxonomy"`), so an installed wheel works from any working directory; explicit `taxonomy_path`/`schema_dir` overrides still supported (hooks for the upcoming config-driven task).
- **`tessera-indexer` CLI** (`indexer/cli.py`) — console entry point with:
  - `check` — install smoke test (taxonomy schemas, Tier 1 QR, Tier 4 backend status)
  - `classify --file/--text` — route a single email body, print routing JSON
  - `ingest-batch <dir>` — batch-mode ingestion
- **`Dockerfile` + `.dockerignore`** — multi-stage build (wheel built in builder stage, slim runtime), `tessera-indexer` as ENTRYPOINT, `models/` mountable at runtime for the ONNX binaries (gitignored, so images build from a clean checkout).
- **README** — install sections rewritten (wheel / container / from-source), CLI usage added, project structure updated.
- **Tests** — `test_engine.py` fixture now uses engine defaults, exercising the package-data taxonomy resolution instead of repo-relative paths.
- GOAL.md M1 item 1 checked off; STATE.md updated.

## Why

M1's definition of done: *a fresh machine stands up a working install from the packaged artifact using only docs + one command.* This PR delivers the artifact half (wheel + container + docs); the CI half is the next M1 item.

## How tested

- `uv build --wheel` → `dist/tessera_indexer-0.1.0-py3-none-any.whl` (verified taxonomy + CLI bundled inside the wheel)
- Fresh venv install of the wheel with `[dev]`:
  - `pytest tests/ -q` **from a scratch dir (no repo on path)** → **9 passed, 1 skipped** (scenario D skips without `models/tier4_model.joblib`, as before)
  - `tessera-indexer check` → 6 schemas loaded from package data, tier1 ok, tier4 gracefully reports `none` without model files
  - `tessera-indexer classify --file data/test_broker/test_1N_body.txt` → routing JSON output
- Source-tree regression: `python -m pytest tests/ -q` from repo root → **9 passed, 1 skipped** (unchanged baseline)
- `docker build -t tessera-indexer:0.1.0 .` → image builds; `docker run --rm tessera-indexer:0.1.0 check` → clean install check; default `--help` renders the CLI

## Notes

- Pins are compatible-release (`~=`, e.g. `pandas~=2.2`): reproducible within a minor version, patch releases flow in. Exact `==` pins can be applied later if a customer needs byte-level reproducibility.
- `torch` stays out of the wheel entirely — training is Colab/GPU-only per `docs/colab_handguide.md`; inference needs only onnxruntime + transformers.
- Diff is ~500 lines of new config/docs + small code changes; the taxonomy `git mv` is the bulk of the churn.
