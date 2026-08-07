# Packaging & Pricing Options — Tessera AI Indexer (DRAFT)

> **Stakes flag:** pricing is a business decision for the owner. This document
> proposes defensible options and price anchors based on the product's
> positioning (on-prem, data-sovereign, large-investor segment). Treat every
> number as a starting point, not a commitment. The roadmap item asks for
> options — here they are.

## Packaging units

The product ships one artifact (`tessera-indexer` wheel or container) with
per-site config. What varies per customer is **what they're paying for**:

| Unit | What it covers | Why it works |
|---|---|---|
| **Per install** | One deployment site (all teams/queues, unlimited volume) | Simple, enterprise-friendly, matches "on-prem" story |
| **Per queue** | Per team queue (policy admin, claims, new business, broker comms) | Scales with org structure; upsell path |
| **Per volume** | Documents/month (tiered) | Aligns price with value delivered; caps risk |

## Option A — Per-install license (classic on-prem)

- **Setup fee:** one-time, covers install, config, model training on client
  taxonomy, pilot run, HITL operator training
- **License:** annual, per site, includes unlimited queues + documents
- **Support & updates:** 20% of license/yr (SLA tiers available)
- **Anchor bands (USD/yr):** SMB pilot ~$18–25k · mid-size ~$40–60k ·
  enterprise ~$90–150k — license scales with queue count and doc volume at
  quoting time, not by a fixed per-unit rate

**Pros:** predictable revenue, easiest procurement (single PO). **Cons:**
harder to expand beyond initial scope; volume risk sits with client.

## Option B — Per-queue subscription

- **Per queue per month** (policy_admin, new_business, claims, broker_comms):
  anchor **$1.2–2.5k/queue/mo** ($15–30k/queue/yr), volume included
- Typical 4-queue deployment: **$60–120k/yr**
- Pilot discount: first queue at 50% for 3 months

**Pros:** matches the client's org chart, natural upsell (new team = new
queue), lower entry price. **Cons:** needs queue-level metering (the system
already writes per-queue JSONL — trivial to meter).

## Option C — Volume-tiered

- Tiers by documents/month (emails + attachments routed):
  - up to 5k docs/mo: **$2–3k/mo**
  - 5–25k: **$5–8k/mo**
  - 25–100k: **$12–20k/mo**
  - 100k+: custom
- Includes all queues; HITL operator seats included to 3 (extra seats +$250/mo)

**Pros:** price tracks value; low-risk entry; scales to their growth. **Cons:**
metering + forecasting overhead; revenue less predictable.

## Recommended go-to-market stack

1. **Pilot package (fixed fee):** 2-week measured pilot on their real inbound
   queue — report (accuracy/HITL/throughput), threshold tuning, exit criteria.
   Fee credited against the first year on close. *(This is exactly what M3
   machinery produces.)*
2. **Standard package:** Option B (per-queue) for mid-size, Option A
   (per-install) for enterprise procurement preference.
3. **Enterprise:** per-install + guaranteed SLA + dedicated model retraining
   on their taxonomy + quarterly threshold calibration.

## Discount / levers

- Multi-year (2–3 yr) commitments: 10–20%
- Multi-site (branch operations): 15% per additional site
- Reference-pilot credit: if the pilot converts, first-year fee minus pilot fee
- Bundled training: client-specific model training included in year 1

## What would change the numbers

- **Real-pilot data (M3):** if real-mail HITL rate or accuracy differs
  materially from the simulated pilot (5.7% HITL, 100% accuracy), re-anchor
  pricing on the demonstrated cost-per-document-saved.
- **Competitor signal:** incumbents (manual ops teams, legacy ECM + RPA
  stacks) are priced per seat + per hour of ops labor; the pitch is
  substitution of manual triage, not software seats.
- **Segmentation:** large investors (the GOAL) buy on sovereignty + SLA, not
  price — anchor high, discount rarely.

## Suggested first close

> **$24k pilot → $96k/yr standard (4 queues, Option B)** — or the enterprise
> per-install at $90k/yr. Pilot fee credited on conversion.
