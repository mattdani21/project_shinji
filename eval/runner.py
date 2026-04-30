import os
import json
import pandas as pd
from eval.metrics import calculate_accuracy, calculate_ece, calculate_auto_route
from indexer.tiers.baselines import DummyBaseline, RandomBaseline, GeminiCeiling

def run_eval(model_name: str, manifest_path: str = "data/manifest.parquet", sample_size: int = None):
    print(f"Running evaluation for model: {model_name}")
    df = pd.read_parquet(manifest_path)
    
    if sample_size and sample_size < len(df):
        df = df.sample(n=sample_size, random_state=42).reset_index(drop=True)
        print(f"  Using stratified sample of {sample_size} emails")
    
    if model_name == "dummy":
        model = DummyBaseline()
    elif model_name == "random":
        model = RandomBaseline()
    elif model_name == "gemini_ceiling":
        model = GeminiCeiling()
    elif model_name == "local_tier4":
        from indexer.rules.engine import RuleEngine
        # We wrap the rule engine's classify_email method
        engine = RuleEngine()
        class LocalModelWrapper:
            def predict(self, body):
                res = engine.classify_email(body)
                # Map keys to match what the runner expects
                return {
                    "prediction": res["prediction"],
                    "confidence": res["confidence"],
                    "latency_ms": res.get("latency_ms", 0.0),
                    "api_used": res.get("method", "local")
                }
        model = LocalModelWrapper()
    else:
        raise ValueError(f"Unknown model {model_name}")
        
    results = []
    total = len(df)
    
    for idx, row in df.iterrows():
        if (idx + 1) % 20 == 0:
            print(f"  [{idx+1}/{total}]")
            
        # Load body text
        with open(row["body_path"], "r") as f:
            body = f.read()
            
        if isinstance(model, DummyBaseline):
            out = model.predict(body, row["sub_type"])
        else:
            out = model.predict(body)
            
        results.append({
            "email_id": row["email_id"],
            "ground_truth": row["sub_type"],
            "prediction": out["prediction"],
            "confidence": out["confidence"],
            "latency_ms": out["latency_ms"],
            "api_used": out["api_used"]
        })
        
    res_df = pd.DataFrame(results)
    
    # Calculate metrics
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
        "avg_latency_ms": avg_latency
    }
    
    os.makedirs("data/runs", exist_ok=True)
    out_path = f"data/runs/{model_name}_results.json"
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
        
    # Save predictions
    res_df.to_parquet(f"data/runs/{model_name}_preds.parquet", index=False)
    
    print(f"Evaluation complete. Accuracy: {acc:.2f}, ECE: {ece:.2f}, Auto-route: {route:.2f}, HC-Acc: {hc_acc:.2f}")
    return report

if __name__ == "__main__":
    import sys
    model = sys.argv[1] if len(sys.argv) > 1 else "random"
    sample = int(sys.argv[2]) if len(sys.argv) > 2 else None
    run_eval(model, sample_size=sample)

