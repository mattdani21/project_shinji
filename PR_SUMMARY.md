# M1.4 — On-prem install checklist (data-sovereignty doc)

## What

`docs/on_prem_install.md` — the on-prem install checklist that closes out M1.
Sections:

1. **Prerequisites** — OS/Python/disk; explicit "no internet requirement at runtime"
2. **Install** — wheel path (`pip install tessera-indexer[onnx]`) or container path
3. **Model placement** — ONNX + label_map + TF-IDF placement (models are trained artifacts, not shipped in the wheel)
4. **Configuration** — copy the annotated example, set paths + `hitl_threshold`, confirm with `tessera-indexer config`
5. **Verify the install** — one command: `tessera-indexer check` (6 schemas, tier1 ok, tier4 backend)
6. **Data-sovereignty guarantees (verify, don't assume)** — firewall: inbound mail only / zero outbound HTTPS; no telemetry; `api_used` is always a local backend; optional `--network none` container hardening
7. **Go live** — batch backfill, watcher mode, HITL review loop, backups of queue/review dirs + config
8. **Operations** — log routing, model updates without code changes, threshold tuning via `training/calibrate.py`, rollback

Plus a definition of done: a machine that never saw the repo stands up end-to-end
from this doc + README with a green `check` and a routed inbound document.

## Why

M1's final item, and the product's core sales claim: **data sovereignty — no
data leaves the local environment.** The checklist turns that claim into a
verifiable install procedure (firewall/egress sign-off), which is what an
investor-facing install conversation needs.

## How tested

- **Network-call audit**: grepped `indexer/` for any HTTP/network usage —
  the routing pipeline (Tier 1 QR, Tier 4 ONNX/TF-IDF, queues, HITL) makes
  **zero network calls**. The only HTTP client in the repo is
  `indexer/tiers/baselines.py` (an API-baseline benchmark) and nothing imports
  it — it is unreferenced/opt-in. The checklist's sovereignty claims are
  therefore verified against the actual code, not assumed.
- Every command in the doc was exercised during PRs #3/#5 verification
  (wheel install, `check`, `config`, `classify`, `ingest-batch` paths,
  container `--network none` pattern is standard Docker).
- M1 definition of done: fresh-machine install from the artifact using docs +
  one command (`pip install …` then `tessera-indexer check`) — all four M1
  items are now checked off, CI is in place and runs on this PR.

## Notes

- Doc-only PR (~200 lines). No code changes.
- The `python -c` one-liner in section 4 for copying the example config was
  tested against the installed wheel (path resolution confirmed in PR #5).
