# M1.3 — Config-driven installs (taxonomy, models, queue dirs, HITL threshold)

## What

All install-specific knobs now live in one YAML config instead of code:

- **`indexer/config.py`** — `IndexerConfig` dataclass + `load_config()`:
  - keys: `taxonomy_path`, `schema_dir`, `onnx_model_dir`, `tfidf_model_path`, `queue_dir`, `review_dir`, `inbox_dir`, `hitl_threshold`
  - resolution order: `--config PATH` → `$TESSERA_INDEXER_CONFIG` → `./tessera_indexer.yaml` (cwd) → built-in defaults (package-bundled taxonomy, cwd-relative data dirs)
  - **relative paths in a user config resolve against the config file's directory** — a self-contained on-prem deploy dir (config + models/ + data/) works from any working directory
  - unknown keys rejected with a clear error; missing explicit file raises `FileNotFoundError`
  - `coerce_config()` lets every component accept a path string or an `IndexerConfig`
- **Wiring** — `RuleEngine`, `Tier4Classifier`, `WorkQueueManager` (queue dir + **HITL threshold now read from config instead of hardcoded 0.85**), `HITLExporter`, `batch_ingest`, `mailbox_watcher` (inbox dir). Explicit constructor args still win over config; config wins over defaults — no breaking changes to existing callers.
- **CLI** — new `tessera-indexer config` subcommand (prints effective config + source); `--config` flag on `check` / `classify` / `ingest-batch`.
- **`indexer/config/example.yaml`** — annotated example, shipped in the wheel (package data).
- **Docs** — README gained a Configuration section (key table + resolution order + usage); GOAL.md M1 item 3 checked off; STATE.md updated.
- **Tests** — `tests/test_config.py`, 10 tests: defaults→package taxonomy, YAML overrides with relative-path resolution, env-var config, cwd config discovery, unknown-key rejection, missing-file error, coerce behavior, threshold wiring in `WorkQueueManager` (0.88 confidence → review at 0.9 threshold, pending at 0.85), engine accepting a config *path*, explicit-args-override precedence.

## Why

M1 item 3: *make installs config-driven … rather than code.* This is what makes a single on-prem artifact deployable per-customer without touching source: the install checklist (M1 item 4) will point at `tessera_indexer.yaml` for all site-specific values, and the HITL threshold becomes a business tuning knob instead of a code constant.

## How tested

- Source tree: `python -m pytest tests/ -q` → **19 passed, 1 skipped** (was 9+1; +10 new config tests, no regressions)
- Rebuilt wheel, reinstalled into the fresh venv, re-ran the suite from a scratch dir against the installed package → **19 passed, 1 skipped**
- CLI: `tessera-indexer config` in a dir with `tessera_indexer.yaml` → auto-discovered, `queue_dir` resolved relative to the config dir, `hitl_threshold: 0.9` applied; explicit `--config` works; `example.yaml` confirmed present in the installed wheel
- Container rebuild (in progress at PR time): image includes the config layer; `tessera-indexer config` available inside the container

## Notes

- `process_pipeline`'s `threshold` parameter (hitl/exporter.py) was left as-is — it already takes an explicit argument; the hardcoded constant it duplicated (0.85 in `WorkQueueManager.route`) is now config-driven, which was the actual code-level knob.
- Diff is ~450 lines (config module + wiring + tests + docs). The `config/` package dir + `config.py` module are new; existing constructor signatures remain backward-compatible.
