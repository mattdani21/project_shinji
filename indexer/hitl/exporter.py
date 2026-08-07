import os
import shutil
import json
import pandas as pd
from typing import Optional

class HITLExporter:
    """
    Handles routing of low-confidence predictions to human review.
    """
    def __init__(self, review_dir: Optional[str] = None, config=None):
        from indexer.config import coerce_config
        config = coerce_config(config)
        if config is not None:
            review_dir = review_dir or config.review_dir
        self.review_dir = review_dir or "data/human_review"
        os.makedirs(self.review_dir, exist_ok=True)
        self.manifest_path = os.path.join(self.review_dir, "review_manifest.jsonl")

    def export_for_review(self, email_id: str, body_text: str, prediction: str, confidence: float, reason: str):
        """
        Saves the email and its metadata to the review directory.
        """
        # Save the body for human to read
        body_path = os.path.join(self.review_dir, f"{email_id}.txt")
        with open(body_path, "w") as f:
            f.write(body_text)
            
        # Log to the review manifest
        entry = {
            "email_id": email_id,
            "ai_prediction": prediction,
            "confidence": confidence,
            "reason": reason,
            "body_path": body_path
        }
        
        with open(self.manifest_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
            
        return body_path

def process_pipeline(engine, exporter, body_text, email_id, threshold=0.85):
    """
    Full pipeline logic with HITL routing.
    """
    result = engine.classify_email(body_text)
    
    status = "AUTO_ROUTED"
    if result["confidence"] < threshold:
        status = "SENT_TO_HUMAN"
        exporter.export_for_review(
            email_id=email_id,
            body_text=body_text,
            prediction=result["prediction"],
            confidence=result["confidence"],
            reason=f"Low confidence ({result['confidence']:.2%})"
        )
    elif result["prediction"] == "unknown":
        status = "SENT_TO_HUMAN"
        exporter.export_for_review(
            email_id=email_id,
            body_text=body_text,
            prediction="unknown",
            confidence=0.0,
            reason="Unrecognized form type"
        )
        
    return {
        "email_id": email_id,
        "prediction": result["prediction"],
        "confidence": result["confidence"],
        "status": status
    }
