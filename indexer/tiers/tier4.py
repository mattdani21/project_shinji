import os
import joblib
import time

class Tier4Classifier:
    """
    Tier 4: Local ML Fallback.
    Uses a pre-trained TF-IDF + Naive Bayes pipeline for fast, private classification.
    """
    def __init__(self, model_path: str = "models/tier4_model.joblib"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Please run train.py first.")
        self.model = joblib.load(model_path)
        
    def predict(self, email_body: str) -> dict:
        start = time.time()
        
        # Get probabilities
        probs = self.model.predict_proba([email_body])[0]
        classes = self.model.classes_
        
        # Find best prediction
        best_idx = probs.argmax()
        prediction = classes[best_idx]
        confidence = probs[best_idx]
        
        return {
            "prediction": prediction,
            "confidence": round(float(confidence), 4),
            "latency_ms": (time.time() - start) * 1000,
            "api_used": "none (local_ml)"
        }
