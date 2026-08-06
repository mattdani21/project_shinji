# M3 — Pilot machinery + simulated pilot + findings fixes

## What

The pilot install milestone, prepared and partially executed:

**`pilot/simulate.py`** — timed inbound-stream simulation through the **real** ingest → route → HITL loop: samples the generated corpus (+ all adversarial edge cases) into an inbox in waves with inter-arrival pacing, runs `RuleEngine.process_inbound` per email (the same path the watcher/batch ingest uses), records prediction/confidence/method/status/latency/routed_to per email.

**`pilot/metrics.py`** — the M3 DoD measurement report:
- routing accuracy (overall + by diversity)
- HITL rate (share to human review)
- avg per-email latency + queue distribution (throughput proxy)
- **RFI threshold sweep** (0.70–0.95): auto-route % vs auto-route accuracy — the business tuning knob
- data-sovereignty confirmation (every route method must be a local backend)

**`pilot/runbook.md`** — how to run the pilot on a **real** inbound queue: ingest modes (IMAP watcher / batch replay), HITL review loop with override-as-ground-truth, measurement path, findings loop, exit criteria.

**Findings from the simulated pilot, fixed back into `indexer/`:**
1. **Flaky QR scan could kill an inbound** — one `cv2` QR-detection failure on a render made `process_inbound` return `error` (1/10,000 in the M2 eval; non-reproducible on re-run). Tier 1 scan failures now fall through to Tier 2 instead of erroring. Stress-tested 25/25 clean.
2. **Body-only routes were invisible to monitoring** — the body-only branch returned no `method`, so pilots/eval saw "unknown" and sovereignty checks flagged it. Now returns `body_only_classify` + `tier`.

## Why

M3's DoD needs a documented accuracy/HITL/throughput report with local inference. Business mail isn't available to the autopilot, so the machinery was built, validated on a 600-email simulated stream, and handed off with a runbook — the real pilot is one config + one command away.

## How tested — simulated pilot results (600 emails: 500 corpus + 100 adversarial, 2026-08-06)

- **Routing accuracy: 100.0% (600/600)** — every diversity slice 100% (clean, legacy, afrikaans, cover_letter, broker_bulk, incomplete, mismatch, body_only)
- **HITL rate: 5.7%** (34 emails to human review — the genuinely low-confidence/unreadable ones)
- **Avg per-email latency: 153 ms** (161 ms first run)
- **Queue distribution**: policy_admin 73.5%, new_business 16.7%, claims 9.8% (broker bulk decomposes into per-client team tasks)
- **Route methods**: tier1 QR 81.3%, tier2 template 14.7%, tier2 unreadable 2.3%, body-only classify 1.7%
- **Data sovereignty: OK** — all methods local
- **RFI threshold sweep**: 0.70–0.80 → **97.7% auto-route at 100% auto-route accuracy** (recommended operating point; default 0.85 gives 94.3%)
- Full suite: **50 passed, 0 skipped** (incl. new pilot-metrics tests)

## Notes

- `data/corpus_10k/`, `pilot/reports/` (csv/md) are gitignored; the report contents are recorded in STATE.md and this summary.
- Remaining M3 work needs owner access to real business mail — flagged in the handoff, not blocked: `pilot/runbook.md` is the path.
- Diff ~600 lines (pilot machinery + engine fixes + tests + docs).
