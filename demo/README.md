# Mini Demo — Tessera AI Indexer

One command runs 8 representative inbound emails through the **real**
pipeline (same code path as batch ingest / the IMAP watcher) and prints a
decision table covering every tier plus the human-review paths.

```bash
PYTHONPATH=. python demo/mini_demo.py          # run + auto-clean
PYTHONPATH=. python demo/mini_demo.py --keep   # keep demo/run/ artifacts
```

Requires the dev extras (`pip install -e ".[dev]"`).

## The 8 cases and what to watch

| case | ground truth | expected route | what proves it |
|---|---|---|---|
| `clean_qr` | repurchase | Tier 1 QR · conf 100% · pending | modern forms route instantly, deterministically |
| `cover_letter` | new_business | Tier 1 QR · conf 100% | broker cover page doesn't break page counting |
| `incomplete` | repurchase | Tier 1 · conf 80% · **review** | missing signature page → human review + RFI "Page(s) 5 of 5 missing" |
| `legacy_nqr` | claim_retirement | **Tier 2 template** · conf 95% · pending | no-QR legacy forms matched from printed structure, no ML needed |
| `afrikaans` | maintenance_client | Tier 1 QR | mixed-language email handled |
| `body_only` | maintenance_contrib | **Tier 3 NER** · pending | no attachment — intent from language evidence, entities extracted |
| `unreadable` | repurchase | **Tier 2 unreadable** · conf 50% · **review** | blank/scanned attachment → never silently dropped, RFI explains why |
| `messy_typos` | claim_death | Tier 1 QR | typo-ridden body doesn't matter when the form declares itself |

## After the run

- `demo/run/workqueues/<team>.jsonl` — routed tasks (policy_admin, new_business, claims)
- `demo/run/human_review/` — items needing a human, each with an RFI reason
- Everything cleans itself up unless you pass `--keep`

## For the sales demo

Pair this with the [sales demo script](../sales/demo_script.md) — this mini
demo is the runnable core; the sales script adds the talk track, the
sovereignty proof (`lsof` during a batch), and the metrics close.
