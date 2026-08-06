import os
import json
import pandas as pd
from eval.metrics import calculate_accuracy, calculate_ece, calculate_auto_route
from indexer.tiers.baselines import DummyBaseline, RandomBaseline, GeminiCeiling


class LocalModelWrapper:
    """Body-text classification via RuleEngine.classify_email (Tiers 1/3/4)."""

    def __init__(self, engine):
        self.engine = engine

    def predict(self, body, attachment=None):
        res = self.engine.classify_email(body)
        return {
            "prediction": res["prediction"],
            "confidence": res["confidence"],
            "latency_ms": res.get("latency_ms", 0.0),
            "api_used": res.get("method", "local"),
            "tier": res.get("tier") or 0,
        }


class FullPipelineWrapper:
    """Attachment-aware routing via RuleEngine.process_inbound (all 4 tiers).

    Bulk instructions (broker 1:N with QR) map to their own ground-truth
    label; otherwise the first task's sub_type is the prediction.
    """

    def __init__(self, engine):
        self.engine = engine

    def predict(self, body, attachment=None):
        res = self.engine.process_inbound("eval", body, attachment)
        method = res.get("method", "error")
        if res["type"] == "error":
            return {"prediction": "error", "confidence": 0.0, "latency_ms": 0.0,
                    "api_used": method, "tier": 0}
        tasks = res.get("tasks") or []
        if res["type"] == "bulk" and method.startswith("tier1"):
            # Broker bulk: the batch itself is the ground truth
            prediction = "bulk_instructions"
            confidence = tasks[0]["confidence"] if tasks else 1.0
        elif tasks:
            prediction = tasks[0]["sub_type"]
            confidence = tasks[0]["confidence"]
        else:
            prediction = "unknown"
            confidence = 0.0
        return {
            "prediction": prediction,
            "confidence": confidence,
            "latency_ms": res.get("latency_ms", 0.0),
            "api_used": method,
            "tier": 1 if method.startswith("tier1") else 2 if method.startswith("tier2") else 4,
        }


def _make_model(model_name):
    if model_name == "dummy":
        return DummyBaseline()
    if model_name == "random":
        return RandomBaseline()
    if model_name == "gemini_ceiling":
        return GeminiCeiling()
    if model_name == "local_tier4_only":
        from indexer.rules.engine import RuleEngine
        engine = RuleEngine()
        engine.tier3 = None  # pre-Tier-3 baseline: straight to the ML fallback
        return LocalModelWrapper(engine)
    if model_name == "local_pipeline":
        from indexer.rules.engine import RuleEngine
        return LocalModelWrapper(RuleEngine())
    if model_name == "local_pipeline_full":
        from indexer.rules.engine import RuleEngine
        return FullPipelineWrapper(RuleEngine())
    raise ValueError(f"Unknown model {model_name}")


def run_eval(model_name: str, manifest_path: str = "data/manifest.parquet",
             sample_size: int = None):
    print(f"Running evaluation for model: {model_name}")
    df = pd.read_parquet(manifest_path)

    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
        print(f"  Using stratified sample of {sample_size} emails")

    model = _make_model(model_name)

    results = []
    total = len(df)

    for idx, row in df.iterrows():
        if (idx + 1) % 20 == 0:
            print(f"  [{idx+1}/{total}]")

        with open(row["body_path"], "r") as f:
            body = f.read()

        attachment = None
        pdf_col = row.get("pdf_path") if hasattr(row, "get") else None
        if pdf_col and isinstance(pdf_col, str) and os.path.exists(pdf_col):
            attachment = pdf_col

        if isinstance(model, DummyBaseline):
            out = model.predict(body, row["sub_type"])
        else:
            out = model.predict(body, attachment)

        results.append({
            "email_id": row["email_id"],
            "ground_truth": row["sub_type"],
            "prediction": out["prediction"],
            "confidence": out["confidence"],
            "latency_ms": out["latency_ms"],
            "api_used": out["api_used"],
            "tier": out.get("tier") or 0,
            "diversity": row.get("diversity", ""),
        })

    res_df = pd.DataFrame(results)

    # Metrics
    acc = calculate_accuracy(res_df["prediction"], res_df["ground_truth"])
    ece = calculate_ece(res_df["confidence"], res_df["prediction"], res_df["ground_truth"])
    route, hc_acc = calculate_auto_route(res_df["confidence"], res_df["prediction"], res_df["ground_truth"])
    avg_latency = res_df["latency_ms"].mean()

    report = {
        "model_name": model_name,
        "total_samples": len(res_df),
        "accuracy": acc,
        "ece": ece,
        "auto_route_pct": route,
        "hc_accuracy": hc_acc,
        "avg_latency_ms": avg_latency,
    }
    if "tier" in res_df.columns and res_df["tier"].nunique() > 1:
        report["method_distribution"] = (
            res_df.groupby("tier").size().to_dict()
        )

    os.makedirs("data/runs", exist_ok=True)
    out_path = f"data/runs/{model_name}_results.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    res_df.to_parquet(f"data/runs/{model_name}_preds.parquet", index=False)

    print(f"Evaluation complete. Accuracy: {acc:.2f}, ECE: {ece:.2f}, Auto-route: {route:.2f}, HC-Acc: {hc_acc:.2f}")
    return report


if __name__ == "__main__":
    import sys
    model = sys.argv[1] if len(sys.argv) > 1 else "random"
    sample = int(sys.argv[2]) if len(sys.argv) > 2 else None
    manifest = sys.argv[3] if len(sys.argv) > 3 else "data/manifest.parquet"
    run_eval(model, manifest_path=manifest, sample_size=sample)
