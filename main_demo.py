import os
import pandas as pd
from indexer.rules.engine import RuleEngine
from indexer.hitl.exporter import HITLExporter, process_pipeline

def run_demo():
    print("=== Tessera AI Indexer Demo ===")
    engine = RuleEngine()
    exporter = HITLExporter()
    
    # 1. Load some clean samples
    clean_df = pd.read_parquet("data/manifest.parquet").head(5)
    
    # 2. Load some messy samples
    stress_df = pd.read_csv("data/stress_test/stress_manifest.csv").head(5)
    
    all_results = []
    
    print("\nProcessing Clean Samples (Auto-Routing)...")
    for _, row in clean_df.iterrows():
        body = open(row["body_path"]).read()
        res = process_pipeline(engine, exporter, body, row["email_id"])
        all_results.append(res)
        print(f"  Email {row['email_id'][:8]}: {res['prediction']} ({res['confidence']:.2%}) -> {res['status']}")

    print("\nProcessing Messy/Ambiguous Samples (HITL Routing)...")
    for _, row in stress_df.iterrows():
        body = open(row["body_path"]).read()
        res = process_pipeline(engine, exporter, body, row["email_id"])
        all_results.append(res)
        print(f"  Email {row['email_id'][:8]}: {res['prediction']} ({res['confidence']:.2%}) -> {res['status']}")

    print("\n=== Final Tally ===")
    res_df = pd.DataFrame(all_results)
    print(res_df["status"].value_counts())
    print(f"\nHuman review files exported to: {exporter.review_dir}")

if __name__ == "__main__":
    run_demo()
