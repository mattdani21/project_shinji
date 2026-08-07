import os
import joblib
import time
import json
import numpy as np
from typing import Dict, Any, Optional

class Tier4Classifier:
    """Tier 4: Local ML Fallback.
    Supports both:
    1. Fast TF-IDF + Naive Bayes (joblib)
    2. Deep XLM-RoBERTa (ONNX) for higher accuracy
    """
    def __init__(self, 
                 onnx_model_dir: Optional[str] = None,
                 tfidf_model_path: Optional[str] = None,
                 config=None):
        
        from indexer.config import coerce_config
        config = coerce_config(config)
        if config is not None:
            onnx_model_dir = onnx_model_dir or config.onnx_model_dir
            tfidf_model_path = tfidf_model_path or config.tfidf_model_path
        onnx_model_dir = onnx_model_dir or "models/tessera-encoder-v1"
        tfidf_model_path = tfidf_model_path or "models/tier4_model.joblib"
        
        self.onnx_session = None
        self.tokenizer = None
        self.label_map = None
        self.tfidf_model = None
        
        # 1. Try to load ONNX model (Production grade)
        onnx_path = os.path.join(onnx_model_dir, "model.onnx")
        label_map_path = os.path.join(onnx_model_dir, "label_map.json")
        
        self.max_length = 256  # Default; overridden by training_config.json if present
        
        if os.path.exists(onnx_path) and os.path.exists(label_map_path):
            try:
                import onnxruntime as ort
                from transformers import AutoTokenizer
                
                # Load training config for max_length
                config_path = os.path.join(onnx_model_dir, "training_config.json")
                if os.path.exists(config_path):
                    with open(config_path, "r") as f:
                        config = json.load(f)
                        self.max_length = config.get("max_length", 256)
                
                print(f"Loading ONNX model from {onnx_path} (max_length={self.max_length})...")
                self.onnx_session = ort.InferenceSession(onnx_path)
                self.tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
                
                with open(label_map_path, "r") as f:
                    # Invert the map if it's label->id
                    raw_map = json.load(f)
                    if isinstance(list(raw_map.keys())[0], str) and isinstance(list(raw_map.values())[0], int):
                        self.label_map = {v: k for k, v in raw_map.items()}
                    else:
                        self.label_map = {int(k): v for k, v in raw_map.items()}
                
                print("ONNX model loaded successfully.")
            except Exception as e:
                print(f"Failed to load ONNX model: {e}. Falling back to TF-IDF.")
        
        # 2. Load TF-IDF model as baseline/fallback
        if os.path.exists(tfidf_model_path):
            try:
                print(f"Loading TF-IDF fallback from {tfidf_model_path}...")
                self.tfidf_model = joblib.load(tfidf_model_path)
            except Exception as e:
                print(f"Failed to load TF-IDF model: {e}")
        
        if not self.onnx_session and not self.tfidf_model:
            print("WARNING: No Tier 4 models found. Classification will return 'unknown'.")

    def predict(self, text: str) -> dict:
        start = time.time()
        
        # Prefer ONNX
        if self.onnx_session and self.tokenizer and self.label_map:
            try:
                inputs = self.tokenizer(
                    text, 
                    return_tensors="np", 
                    padding="max_length", 
                    truncation=True, 
                    max_length=self.max_length
                )
                
                # ONNX expects input names from the export
                onnx_inputs = {
                    "input_ids": inputs["input_ids"],
                    "attention_mask": inputs["attention_mask"]
                }
                
                logits = self.onnx_session.run(None, onnx_inputs)[0]
                
                # Softmax
                exp_logits = np.exp(logits - np.max(logits))
                probs = exp_logits / exp_logits.sum(axis=-1, keepdims=True)
                
                best_idx = int(np.argmax(probs))
                prediction = self.label_map.get(best_idx, "unknown")
                confidence = float(probs[0][best_idx])
                
                return {
                    "prediction": prediction,
                    "confidence": round(confidence, 4),
                    "latency_ms": (time.time() - start) * 1000,
                    "api_used": "none (local_onnx)"
                }
            except Exception as e:
                print(f"ONNX prediction failed: {e}. Falling back to TF-IDF.")
                # Fall through to TF-IDF

        # Fallback to TF-IDF
        if self.tfidf_model:
            try:
                probs = self.tfidf_model.predict_proba([text])[0]
                classes = self.tfidf_model.classes_
                best_idx = probs.argmax()
                
                return {
                    "prediction": classes[best_idx],
                    "confidence": round(float(probs[best_idx]), 4),
                    "latency_ms": (time.time() - start) * 1000,
                    "api_used": "none (local_tfidf_fallback)"
                }
            except Exception as e:
                print(f"TF-IDF prediction failed: {e}")

        return {
            "prediction": "unknown",
            "confidence": 0.0,
            "latency_ms": (time.time() - start) * 1000,
            "api_used": "none (failed)"
        }
