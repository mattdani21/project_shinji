import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

def train_tier4(manifest_path: str = "data/manifest.parquet", model_dir: str = "models"):
    print("Loading data for Tier 4 training...")
    df = pd.read_parquet(manifest_path)
    
    texts = []
    labels = []
    
    for idx, row in df.iterrows():
        with open(row["body_path"], "r") as f:
            texts.append(f.read())
        labels.append(row["sub_type"])
        
    print(f"  Total samples: {len(texts)}")
    
    # Split for validation
    X_train, X_test, y_train, y_test = train_test_split(texts, labels, test_size=0.2, random_state=42)
    
    print("Training Pipeline (TF-IDF + Naive Bayes)...")
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(stop_words='english', ngram_range=(1, 2))),
        ('clf', MultinomialNB(alpha=0.1))
    ])
    
    pipeline.fit(X_train, y_train)
    
    # Evaluate
    y_pred = pipeline.predict(X_test)
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))
    
    # Save
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "tier4_model.joblib")
    joblib.dump(pipeline, model_path)
    print(f"\nModel saved to {model_path}")

if __name__ == "__main__":
    train_tier4()
