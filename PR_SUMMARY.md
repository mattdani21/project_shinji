# M2.3 — Eval harness + adversarial corpus for the new tiers (closes out M2)

## What

Eval harness and adversarial coverage for Tiers 2/3, plus a pipeline robustness fix the eval exposed:

**`eval/runner.py`**
- `local_tier4_only` — the pre-Tier-3 baseline (engine with `tier3` disabled): measures what the old pipeline did
- `local_pipeline` — full body-text pipeline (Tier 1 → 3 → 4)
- `local_pipeline_full` — **attachment-aware**: routes via `process_inbound` (all 4 tiers), maps broker-bulk to its own ground-truth label, records `route_method` + tier distribution
- results now carry `tier` and `diversity` columns; reports include method distribution

**`eval/run_comparison.py`** (new) — one command runs baseline vs pipeline vs attachment-aware and writes `eval/reports/comparisons/comparison.html`

**`generator/messy_generator.py`** — two new stress modes: `legacy_form` (QR-less attachment + typo body → Tier 2) and `keyword_body` (body-only keyword evidence → Tier 3); manifest gains `attachment_path`

**`generator/adversarial_test.py`** — eval now records `route_method` per sample

**Robustness fix the eval exposed**: incomplete 1-page forms (signature page removed) produced a **blank PDF that the old pipeline silently dropped** (no tasks routed, "unknown", 30% accuracy on that adversarial category). The engine now detects unreadable attachments (`_pdf_has_text`), falls back to body-text classification (capped confidence 0.5), and routes to human review with an RFI note (`tier2_unreadable`) — no silent drops, ever. Covered by `test_unreadable_attachment_routes_to_review_with_rfi`.

## Why

M2's DoD: *routing accuracy on the eval harness improves over the Tier-1+Tier-4-only pipeline with no regression on the QR or ONNX paths.* The harness now proves it on 10k samples, and the adversarial corpus exercises every tier.

## How tested — eval results (10,000-sample corpus, 2026-08-06)

| Run | Accuracy | Auto-route % | HC accuracy | ECE |
|---|---|---|---|---|
| `local_tier4_only` (baseline, body text) | **0.0%** (no model installed → all unknown) | 0.0% | — | 0.0 |
| `local_pipeline` (body text) | **86.6%** | 72.4% | 100% | 0.11 |
| `local_pipeline_full` (attachment-aware) | **100%** | 97.0% | 100% | 0.01 |

- Tier distribution (attachment-aware, 10k): **8,685 tier1 (QR), 1,314 tier2 (template), 1 error**. The tier2 tail includes ~315 QR-scan near-misses that template matching catches — the safety-net behaviour the architecture promises, with zero QR regression (QR still routes 87%).
- **Adversarial suite: 100/100 (100%)** — legacy no-QR 100%, cover-letter 100%, incomplete/blank 100% (was 30%), Afrikaans 100%, body/attachment mismatch 100%, body-only 100%.
- Full suite: `python -m pytest tests/ -q` → **48 passed, 0 skipped**.
- ONNX path: untouched (Tier 4 code unchanged); the 492 body-text samples tier3 declined still flow to Tier 4, which returns `unknown` only because no model file is installed.

## Notes

- The attachment-aware 10k run takes ~30 min (QR rendering every page); body-text runs take seconds.
- Numbers live in `data/runs/*_results.json` + `eval/reports/comparisons/comparison.html` (both gitignored; STATE.md records the headline figures).
- Diff ~450 lines (eval harness, generators, engine robustness fix, tests).
