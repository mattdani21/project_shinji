"""Eval harness comparison for the M2 tiers.

Runs the pre-Tier-3 baseline (tier4-only) against the full pipeline on a
generated corpus manifest, plus an attachment-aware full-pipeline run, and
writes a comparison report.

Usage:
    PYTHONPATH=. python eval/run_comparison.py data/corpus_eval/manifest_10k.parquet
"""
import json
import os
import sys

from eval.runner import run_eval
from eval.compare import compare_runs


def main(manifest_path: str = "data/corpus_eval/manifest_10k.parquet", sample_size=None):
    runs = [
        ("local_tier4_only", "pre-Tier-3 baseline (body text)"),
        ("local_pipeline", "full pipeline, body text (Tier 1/3/4)"),
        ("local_pipeline_full", "full pipeline, attachment-aware (Tier 1/2/3/4)"),
    ]
    reports = {}
    for name, desc in runs:
        print(f"\n=== {desc} ===")
        reports[name] = run_eval(name, manifest_path=manifest_path, sample_size=sample_size)

    compare_runs([n for n, _ in runs])

    print("\n=== SUMMARY ===")
    base = reports["local_tier4_only"]
    new = reports["local_pipeline"]
    print(f"Body-text accuracy:  {base['accuracy']:.3f} (tier4-only) -> {new['accuracy']:.3f} (full pipeline)")
    print(f"Auto-route %:        {base['auto_route_pct']:.3f} -> {new['auto_route_pct']:.3f}")
    print(f"Auto-route accuracy: {base['hc_accuracy']:.3f} -> {new['hc_accuracy']:.3f}")
    full = reports["local_pipeline_full"]
    if "method_distribution" in full:
        print(f"Full-pipeline tier distribution: {full['method_distribution']}")
    return reports


if __name__ == "__main__":
    manifest = sys.argv[1] if len(sys.argv) > 1 else "data/corpus_eval/manifest_10k.parquet"
    sample = int(sys.argv[2]) if len(sys.argv) > 2 else None
    main(manifest, sample)
