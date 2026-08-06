# Tessera AI Indexer — On-Prem Install Checklist

The product's selling point is **data sovereignty: no data leaves the local
environment**. Every item below exists to guarantee that property survives a
real install. Follow the checklist top to bottom on a fresh machine.

---

## 1. Prerequisites

- [ ] **OS**: any 64-bit Linux / macOS / Windows with Python **3.9–3.12** (64-bit)
- [ ] **Python** present: `python3 --version` → `3.9+`
- [ ] **Disk**: ~1.5 GB free (wheel + model + runtime data)
- [ ] **No internet requirement at runtime**: the install step needs pip access
      (or offline wheels), but **inference never calls out**
- [ ] (Container path) Docker Engine 20.10+ if installing via image

## 2. Install

Choose one:

- [ ] **Wheel path**
  ```bash
  pip install tessera-indexer[onnx]      # + [gen] if you generate synthetic test data
  tessera-indexer --version              # → tessera-indexer 0.1.0
  ```
- [ ] **Container path**
  ```bash
  docker load < tessera-indexer-0.1.0.tar   # or: docker build -t tessera-indexer .
  docker run --rm tessera-indexer --version
  ```

## 3. Model placement (deep-learning Tier 4)

The ONNX model is **not** shipped in the wheel (it is a trained artifact).
Place it on the machine:

- [ ] Create the model dir (default `models/tessera-encoder-v1/` relative to
      your config — see step 4)
- [ ] Copy `model.onnx` (+ `model.onnx.data` if present), `label_map.json`,
      `training_config.json` into it
- [ ] Optional TF-IDF fallback: copy `tier4_model.joblib` to `models/`
- [ ] Verify: `tessera-indexer check` reports `tier4: onnx`

> The container ships the model dir at `/app/models`; mount your trained
> models with `-v /host/models:/app/models`.

## 4. Configuration

- [ ] Copy the annotated example to your deploy dir:
  ```bash
  # path inside an installed wheel:
  python -c "import indexer.config, pathlib, shutil; \
  src = pathlib.Path(indexer.config.__file__).parent / 'config' / 'example.yaml'; \
  shutil.copy(src, 'tessera_indexer.yaml')"
  ```
- [ ] Set `onnx_model_dir` / `tfidf_model_path` (absolute, or relative — they
      resolve against the config file's dir)
- [ ] Set `queue_dir`, `review_dir`, `inbox_dir` (or accept defaults under the
      working dir)
- [ ] Set `hitl_threshold` (default `0.85`): lower = more auto-routing, higher
      = more human review
- [ ] Confirm effective config: `tessera-indexer config --config tessera_indexer.yaml`
- [ ] Point `$TESSERA_INDEXER_CONFIG` at the file (or run everything with
      `--config`) so cron/scheduled runs use the same settings

## 5. Verify the install (one command)

- [ ] `tessera-indexer check --config tessera_indexer.yaml`
  - [ ] `taxonomy:` lists the 6 schemas (claim_death, claim_retirement,
        maintenance_client, maintenance_contrib, new_business, repurchase)
  - [ ] `tier1 QR: ok`
  - [ ] `tier4: onnx` (or `tfidf` if you only installed the fallback model)
- [ ] Smoke-classify a real inbound email body:
  `tessera-indexer classify --file sample_body.txt`

## 6. Data-sovereignty guarantees (verify, don't assume)

- [ ] **No external inference calls**: Tier 1 (QR) and Tier 4 (ONNX/TF-IDF)
      run entirely in-process. Confirm on the network perimeter:
  - [ ] Firewall rules for the indexer host allow **inbound mail only**
        (IMAP/SMTP or the inbox share) — **no outbound HTTPS required**
  - [ ] If your environment has egress monitoring, verify **zero** outbound
        connections from the indexer process during a batch run
- [ ] **No telemetry**: the wheel makes no analytics/phone-home calls
- [ ] **No cloud model APIs**: `api_used` in classify output is always
      `none (local_onnx)` / `none (local_tfidf_fallback)` — never an endpoint
- [ ] (Optional hardening) Run the container with `--network none` if the
      inbox is a mounted volume instead of IMAP:
  ```bash
  docker run --rm --network none \
    -v /host/models:/app/models -v /host/inbox:/app/data/inbox \
    tessera-indexer ingest-batch /app/data/inbox
  ```

## 7. Go live

- [ ] **Batch mode** (first run / backfill):
  `tessera-indexer ingest-batch /path/to/inbox`
  - [ ] Work-queue files appear under `queue_dir` (`<team>.jsonl`)
  - [ ] Low-confidence items land in `review_dir` with a review manifest
- [ ] **Watcher mode** (ongoing): run `mailbox_watcher` (IMAP poll) or point
      a scheduled job at `ingest-batch`
- [ ] **HITL review loop**: reviewers process `review_dir` items; accepted
      items go to the team queue; RFI reasons (e.g. missing pages) are
      captured in the manifest
- [ ] **Backups**: `queue_dir`, `review_dir`, and the config file are the
      system's state — back them up with the rest of the business data

## 8. Operations notes

- [ ] Log rotation: route `tessera-indexer` stdout/stderr to the site's log
      collector
- [ ] Model updates: replace `model.onnx` + `label_map.json` together, then
      re-run `tessera-indexer check`; no code changes required
- [ ] Threshold tuning: adjust `hitl_threshold` in the config and re-check
      with `training/calibrate.py` (from the source checkout) using the local
      test split
- [ ] Rollback: keep the previous wheel (`pip install tessera-indexer==<old>`)
      or image tag; config is forward/backward compatible

---

**Definition of done for this checklist:** a machine that has never seen the
repository can be stood up end-to-end following only this document plus the
README, ending with a green `tessera-indexer check` and a successfully routed
inbound document — with the firewall/egress verification in section 6 signed
off.
