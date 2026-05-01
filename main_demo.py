import os
import argparse

def run_demo(manifest_path: str = "data/corpus_10k/manifest_10k.parquet", num_samples: int = 10):
    import pandas as pd
    from indexer.rules.engine import RuleEngine
    from indexer.hitl.exporter import HITLExporter

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

def main():
    parser = argparse.ArgumentParser(description="Run the Tessera AI Indexer demo.")
    parser.add_argument("--dashboard", action="store_true", help="Run the local dashboard UI instead of the CLI demo.")
    parser.add_argument("--live", action="store_true", help="Connect to a real IMAP mailbox for live processing (requires config/mailbox.env).")
    parser.add_argument("--host", default="127.0.0.1", help="Dashboard host when --dashboard is set.")
    parser.add_argument("--port", default=8765, type=int, help="Dashboard port when --dashboard is set.")
    parser.add_argument("--open", action="store_true", help="Open the dashboard in a browser.")
    parser.add_argument("--manifest", default="data/corpus_10k/manifest_10k.parquet", help="Manifest path for the CLI demo.")
    parser.add_argument("--samples", default=10, type=int, help="Number of samples for the CLI demo.")
    args = parser.parse_args()

    if args.dashboard:
        from indexer.dashboard import run, STATE

        if args.live:
            # Start with an empty inbox for live mode
            STATE.reset_empty()

            try:
                from indexer.imap_watcher import IMAPWatcher, load_credentials

                creds = load_credentials()
                watcher = IMAPWatcher(
                    host=creds.get("TESSERA_IMAP_HOST", "imap.gmail.com"),
                    email_addr=creds["TESSERA_IMAP_EMAIL"],
                    password=creds["TESSERA_IMAP_PASSWORD"],
                    folder=creds.get("TESSERA_IMAP_FOLDER", "INBOX"),
                    poll_interval=int(creds.get("TESSERA_POLL_INTERVAL", "5")),
                    on_email=STATE.push_email,
                )
                watcher.start()
                print("IMAP watcher started. Emails will appear on the dashboard as they arrive.")
            except FileNotFoundError as exc:
                print(f"\n⚠️  {exc}")
                print("Running dashboard without live mailbox connection.\n")
            except Exception as exc:
                print(f"\n⚠️  IMAP watcher failed to start: {exc}")
                print("Running dashboard without live mailbox connection.\n")

        run(host=args.host, port=args.port, open_browser=args.open)
        return

    run_demo(manifest_path=args.manifest, num_samples=args.samples)


if __name__ == "__main__":
    main()
