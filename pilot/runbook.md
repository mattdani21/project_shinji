# Pilot Runbook — Tessera AI Indexer

How to run a pilot against a **real inbound-document queue** (business
operations), from the packaged artifact, fully local.

## 0. Prerequisites

- [ ] A deployed install per the [on-prem checklist](../docs/on_prem_install.md) — wheel or container, `tessera-indexer check` green
- [ ] Trained Tier-4 model present (`models/tessera-encoder-v1/model.onnx` + `label_map.json`) — optional but recommended for the pilot
- [ ] Access to a **real inbound queue**: either an IMAP mailbox the business receives into, or a network share where inbound emails (`.txt` body + `.pdf` attachment pairs) are dropped
- [ ] Config file pointing `inbox_dir` / `queue_dir` / `review_dir` at the pilot workspace (keep pilot data separate from production queues)

## 1. Ingest

Pick the mode that matches the business queue:

| Queue type | Mode | Command |
|---|---|---|
| IMAP mailbox | watcher | `tessera-indexer watch` (via `python -m indexer.ingest watch`, config-backed) |
| File drop folder | batch (scheduled) | `tessera-indexer ingest-batch <inbox_dir> --config tessera_indexer.yaml` |

For a first pilot, prefer **batch mode over a bounded window** (e.g. one
business day of mail replayed through the drop folder): it gives a complete,
reproducible dataset.

## 2. Run

```bash
# replay the window in waves (every 5 min, 25 emails per wave, e.g. via cron)
tessera-indexer ingest-batch /data/pilot-inbox --config /data/pilot/tessera_indexer.yaml
```

Observe:
- Work-queue files appear under `queue_dir` (`<team>.jsonl`) — policy_admin, new_business, claims, broker_comms, unknown
- Low-confidence / incomplete items land in `review_dir` with `review_manifest.jsonl`

## 3. HITL review loop (the humans)

- [ ] Reviewers process `review_dir` items: confirm/override the AI prediction, note the RFI reason (missing pages, unreadable attachment, low confidence)
- [ ] Accepted items are moved to the team queue; the override outcome is the ground truth for the pilot report

## 4. Measure

Two measurement paths:

**A. Simulated pilot (machinery validation, no business data):**
```bash
PYTHONPATH=. python pilot/simulate.py --num-emails 500 --wave-size 20 --wave-delay 2
PYTHONPATH=. python pilot/metrics.py pilot/reports/pilot_sim_results.csv
```
Produces `pilot/reports/pilot_report.md`: accuracy, HITL rate, latency,
queue distribution, route methods, RFI threshold sweep, sovereignty check.

**B. Real pilot (business data):** run the same metrics over the review
manifest + queue files:

```bash
# per-email ground truth comes from the HITL review outcomes;
# use the eval harness with a pilot manifest:
PYTHONPATH=. python eval/runner.py local_pipeline_full --manifest <pilot_manifest.parquet>
PYTHONPATH=. python eval/run_comparison.py <pilot_manifest.parquet>
```

Manual tally template:

| email_id | ground truth (HITL) | AI prediction | method | confidence | auto/HITL | latency ms |
|---|---|---|---|---|---|---|
| … | | | | | | |

Metrics to report (the M3 DoD list):
1. **Routing accuracy** — AI prediction == HITL-confirmed truth
2. **HITL rate** — share of items sent to human review
3. **Queue throughput** — emails processed per minute (batch timestamps) and per-queue volumes
4. **RFI threshold behavior** — the `hitl_threshold` sweep from `pilot/metrics.py`: auto-route % vs auto-route accuracy at 0.70–0.95; pick the operating point where auto-route accuracy stays ≥ 99%
5. **Data sovereignty confirmation** — all `api_used` values are local backends; firewall/egress check signed off (section 6 of the install checklist)

## 5. Fix findings

- Findings from the pilot go back into `indexer/` (tier logic, thresholds, extraction patterns) with tests
- Threshold changes are config-only (`hitl_threshold` in `tessera_indexer.yaml`) — no code deploy needed

## 6. Pilot exit criteria

- [ ] ≥ 1 week of real inbound processed with **zero silent drops** (every email yields ≥ 1 routed task or a review item)
- [ ] Accuracy + HITL rate + throughput documented in `pilot/reports/`
- [ ] Auto-route operating point chosen from the threshold sweep
- [ ] Inference confirmed 100% local (sovereignty sign-off)
