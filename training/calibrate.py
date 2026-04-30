import os
import pandas as pd
import numpy as np
import json
from indexer.tiers.tier4 import Tier4Classifier
from sklearn.metrics import accuracy_score

def calibrate_model(test_data_path: str = "data/splits/test.parquet"):
    """
    Evaluates the trained model (ONNX or TF-IDF) and checks if confidence 
    scores are well-calibrated.
    """
    if not os.path.exists(test_data_path):
        print(f"Test data not found at {test_data_path}. Please run prepare_data.py first.")
        return

    print(f"Loading test data from {test_data_path}...")
    df = pd.read_parquet(test_data_path)
    
    print("Initializing Tier 4 Classifier...")
    classifier = Tier4Classifier()
    
    results = []
    print(f"Evaluating {len(df)} samples...")
    for i, row in df.iterrows():
        if i % 100 == 0:
            print(f"  Processed {i}/{len(df)}...")
        
        pred = classifier.predict(row["input_text"])
        results.append({
            "true_label": row["label"],
            "pred_label": pred["prediction"],
            "confidence": pred["confidence"]
        })
    
    res_df = pd.DataFrame(results)
    res_df["is_correct"] = res_df["true_label"] == res_df["pred_label"]
    
    print("\n=== Calibration Report ===")
    overall_acc = accuracy_score(res_df["true_label"], res_df["pred_label"])
    print(f"Overall Accuracy: {overall_acc:.2%}")
    
    # Check calibration by bins
    bins = [0.0, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0]
    res_df["conf_bin"] = pd.cut(res_df["confidence"], bins)
    
    calibration = res_df.groupby("conf_bin", observed=True).agg({
        "is_correct": ["count", "mean"],
        "confidence": "mean"
    })
    
    calibration.columns = ["count", "actual_accuracy", "avg_confidence"]
    print("\nConfidence Calibration Table:")
    print(calibration)
    
    # RFI Threshold analysis
    print("\n=== RFI Threshold Analysis ===")
    for threshold in [0.7, 0.8, 0.9, 0.95]:
        auto_route = res_df[res_df["confidence"] >= threshold]
        review = res_df[res_df["confidence"] < threshold]
        
        auto_acc = auto_route["is_correct"].mean() if not auto_route.empty else 0
        print(f"At {threshold:.0%} threshold:")
        print(f"  Auto-route rate: {len(auto_route)/len(res_df):.1%}")
        print(f"  Auto-route accuracy: {auto_acc:.2%}")
        print(f"  Review rate (HITL): {len(review)/len(res_df):.1%}")
        print("-" * 30)

if __name__ == "__main__":
    calibrate_model()
