# M1.2 — Add CI that runs the existing suite on every PR

## What

`.github/workflows/ci.yml` — GitHub Actions CI that:

- runs on **every PR** and on pushes to `main`
- installs the package editable with `[dev]` extras (`pip install -e ".[dev]"`)
- runs the existing suite: `python -m pytest tests/ -q`
- runs across a **Python 3.9 / 3.11 / 3.12 matrix** (the wheel claims `requires-python >=3.9`, so CI now proves it)
- adds a `python -m build --wheel` step so packaging regressions are caught on every PR
- `permissions: contents: read` (least privilege), 20-min timeout, `fail-fast: false`

## Why

M1's definition of done: *a fresh machine stands up a working install from the packaged artifact using only docs + one command, with CI green.* PR #3 delivered the artifact; this PR delivers the "CI green" half — the two test files were previously never run automatically.

## How tested

- The exact CI install command (`pip install -e ".[dev]"`) was run locally in a fresh venv, then `python -m pytest tests/ -q` → **9 passed, 1 skipped** (same baseline; scenario D skips without `models/tier4_model.joblib`, which is gitignored — noted in the workflow).
- Python 3.9 compatibility scan: no 3.10+ syntax (match statements, PEP 604 unions, builtin generics) in `indexer/`, `tests/`, or `generator/`.
- The workflow itself will be exercised by this PR (CI runs on PRs).

## Notes

- The tier-4 model binary is gitignored, so `test_scenario_d_legacy_form` skips in CI just as it does locally; a future task can add a tiny fixture model or download step if full coverage is required.
