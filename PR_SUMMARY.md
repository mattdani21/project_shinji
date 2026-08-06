# M2.1 — Tier 2: OCR & template matching for legacy (QR-less) forms

## What

`indexer/tiers/tier2.py` — `Tier2TemplateMatcher`, the first piece of M2:

- **Template registry** per sub_type (form-ref code, header title, section markers, field labels) derived from the actual form layouts (`generator/forms/generic.py`) and taxonomy schemas
- **Deterministic, explainable confidence**:
  - exact `Form Ref: MWS-<TYPE>` hit → 0.95 (the form declares its own type)
  - title match → 0.60 base + 0.05/section + 0.02/field (cap 0.90)
  - sections/fields only → 0.30 + 0.05/section + 0.02/field (cap 0.70)
  - no signals → `None` (falls through to later tiers)
- **Completeness semantics mirror Tier 1**: missing "Declaration and Signature" → `status: incomplete`, confidence capped at 0.8, RFI note set → item routed to human review
- **Label-aware field extraction** (policy number, SA ID, client name, amount) — reads values from their labeled lines so a 12-digit ID can't be mistaken for a policy number
- **Optional OCR hook**: scanned PDFs with no text layer are OCR'd via pytesseract when installed; otherwise reported as no-match (no new hard dependency)
- **Engine wiring**: `process_inbound` now tries Tier 2 between the QR branch and the page-split fallback; QR path untouched (no regression), Tier 4 path untouched

## Why

M2's first unchecked task. Legacy forms (no QR) are the highest-volume real-world edge case the existing pipeline handled worst — they fell all the way to the ML model (or `unknown` without one). Tier 2 routes them deterministically from their printed structure, with explainable confidence and HITL semantics.

## How tested

- `tests/test_tier2.py` (14 tests): every one of the 6 form types matches its template (form-ref hit → ≥0.9, complete); incomplete forms flagged review with capped confidence + RFI note; cover-letter-prepended forms still match (page_count correct); mixed Afrikaans/English still matches; field extraction verified against ground-truth params (policy/ID/name); no-match and weak-evidence cases return None / fall below threshold; title-only scoring; end-to-end engine routing via `tier2_template` with auto-route (0.95 ≥ 0.85).
- **`test_scenario_d_legacy_form` rewritten**: previously skipped without `models/tier4_model.joblib`; now asserts `method == "tier2_template"`, `sub_type == maintenance_client`, confidence 0.95 — **the legacy-form path no longer depends on the ML model at all**.
- Full suite: `python -m pytest tests/ -q` → **33 passed, 0 skipped** (was 19+1; scenario D un-skipped, no regressions).
- Debugging notes: extraction was initially fooled by 12-digit IDs (fixed with label-aware ordering) and case-sensitive label matching (fixed with `re.IGNORECASE`).

## Notes

- Scope: single-form PDFs. Multi-form legacy bulk (no QR) still goes through the existing page-split fallback; Tier 2 for page groups can build on `match_text` in a later pass.
- OCR path is untested in CI (pytesseract not installed); it degrades to no-match, so it can't break the pipeline.
- Diff ~430 lines (module + tests + wiring + doc updates).
