import os
import pandas as pd
from indexer.rules.engine import RuleEngine
from indexer.hitl.exporter import HITLExporter, process_pipeline

def run_demo(manifest_path: str = "data/corpus_10k/manifest_10k.parquet", num_samples: int = 10):
    print("=== Tessera AI Indexer Demo ===")
    
    if not os.path.exists(manifest_path):
        print(f"Manifest not found at {manifest_path}. Please run scale_corpus.py first.")
        # Fallback to original manifest if available
        if os.path.exists("data/manifest.parquet"):
            manifest_path = "data/manifest.parquet"
        else:
            return

    print(f"Loading samples from {manifest_path}...")
    df = pd.read_parquet(manifest_path)
    
    # Take a mix of diversities
    samples = []
    for div in df["diversity"].unique():
        samples.append(df[df["diversity"] == div].head(2))
    
    demo_df = pd.concat(samples).sample(frac=1).reset_index(drop=True).head(num_samples)
    
    engine = RuleEngine()
    exporter = HITLExporter()
    
    all_results = []
    
    print(f"\nProcessing {len(demo_df)} Mixed Samples...")
    for _, row in demo_df.iterrows():
        with open(row["body_path"], "r") as f:
            body = f.read()
        
        # In main_demo, we pass the attachment if it exists
        attachment = row.get("pdf_path")
        
        # Using engine.process_inbound for full pipeline (Tier 1 -> Tier 4)
        res = engine.process_inbound(row["email_id"], body, attachment)
        
        # Wrap for display
        if res["type"] == "single":
            task = res["tasks"][0]
            print(f"  [{row['diversity']:<12}] Email {row['email_id'][:12]}: {task['sub_type']} ({task['confidence']:.1%}) -> {task['status']}")
            all_results.append(task)
        else:
            print(f"  [{row['diversity']:<12}] Email {row['email_id'][:12]}: Bulk ({res['total_tasks']} tasks) -> {res['method']}")
            for task in res["tasks"]:
                all_results.append(task)

    print("\n=== Final Tally ===")
    if all_results:
        res_df = pd.DataFrame(all_results)
        print(res_df["status"].value_counts())
    
    print(f"\nWork queues populated in: data/workqueues/")
    print(f"Human review files exported to: {exporter.review_dir}")

if __name__ == "__main__":
    run_demo()
