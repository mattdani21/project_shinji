# Tessera AI Indexer
### The on-prem document router for institutions that cannot afford to send mail out

---

## The problem
Large investors' operations teams manually triage **thousands of inbound emails a day** — repurchases, claims, new business, maintenance — across modern PDF forms, legacy paper forms, and messy free-text messages. Every misfiled document is a compliance risk and a delay.

## The solution: four-tier routing, fully local
Every inbound email is routed through a cascading pipeline, cheapest tier first:

1. **QR routing** — modern forms route instantly, 100% deterministic confidence
2. **Template matching** — legacy no-QR forms identified from their printed structure (form refs, sections, fields)
3. **NER & taxonomy** — policy numbers, IDs, and form intent extracted from unstructured text (incl. Afrikaans)
4. **XLM-RoBERTa ONNX** — the deep-learning safety net for anything ambiguous, running on CPU in-process

**Human-in-the-loop:** anything below the confidence threshold — or missing pages, unsigned forms, unreadable scans — goes to a human review queue with the reason attached (RFI), never silently dropped.

## The guarantee: 100% data sovereignty
- Inference runs **entirely in-process** — no external APIs, no telemetry, no phone-home. Verified: the routing pipeline makes **zero network calls**.
- Deployed as a **wheel or container on the client's own hardware**; firewall/egress sign-off is part of the install checklist.
- Config-driven installs: taxonomy, models, queue dirs, and the auto-route threshold are YAML — no code changes per site.

## Proof (calibrated, reproducible)
| Metric | Result |
|---|---|
| Routing accuracy, attachment-aware pipeline (10k corpus) | **100%** (10,000/10,000) |
| Auto-routed without human review | **97.3%**, of which **100% correct** |
| Adversarial edge cases (legacy, scanned, Afrikaans, mismatched, incomplete) | **100% (100/100)** |
| Simulated pilot, 600 emails end-to-end | **100% accuracy**, 5.7% HITL rate, **153 ms avg latency** |
| Calibration error (ECE) | 0.01 |

*Sources: eval harness + pilot simulator in-repo; see metrics_snapshot.md. Real-mail pilot in progress.*

## The offer
- **On-prem installs** sized per queue or per document volume — license, subscription, or volume pricing (pricing options kept private; on request)
- **Pilot path**: connect the client's real inbound queue for a measured pilot (accuracy, HITL rate, throughput) before committing

---

*Tessera AI Indexer — route everything, ship nothing.*
