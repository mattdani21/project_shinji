# Pilot Report

- **Source**: `pilot/reports/pilot_sim_results.csv`
- **Emails processed**: 600
- **Routing accuracy**: 100.0% (600/600)
- **HITL rate**: 5.7% (34 emails to human review)
- **Avg per-email latency**: 153.4 ms
- **Data sovereignty**: OK — all route methods local

## Queue distribution

- `policy_admin`: 441 (73.5%)
- `new_business`: 100 (16.7%)
- `claims`: 59 (9.8%)

## Route methods

- `tier1_qr_deterministic`: 488 (81.3%)
- `tier2_template`: 88 (14.7%)
- `tier2_unreadable`: 14 (2.3%)
- `body_only_classify`: 10 (1.7%)

## RFI threshold behavior (auto-route % vs auto-route accuracy)

| threshold | auto-route % | auto-route accuracy |
|---|---|---|
| 0.70 | 97.7% | 100.0% |
| 0.75 | 97.7% | 100.0% |
| 0.80 | 97.3% | 100.0% |
| 0.85 | 94.3% | 100.0% |
| 0.90 | 94.0% | 100.0% |
| 0.95 | 94.0% | 100.0% |

## Accuracy by diversity

- `afrikaans`: 100.0% (51 samples)
- `afrikaans_mixed`: 100.0% (20 samples)
- `body_attachment_mismatch`: 100.0% (10 samples)
- `body_only`: 100.0% (10 samples)
- `broker_bulk`: 100.0% (22 samples)
- `clean`: 100.0% (344 samples)
- `cover_letter`: 100.0% (45 samples)
- `incomplete_no_signature`: 100.0% (20 samples)
- `legacy`: 100.0% (58 samples)
- `legacy_no_qr`: 100.0% (20 samples)
