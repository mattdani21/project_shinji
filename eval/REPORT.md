# Tessera AI Indexer — Eval Report

**What this is.** A measurement report for the Tessera indexing agent: routing
accuracy, auto-route behavior, calibration, adversarial robustness, and a
simulated pilot. The report is **eval-first**: every number below is produced by
a real command in this repository, and the exact command is listed next to the
number.

---

## ⚠️ Honesty box (read first)

- **Every measurement is on synthetic or simulated data.** No real-world
  accuracy is claimed anywhere in this report.
- Corpus: **10,000 generated emails/PDFs** (`generator/scale_corpus.py`).
- Simulated pilot: **600 emails** through the real ingest → route → HITL loop
  (`pilot/simulate.py` + `pilot/metrics.py`).
- A real-document pilot (M3) is the outstanding milestone; the machinery to run
  and report it is in `pilot/runbook.md`. Until that runs, treat all numbers as
  **machine-vs-synthetic-ground-truth**, not production performance.
- These are NOT claims about how the agent will behave on real insurance mail.

---

## 1. Headline metrics

| Metric | Value | Source |
|---|---|---|
| Attachment-aware full-pipeline routing accuracy | **100%** (10,000/10,000) | synthetic-corpus |
| Auto-route rate (no human review needed) | **97%** (97.3%) | synthetic-corpus |
| Auto-route accuracy (among auto-routed) | **100%** | synthetic-corpus |
| Body-text routing accuracy (email only, Tier 3+4) | **86.6%** | synthetic-corpus |
| — vs pre-Tier-3 baseline (Tier 4 only, no model) | **0.0%** | synthetic-corpus |
| Calibration (ECE) | **0.01** | synthetic-corpus |
| Adversarial suite (edge cases) | **100/100** (was 86/100 before the unreadable-attachment fix) | synthetic-corpus |
| Simulated pilot — routing accuracy | **100%** (600/600) | simulated-pilot |
| Simulated pilot — HITL rate | **5.7%** (34/600 to human review) | simulated-pilot |
| Simulated pilot — avg latency | **153 ms / email** (fresh re-run: 160 ms — machine-dependent) | simulated-pilot |
| Simulated pilot — data sovereignty | **OK — all route methods local** | simulated-pilot |
| Simulated pilot — threshold sweep 0.70–0.80 | **97.7% auto-route at 100% auto-route accuracy** | simulated-pilot |
| Tier distribution (attachment-aware run) | QR 8,686 · template 1,314 · **0 errors** (the earlier single QR-scan flake is fixed) | synthetic-corpus |

Source labels: `synthetic-corpus` = generated emails/PDFs scored against
generator ground truth · `simulated-pilot` = simulated inbound stream through
the real pipeline · `real` = real business mail (none yet — M3).

---

## 2. Methodology

**Corpus.** `generator/scale_corpus.py` generates 10k emails across six
business classes (repurchase, maintenance_client, maintenance_contrib,
new_business, claim_death, claim_retirement) plus broker bulk instructions,
with diversity sampling: clean, legacy (no QR), Afrikaans/English mixed,
cover-letter-prepended, broker-bulk. Forms are real PDFs (reportlab) with
embedded QR codes.

**Pipeline (the product path).** `indexer/rules/engine.py` cascades four tiers
per inbound email:

1. **Tier 1 — QR** (deterministic metadata extraction from PDF attachments)
2. **Tier 2 — OCR/template matching** (legacy forms without QR; completeness
   semantics: unsigned → review + RFI)
3. **Tier 3 — NER & taxonomy** (policy/ID/name/amount extraction + weighted
   keyword classification incl. Afrikaans)
4. **Tier 4 — deep-learning fallback** (XLM-RoBERTa ONNX, fully local; TF-IDF
   fallback when the model file is absent — no model binary is installed in
   this eval, so Tier 4 reports `unknown` for declined items)

**Eval harness modes** (`eval/runner.py`):
- `local_tier4_only` — pre-Tier-3 baseline (body text, straight to ML fallback)
- `local_pipeline` — full pipeline, body text only (Tiers 1/3/4)
- `local_pipeline_full` — full pipeline, **attachment-aware** (all 4 tiers)

**HITL band.** `hitl_threshold` (default 0.85) splits outcomes:
- confidence ≥ threshold → **auto-route**
- threshold > confidence ≥ 0.7 → **review** (with RFI reason)
- confidence < 0.7 → **escalate**
A threshold sweep (0.70–0.95) is part of the pilot report.

**Model versions.** Tier 4 is the ONNX export of a fine-tuned XLM-RoBERTa
(`models/tessera-encoder-v1/`); binaries are gitignored, so this eval exercises
Tiers 1–3 + the TF-IDF fallback path. Deterministic tiers (1–3) need no model.

---

## 3. Reproduce

Run from a fresh clone (Python ≥ 3.9):

```bash
git clone https://github.com/mattdani21/project_shinji
cd project_shinji
pip install -e ".[dev]"

# 1) Test suite
python -m pytest tests/ -q
#   → 50 passed, 0 skipped (verified 2026-08-13, py3.11)

# 2) Eval comparison (attachment-aware + body-text + baseline)
#    First generate the 10k corpus if it isn't present:
PYTHONPATH=. python generator/scale_corpus.py
#    Then run the comparison against the generated manifest:
PYTHONPATH=. python eval/run_comparison.py data/corpus_10k/manifest_10k.parquet
#    → writes data/runs/{local_tier4_only,local_pipeline,local_pipeline_full}_results.json

# 3) Simulated pilot (600 emails = 500 corpus sample + 100 adversarial)
PYTHONPATH=. python pilot/simulate.py \
  --manifest data/corpus_10k/manifest_10k.parquet \
  --num-emails 500 --wave-size 20 --wave-delay 2
PYTHONPATH=. python pilot/metrics.py pilot/reports/pilot_sim_results.csv
#    → writes pilot/reports/pilot_report.md

# 4) Adversarial suite
PYTHONPATH=. python generator/adversarial_test.py eval
```

Interactive HTML comparison of the same runs:
`eval/reports/comparisons/comparison.html`.

---

## 4. Known gaps (read this too)

- **No human baseline (T2).** All accuracy is vs synthetic generator ground
  truth. A human-baseline study on the same corpus is the missing comparison —
  it decides whether "100%" means anything vs a competent analyst.
- **No real documents (M3).** Real-mail pilot pending business access; numbers
  will be re-issued from real data when it runs.
- **Long-tail per-box numbers** (per form-type accuracy, per-RFI-reason
  breakdown) exist in the harness outputs but are not yet surfaced in this
  report.
- **Drift monitoring** is not yet in the product.
- Tier 4 deep-learning path is **not exercised** here (no model binary in git);
  Tier 4 numbers are the TF-IDF/fallback behavior.

---

*Report generated from `eval/run_comparison.py`, `pilot/simulate.py`,
`pilot/metrics.py`, `generator/adversarial_test.py`, and
`python -m pytest tests/ -q` — all executed from a fresh clone, 2026-08-13.*
