"""Pilot machinery: simulated-stream results + metrics report."""
import csv
import os
import pytest

from pilot.metrics import build_report, LOCAL_METHODS

SAMPLE_ROWS = [
    {"email_id": "a1", "diversity": "clean", "ground_truth": "repurchase",
     "prediction": "repurchase", "confidence": "0.95", "method": "tier1_qr_deterministic",
     "status": "pending", "latency_ms": "120.0", "routed_to": "policy_admin"},
    {"email_id": "a2", "diversity": "legacy", "ground_truth": "claim_death",
     "prediction": "claim_death", "confidence": "0.95", "method": "tier2_template",
     "status": "pending", "latency_ms": "180.0", "routed_to": "claims"},
    {"email_id": "a3", "diversity": "body_only", "ground_truth": "new_business",
     "prediction": "new_business", "confidence": "0.76", "method": "body_only_classify",
     "status": "review", "latency_ms": "90.0", "routed_to": "new_business"},
    {"email_id": "a4", "diversity": "clean", "ground_truth": "repurchase",
     "prediction": "maintenance_client", "confidence": "0.60", "method": "local_ner_keyword",
     "status": "review", "latency_ms": "70.0", "routed_to": "policy_admin"},
]


@pytest.fixture
def results_csv(tmp_path):
    path = os.path.join(tmp_path, "results.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(SAMPLE_ROWS[0].keys()))
        writer.writeheader()
        writer.writerows(SAMPLE_ROWS)
    return path


def test_metrics_report_contents(results_csv, tmp_path):
    out = build_report(results_csv, str(tmp_path / "report.md"))
    assert os.path.exists(out)
    with open(out) as f:
        text = f.read()
    assert "Routing accuracy**: 75.0%" in text  # 3/4 correct
    assert "HITL rate**: 50.0%" in text  # 2/4 review
    assert "Data sovereignty**: OK" in text
    assert "RFI threshold behavior" in text


def test_local_methods_cover_all_route_methods():
    assert "tier1_qr_deterministic" in LOCAL_METHODS
    assert "tier2_template" in LOCAL_METHODS
    assert "tier2_unreadable" in LOCAL_METHODS
    assert "body_only_classify" in LOCAL_METHODS
