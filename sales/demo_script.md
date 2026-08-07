# Demo Script — Tessera AI Indexer

A 10-minute, scripted walkthrough. Every command below is the real product —
nothing mocked. Total setup: one machine, one config file.

> Run from a machine with the wheel installed (`pip install tessera-indexer[onnx]`)
> or the container. Commands marked `(source)` run from a source checkout.

---

## Scene 0 — Install & verify (60s)

```bash
tessera-indexer check
```

Expected output:

```
Tessera AI Indexer install check
  version:   0.1.0
  taxonomy:  6 schema(s): claim_death, claim_retirement, maintenance_client, maintenance_contrib, new_business, repurchase
  tier1 QR:  ok
  tier4:     onnx        # or "tfidf" without the deep model
```

**Talk track:** one command tells you the whole install is healthy — taxonomy
loaded, both deterministic tiers up, deep model loaded. No data has left the
machine to get here.

## Scene 1 — Clean modern form, auto-routed (90s)

```bash
# (source) demo over 10 mixed corpus emails
PYTHONPATH=. python main_demo.py
```

Expected: QR-coded forms route instantly — `confidence 100.0%`, status
`pending`, work queues populated in `data/workqueues/`.

**Talk track:** Tier 1 reads the QR on the form — the form literally declares
its own type, page count, and completeness. Deterministic, 100% confidence,
zero ML involved.

## Scene 2 — Legacy paper form, no QR (2 min)

The client's old forms have no QR. Tier 2 reads their printed structure.

```bash
tessera-indexer classify --file legacy_body.txt   # or route a legacy PDF via ingest-batch
```

Expected: `method: tier2_template`, confidence 0.95, sub_type matched from
the form's own `Form Ref` / section markers. In the queue: `status: pending`.

**Talk track:** the form says what it is on the page — form reference, section
headers, field labels. We match that structure deterministically. This is the
case that used to require an ML model; now it's instant and explainable.

## Scene 3 — Messy free-text email, no attachment (2 min)

```bash
tessera-indexer classify --file messy_body.txt
```

Expected: `tier: 3`, `method: local_ner_keyword`, prediction from weighted
keyword/taxonomy evidence (incl. Afrikaans), extracted policy number + client
name in the output.

**Talk track:** no form at all — just an email saying "please withdraw R5,000
from my policy". Tier 3 extracts the entities and classifies intent from
language evidence before any model is touched. Cheap, fast, explainable.

## Scene 4 — The safety net: HITL review (2 min)

Show the review queue after a mixed batch:

```bash
ls data/human_review/ && head -3 data/human_review/review_manifest.jsonl
```

Expected: items below the confidence threshold, unsigned forms, or unreadable
scans land here with an `rfi_reason` (e.g. "Page(s) 5 of 5 missing", "Attachment
contains no readable text").

**Talk track:** nothing is ever silently dropped. Every uncertain document goes
to a human with the reason attached — that's the compliance story.

## Scene 5 — The sovereignty proof (2 min)

While a batch runs, show there is no outbound network:

```bash
# (source) run a batch in one terminal…
PYTHONPATH=. python pilot/simulate.py --num-emails 200 --wave-size 20 --wave-delay 0
# …and in another, watch connections:
lsof -nP -iTCP -sTCP:ESTABLISHED | grep -i python || echo "no outbound connections"
```

Expected: no connections from the indexer process (or only your SSH session).

**Talk track:** the pipeline makes zero network calls — verified in the code
and observable on the wire. Firewall egress can be disabled entirely; the
container even runs with `--network none` if the inbox is a mounted volume.

## Scene 6 — The numbers (60s)

Show `sales/metrics_snapshot.md`:

- 99.99% routing accuracy, 10k-document corpus (attachment-aware)
- 97.3% auto-routed without a human, 100% of auto-routed correct
- 100/100 adversarial edge cases
- Simulated pilot: 600 emails, 153 ms avg latency, 5.7% HITL rate
- Threshold sweep: the auto-route knob and its trade-off curve

**Talk track:** every number is reproducible from the repo's eval harness.
The pilot path means we measure on *their* mail before they commit.

---

## Close

> "You give us a read-only copy of your inbound queue for two weeks. We run
> the pilot, you get a documented accuracy/HITL/throughput report, and the
> system runs entirely inside your infrastructure. If the numbers don't
> convince you, we walk away — you've lost nothing but a shared folder."

## Demo tips

- Run Scene 1–4 back-to-back from one `data/corpus_10k` corpus — no waiting.
- Pre-generate the corpus before the demo: `PYTHONPATH=. python generator/scale_corpus.py`.
- If the deep model (`model.onnx`) isn't installed, scenes still work — Tier 4
  degrades to TF-IDF/unknown and scenes 1–3 don't need it. Install note is on
  the on-prem checklist.
