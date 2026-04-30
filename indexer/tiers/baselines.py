import random
import os
import requests

class DummyBaseline:
    """Always returns the ground truth class (for testing harness logic)."""
    def predict(self, email_body: str, ground_truth_type: str) -> dict:
        return {
            "prediction": ground_truth_type,
            "confidence": 1.0,
            "latency_ms": 1.0,
            "api_used": "none"
        }

class RandomBaseline:
    """Randomly guesses the class from the 6 possible schemas."""
    def __init__(self):
        self.classes = [
            "repurchase", "new_business", "maintenance_client", 
            "maintenance_contrib", "claim_death", "claim_retirement"
        ]
        
    def predict(self, email_body: str) -> dict:
        import time
        start = time.time()
        pred = random.choice(self.classes)
        return {
            "prediction": pred,
            "confidence": round(random.uniform(0.1, 1.0), 2),
            "latency_ms": (time.time() - start) * 1000,
            "api_used": "none"
        }

class GeminiCeiling:
    """Uses Gemini zero-shot to establish the max accuracy ceiling."""
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY", "AIzaSyB-t0nFrV4ITCzjA1D7W46jfp0XVgcgtZE")
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={self.api_key}"
        self.classes = [
            "repurchase", "new_business", "maintenance_client", 
            "maintenance_contrib", "claim_death", "claim_retirement"
        ]
        self._call_count = 0
        
    def predict(self, email_body: str) -> dict:
        import time
        
        self._call_count += 1
        if self._call_count > 1:
            time.sleep(2.0)
        
        start = time.time()
        prompt = f"""Classify the following insurance email into exactly one of these classes:
{', '.join(self.classes)}

Email text:
{email_body}

Respond with ONLY the class name and nothing else."""
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0}
        }
        
        for attempt in range(3):
            try:
                res = requests.post(self.url, headers={"Content-Type": "application/json"}, json=payload, timeout=30)
                if res.status_code == 429:
                    time.sleep((2 ** attempt) * 2)
                    continue
                res.raise_for_status()
                text = res.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                pred = "unknown"
                for c in self.classes:
                    if c.lower() in text.lower():
                        pred = c
                        break
                return {
                    "prediction": pred,
                    "confidence": 0.99,
                    "latency_ms": (time.time() - start) * 1000,
                    "api_used": "gemini-flash-latest"
                }
            except Exception as e:
                if attempt < 2:
                    time.sleep((2 ** attempt) * 2)
                    continue
        
        return {
            "prediction": "error",
            "confidence": 0.0,
            "latency_ms": (time.time() - start) * 1000,
            "api_used": "error"
        }

