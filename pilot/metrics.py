"""Pilot report: accuracy, HITL rate, queue throughput, RFI threshold sweep.

Reads a pilot results CSV (pilot/simulate.py output) and produces
pilot/reports/pilot_report.md — the documented metrics a real pilot needs:

  - routing accuracy (overall + by diversity/method)
  - HITL rate (share routed to human review)
  - queue throughput (emails/min, per-queue distribution)
  - RFI threshold behavior: auto-route % and auto-route accuracy across
    hitl_threshold values 0.70–0.95 (the business tuning knob)
  - data-sovereignty confirmation (all route methods are local)

Usage:
    PYTHONPATH=. python pilot/metrics.py pilot/reports/pilot_sim_results.csv
"""
import argparse
import csv
import os

from eval.metrics import calculate_accuracy, calculate_auto_route

THRESHOLD_SWEEP = [0.70, 0.75, 0.80, 0.85, 0.90, 0.95]
LOCAL_METHODS = {"tier1_qr_deterministic", "tier2_template", "tier2_unreadable",
                 "body_only_classify", "local_ner_keyword", "tier4_sequence_fallback",
                 "local_ml_fallback"}


def load_rows(csv_path):
    with open(csv_path, newline="") as f:
        return list(csv.DictReader(f))


def build_report(csv_path, out_path=None):
    rows = load_rows(csv_path)
    if not rows:
        raise SystemExit("no rows in results file")

    n = len(rows)
    correct = sum(1 for r in rows if r["prediction"] == r["ground_truth"])
    accuracy = correct / n

    review = [r for r in rows if r["status"] == "review"]
    hitl_rate = len(review) / n

    latencies = [float(r["latency_ms"]) for r in rows]
    avg_lat = sum(latencies) / len(latencies)

    # Throughput: wall-clock is not recorded per wave; estimate from the
    # recorded latencies + a 2s simulated inter-wave gap is simulation
    # specific — report per-email latency + queue distribution instead.
    queue_counts = {}
    for r in rows:
        q = r.get("routed_to") or "unknown"
        queue_counts[q] = queue_counts.get(q, 0) + 1

    method_counts = {}
    for r in rows:
        method_counts[r["method"]] = method_counts.get(r["method"], 0) + 1

    # RFI threshold sweep
    sweep = []
    confs = [float(r["confidence"]) for r in rows]
    preds = [r["prediction"] for r in rows]
    truths = [r["ground_truth"] for r in rows]
    for t in THRESHOLD_SWEEP:
        route_pct, hc_acc = calculate_auto_route(confs, preds, truths, threshold=t)
        sweep.append({"threshold": t, "auto_route_pct": route_pct, "hc_accuracy": hc_acc})

    # Data sovereignty
    non_local = sorted({r["method"] for r in rows} - LOCAL_METHODS)

    lines = []
    lines.append("# Pilot Report\n")
    lines.append(f"- **Source**: `{csv_path}`")
    lines.append(f"- **Emails processed**: {n}")
    lines.append(f"- **Routing accuracy**: {accuracy:.1%} ({correct}/{n})")
    lines.append(f"- **HITL rate**: {hitl_rate:.1%} ({len(review)} emails to human review)")
    lines.append(f"- **Avg per-email latency**: {avg_lat:.1f} ms")
    lines.append(f"- **Data sovereignty**: {'OK — all route methods local' if not non_local else f'VIOLATION: {non_local}'}")
    lines.append("\n## Queue distribution\n")
    for q, c in sorted(queue_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{q}`: {c} ({c / n:.1%})")
    lines.append("\n## Route methods\n")
    for m, c in sorted(method_counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"- `{m}`: {c} ({c / n:.1%})")
    lines.append("\n## RFI threshold behavior (auto-route % vs auto-route accuracy)\n")
    lines.append("| threshold | auto-route % | auto-route accuracy |")
    lines.append("|---|---|---|")
    for s in sweep:
        lines.append(f"| {s['threshold']:.2f} | {s['auto_route_pct']:.1%} | {s['hc_accuracy']:.1%} |")

    # Per-diversity accuracy
    lines.append("\n## Accuracy by diversity\n")
    divs = {}
    for r in rows:
        divs.setdefault(r["diversity"], []).append(r)
    for d, rs in sorted(divs.items()):
        acc = sum(1 for r in rs if r["prediction"] == r["ground_truth"]) / len(rs)
        lines.append(f"- `{d}`: {acc:.1%} ({len(rs)} samples)")

    report = "\n".join(lines) + "\n"
    if out_path is None:
        out_path = os.path.join(os.path.dirname(csv_path), "pilot_report.md")
    with open(out_path, "w") as f:
        f.write(report)
    print(report)
    return out_path


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("csv_path")
    p.add_argument("--out", default=None)
    args = p.parse_args()
    build_report(args.csv_path, args.out)
