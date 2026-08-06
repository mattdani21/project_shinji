"""Simulated pilot: a timed inbound stream through the real pipeline.

Pilot protocol (mirrors a real deployment):
  1. Sample emails from the generated corpus (+ adversarial edge cases) into
     an inbox directory, in waves, with realistic inter-arrival timing.
  2. Each wave runs the real ingest path (`batch_ingest` semantics, engine
     per batch like the watcher would create).
  3. Every email's routing decision is recorded: prediction, confidence,
     route method, status (auto-routed vs HITL review), latency.

This exercises the same ingest -> route -> HITL loop a real pilot runs;
the only difference from production is the source of the inbound documents
(synthetic instead of business mail). Run the real pilot per `runbook.md`.

Usage:
    PYTHONPATH=. python pilot/simulate.py --manifest data/corpus_10k/manifest_10k.parquet \
        --num-emails 500 --wave-size 20 --wave-delay 2 --out pilot/reports
"""
import argparse
import csv
import os
import random
import shutil
import time

from indexer.rules.engine import RuleEngine


def _load_samples(manifest_path, adversarial_manifest, num_emails, rng):
    import pandas as pd

    def _path(v):
        if v is None:
            return ""
        try:
            if pd.isna(v):
                return ""
        except (TypeError, ValueError):
            pass
        return str(v)

    samples = []
    df = pd.read_parquet(manifest_path)
    df = df.sample(n=min(num_emails, len(df)), random_state=42)
    for _, row in df.iterrows():
        samples.append({
            "email_id": row["email_id"],
            "ground_truth": row["sub_type"],
            "body_path": row["body_path"],
            "pdf_path": _path(row.get("pdf_path")),
            "diversity": row.get("diversity", "clean"),
        })

    # Adversarial edge cases ride along (legacy, incomplete, mismatch, body-only…)
    if adversarial_manifest and os.path.exists(adversarial_manifest):
        adv = pd.read_csv(adversarial_manifest)
        for _, row in adv.iterrows():
            samples.append({
                "email_id": row["email_id"],
                "ground_truth": row["ground_truth"],
                "body_path": row["body_path"],
                "pdf_path": _path(row.get("attachment_path")),
                "diversity": row.get("category", "adversarial"),
            })
    rng.shuffle(samples)
    return samples


def run_pilot(manifest_path, num_emails=500, wave_size=20, wave_delay=2.0,
              adversarial_manifest="data/adversarial_test/adversarial_manifest.csv",
              out_dir="pilot/reports"):
    rng = random.Random(1234)
    os.makedirs(out_dir, exist_ok=True)
    inbox = os.path.join(out_dir, "inbox")
    if os.path.exists(inbox):
        shutil.rmtree(inbox)
    os.makedirs(inbox)

    samples = _load_samples(manifest_path, adversarial_manifest, num_emails, rng)
    print(f"Pilot: {len(samples)} inbound emails, waves of {wave_size} every {wave_delay}s")

    engine = RuleEngine()
    rows = []
    wave_clock = 0.0
    start = time.time()

    for wave_idx in range(0, len(samples), wave_size):
        wave = samples[wave_idx:wave_idx + wave_size]
        wave_start = time.time()

        for s in wave:
            # Stage the email into the inbox (watcher-equivalent arrival)
            body_dst = os.path.join(inbox, f"{s['email_id']}_body.txt")
            shutil.copy(s["body_path"], body_dst)
            pdf_dst = None
            if s["pdf_path"] and os.path.exists(s["pdf_path"]):
                pdf_dst = os.path.join(inbox, f"{s['email_id']}_attachment.pdf")
                shutil.copy(s["pdf_path"], pdf_dst)

            with open(body_dst) as f:
                body = f.read()

            t0 = time.perf_counter()
            out = engine.process_inbound(s["email_id"], body, pdf_dst)
            latency_ms = (time.perf_counter() - t0) * 1000

            if out["type"] == "error":
                rows.append({
                    "email_id": s["email_id"], "diversity": s["diversity"],
                    "ground_truth": s["ground_truth"], "prediction": "error",
                    "confidence": 0.0, "method": "error", "status": "error",
                    "latency_ms": round(latency_ms, 1), "routed_to": "",
                })
                continue

            method = out.get("method", "unknown")
            tasks = out.get("tasks") or []
            if out["type"] == "bulk" and method.startswith("tier1"):
                pred, conf = "bulk_instructions", (tasks[0]["confidence"] if tasks else 1.0)
                status = "pending" if conf >= engine.config.hitl_threshold else "review"
            elif tasks:
                pred, conf = tasks[0]["sub_type"], tasks[0]["confidence"]
                status = tasks[0]["status"]
            else:
                pred, conf, status = "unknown", 0.0, "review"

            rows.append({
                "email_id": s["email_id"], "diversity": s["diversity"],
                "ground_truth": s["ground_truth"], "prediction": pred,
                "confidence": conf, "method": method, "status": status,
                "latency_ms": round(latency_ms, 1),
                "routed_to": (tasks[0].get("routed_to") or out.get("routed_to") or "") if tasks else "",
            })

        # Simulated inter-arrival pacing
        wave_clock += wave_delay
        elapsed = time.time() - start
        if wave_clock > elapsed:
            time.sleep(wave_clock - elapsed)
        print(f"  wave {wave_idx // wave_size + 1}: {len(wave)} emails "
              f"({(len(rows))}/{len(samples)}) — {time.time() - start:.0f}s elapsed")

    csv_path = os.path.join(out_dir, "pilot_sim_results.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nPilot complete: {len(rows)} emails routed in {time.time() - start:.0f}s")
    print(f"Results: {csv_path}")
    return csv_path


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--manifest", default="data/corpus_10k/manifest_10k.parquet")
    p.add_argument("--num-emails", type=int, default=500)
    p.add_argument("--wave-size", type=int, default=20)
    p.add_argument("--wave-delay", type=float, default=2.0)
    p.add_argument("--out", default="pilot/reports")
    args = p.parse_args()
    run_pilot(args.manifest, args.num_emails, args.wave_size, args.wave_delay, out_dir=args.out)
