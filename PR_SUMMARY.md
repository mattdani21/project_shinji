# M2.2 — Tier 3: NER & taxonomy for unstructured text

## What

`indexer/tiers/tier3.py` — `Tier3NERExtractor`:

- **Entity extraction** (`extract(text)`): policy number (label-aware + POL- patterns), SA ID number (13-digit), client name (email closing line), amounts (R …), dates (ISO). Label-aware so a 12-digit ID can't be mistaken for a policy number.
- **Keyword/taxonomy classification** (`classify(text)`): weighted keyword evidence per sub_type — strong phrases (weight 2, distinctive: "death claim", "premium adjustment", "onttrekking"…) and weak words (weight 1) — drawn from the taxonomy labels and the actual corpus language, with **Afrikaans coverage** (onttrekking, adres verander, premie verhoog, aftrede, sterfte, nuwe besigheid).
- **Explainable confidence**: `min(0.95, 0.40 + 0.12 * weighted_hits)`; returns `None` with zero evidence so Tier 4 takes over; `evidence` dict explains every hit.
- **Engine wiring**: `classify_email` runs Tier 3 between Tier 1 (QR) and Tier 4 (ONNX) — cheap deterministic routing before the ML fallback; extracted fields now flow into `WorkQueueItem.extracted_fields` for both body-only and chunk paths.

## Why

M2's second unchecked task. Body-only emails (the highest-frequency real case) previously went straight to the ML model — and to `unknown` when no model is installed. Tier 3 routes them deterministically from language evidence, no model required, with the taxonomy as the source of truth for what each form type "sounds like".

## How tested

- `tests/test_tier3.py` (14 tests): every sub_type's generated body classifies to its own type via tier3 (parametrized over all 6); unknown text → None; ambiguous text → low confidence; Afrikaans withdrawal body → repurchase; Afrikaans claim body → claim family; policy + client-name extraction verified; engine `classify_email` routes via tier3 (`local_ner_keyword`); end-to-end body-only `process_inbound` routes with extracted_fields attached; confidence calibration (strong vs weak evidence).
- Full suite: `python -m pytest tests/ -q` → **47 passed, 0 skipped** (was 33; +14 tier3, no regressions).
- Debugging notes: closing-name regex greediness (fixed with lazy `[,\s]*?`) and case sensitivity (fixed with `re.IGNORECASE`) — both were caught by the tests.

## Notes

- Tier 3 runs before Tier 4 in `classify_email`; the QR path (Tier 1) is untouched. When a trained ONNX model is present, Tier 4 still handles everything Tier 3 declines (evidence below threshold / no evidence).
- README architecture section updated: Tiers 2 and 3 no longer "Stubbed".
- Diff ~380 lines (module + tests + wiring + docs).
