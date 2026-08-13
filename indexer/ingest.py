"""
Ingestion Layer for Tessera AI Indexer.

Two modes of operation:
1. Batch Mode:   Process a folder of .eml or .txt + .pdf files in bulk.
2. Watcher Mode: Poll a mailbox (IMAP) and process emails as they arrive.

Both modes feed into RuleEngine.process_inbound() which handles
PDF splitting, classification, and work queue routing.
"""
import os
import glob
import json
import time
import datetime
from typing import Optional


def batch_ingest(input_dir: str, engine=None, config=None):
    """
    Batch Mode: Scan a directory for email bodies and their PDF attachments.
    
    Expected file naming convention:
      {email_id}_body.txt     — the email body
      {email_id}_attachment.pdf  OR  {email_id}_bulk_attachment.pdf — the PDF
    
    Processes all emails in the directory and routes to work queues.
    """
    if engine is None:
        from indexer.rules.engine import RuleEngine
        engine = RuleEngine(config=config)
        
    body_files = sorted(glob.glob(os.path.join(input_dir, "*_body.txt")))
    
    print(f"Batch Ingest: Found {len(body_files)} emails in {input_dir}")
    results = []
    
    for body_path in body_files:
        # Derive email_id from filename
        basename = os.path.basename(body_path)
        email_id = basename.replace("_body.txt", "")
        
        # Read body
        with open(body_path, "r") as f:
            body_text = f.read()
            
        # Find attachment (try both naming patterns)
        attachment_path = None
        for suffix in ["_attachment.pdf", "_bulk_attachment.pdf"]:
            candidate = os.path.join(input_dir, f"{email_id}{suffix}")
            if os.path.exists(candidate):
                attachment_path = candidate
                break
                
        # Process through the indexing pipeline
        result = engine.process_inbound(email_id, body_text, attachment_path)
        results.append(result)
        
        total_tasks = result.get("total_tasks", 0)
        print(f"  [{email_id[:12]}] {result['type']} — {total_tasks} task(s)")
        
    # Print summary
    from indexer.workqueue import WorkQueueManager
    wq = WorkQueueManager(config=config)
    stats = wq.get_stats()
    
    print(f"\n=== Batch Complete: {len(body_files)} emails processed ===")
    print(f"Work Queue Summary:")
    for queue_name, counts in stats.items():
        print(f"  {queue_name}: {counts['total']} tasks ({counts['pending']} pending, {counts['review']} needs review)")
        
    return results


def mailbox_watcher(host: str, email: str, password: str, 
                    folder: str = "INBOX", poll_interval: int = 30,
                    engine=None, config=None):
    """
    Watcher Mode: Connect to an IMAP mailbox, poll for new emails, 
    and process them as they arrive.
    
    NOTE: This is the interface/stub. In production you would use 
    imaplib or exchangelib. For the demo, we simulate the polling loop
    with a local directory.
    """
    print(f"Mailbox Watcher: Connecting to {host} ({email})...")
    print(f"  Polling folder: {folder}")
    print(f"  Poll interval: {poll_interval}s")
    print(f"  Press Ctrl+C to stop.\n")
    
    if engine is None:
        from indexer.rules.engine import RuleEngine
        engine = RuleEngine(config=config)
    
    # In a real implementation, this would be:
    #   import imaplib
    #   mail = imaplib.IMAP4_SSL(host)
    #   mail.login(email, password)
    #   mail.select(folder)
    #
    # For the demo, we simulate by watching a local directory.
    # Honor a module-level override (tests set indexer.ingest.watch_dir).
    from indexer.config import load_config
    effective = load_config()
    watch_dir = globals().get("watch_dir") or effective.inbox_dir
    os.makedirs(watch_dir, exist_ok=True)
    processed = set()
    
    try:
        while True:
            body_files = glob.glob(os.path.join(watch_dir, "*_body.txt"))
            new_files = [f for f in body_files if f not in processed]
            
            if new_files:
                for body_path in new_files:
                    basename = os.path.basename(body_path)
                    email_id = basename.replace("_body.txt", "")
                    
                    with open(body_path, "r") as f:
                        body_text = f.read()
                        
                    attachment_path = None
                    for suffix in ["_attachment.pdf", "_bulk_attachment.pdf"]:
                        candidate = os.path.join(watch_dir, f"{email_id}{suffix}")
                        if os.path.exists(candidate):
                            attachment_path = candidate
                            break
                    
                    ts = datetime.datetime.now().strftime("%H:%M:%S")
                    print(f"[{ts}] New email: {email_id[:12]}...")
                    
                    result = engine.process_inbound(email_id, body_text, attachment_path)
                    total_tasks = result.get("total_tasks", 0)
                    print(f"  → {result['type']} — {total_tasks} task(s) routed")
                    
                    processed.add(body_path)
                    
            time.sleep(poll_interval)
            
    except KeyboardInterrupt:
        print("\nWatcher stopped.")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Batch mode:   python -m indexer.ingest batch <directory>")
        print("  Watcher mode: python -m indexer.ingest watch")
        sys.exit(1)
        
    mode = sys.argv[1]
    
    if mode == "batch":
        input_dir = sys.argv[2] if len(sys.argv) > 2 else "data/corpus"
        batch_ingest(input_dir)
    elif mode == "watch":
        import os as _os
        _cred = _os.environ.get("IMAP_PASSWORD", "")
        mailbox_watcher(
            _os.environ.get("IMAP_HOST", "imap.example.com"),
            _os.environ.get("IMAP_USER", "indexer@example.com"),
            _cred,
        )
    else:
        print(f"Unknown mode: {mode}")
