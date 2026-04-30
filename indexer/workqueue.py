"""
Work Queue System for Tessera AI Indexer.

Each work queue corresponds to a team (Maintenance, New Business, Claims, etc.).
Items in the queue are structured tasks extracted from emails and their attachments.

Future: AI Agent Processors will pull from these queues and process automatically.
"""
import os
import json
import re
import datetime
from typing import List, Dict, Any, Optional

class WorkQueueItem:
    """A single task routed to a team queue."""
    def __init__(self, 
                 email_id: str,
                 task_id: str,
                 policy_number: str,
                 client_name: str,
                 main_type: str,
                 sub_type: str,
                 pages: str,
                 confidence: float,
                 source_attachment: str = "",
                 extracted_fields: Dict[str, Any] = None):
        self.email_id = email_id
        self.task_id = task_id
        self.policy_number = policy_number
        self.client_name = client_name
        self.main_type = main_type
        self.sub_type = sub_type
        self.pages = pages
        self.confidence = confidence
        self.source_attachment = source_attachment
        self.extracted_fields = extracted_fields or {}
        self.status = "pending"          # pending | in_progress | complete | review
        self.assigned_to = None          # Future: agent or human assignee
        self.created_at = datetime.datetime.now().isoformat()
        self.completed_at = None
        
    def to_dict(self) -> dict:
        return {
            "email_id": self.email_id,
            "task_id": self.task_id,
            "policy_number": self.policy_number,
            "client_name": self.client_name,
            "main_type": self.main_type,
            "sub_type": self.sub_type,
            "pages": self.pages,
            "confidence": self.confidence,
            "source_attachment": self.source_attachment,
            "extracted_fields": self.extracted_fields,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }

# Mapping from sub_type to the team queue (main_type)
SUB_TYPE_TO_QUEUE = {
    "repurchase": "policy_admin",
    "maintenance_client": "policy_admin",
    "maintenance_contrib": "policy_admin",
    "new_business": "new_business",
    "claim_death": "claims",
    "claim_retirement": "claims",
    "bulk_instructions": "broker_comms"
}

class WorkQueueManager:
    """
    Manages all team work queues. Persists to disk as JSONL files.
    Each queue is a separate file: workqueues/{main_type}.jsonl
    """
    def __init__(self, queue_dir: str = "data/workqueues"):
        self.queue_dir = queue_dir
        os.makedirs(self.queue_dir, exist_ok=True)
        
    def route(self, item: WorkQueueItem):
        """Route a work queue item to the correct team queue."""
        queue_name = SUB_TYPE_TO_QUEUE.get(item.sub_type, "unknown")
        item.main_type = queue_name
        
        # If confidence is below threshold, mark for human review
        if item.confidence < 0.85:
            item.status = "review"
            
        queue_path = os.path.join(self.queue_dir, f"{queue_name}.jsonl")
        with open(queue_path, "a") as f:
            f.write(json.dumps(item.to_dict()) + "\n")
            
        return queue_name
        
    def get_queue(self, queue_name: str) -> List[dict]:
        """Read all items from a specific team queue."""
        queue_path = os.path.join(self.queue_dir, f"{queue_name}.jsonl")
        if not os.path.exists(queue_path):
            return []
        items = []
        with open(queue_path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        return items
        
    def get_stats(self) -> Dict[str, Any]:
        """Get counts per queue and per status."""
        stats = {}
        for fname in os.listdir(self.queue_dir):
            if fname.endswith(".jsonl"):
                queue_name = fname.replace(".jsonl", "")
                items = self.get_queue(queue_name)
                stats[queue_name] = {
                    "total": len(items),
                    "pending": sum(1 for i in items if i["status"] == "pending"),
                    "review": sum(1 for i in items if i["status"] == "review"),
                    "complete": sum(1 for i in items if i["status"] == "complete"),
                }
        return stats


def extract_policy_number(text: str) -> str:
    """Extract a policy number from text using regex (Tier 2 logic)."""
    match = re.search(r'POL-\d{8}', text)
    if match:
        return match.group(0)
    # Try broader patterns
    match = re.search(r'[Pp]olicy\s*(?:[Nn]o\.?\s*)?(\S+)', text)
    if match:
        return match.group(1)
    return "UNKNOWN"


def extract_client_name(text: str) -> str:
    """Attempt to extract a client name from text."""
    # Look for "Client Name: X" or "Name: X" patterns
    match = re.search(r'(?:Client Name|Name|Investor|Member)\s*:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "Unknown Client"
