import pandas as pd
import os
import pypdf
import json
from sklearn.model_selection import train_test_split
from typing import List, Dict, Any

def extract_text_from_pdf(pdf_path: str, max_chars: int = 3000) -> str:
    if not pdf_path or not os.path.exists(pdf_path):
        return ""
    try:
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
            if len(text) > max_chars:
                break
        return text[:max_chars]
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def prepare_training_data(manifest_path: str, output_dir: str = "data/splits"):
    print(f"Preparing training data from {manifest_path}...")
    df = pd.read_parquet(manifest_path)
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Extract text and combine
    print("Extracting PDF text and combining with email bodies...")
    processed_data = []
    
    for i, row in df.iterrows():
        if i % 500 == 0:
            print(f"  Processed {i}/{len(df)}...")
            
        with open(row["body_path"], "r") as f:
            body_text = f.read()
            
        pdf_text = extract_text_from_pdf(row["pdf_path"])
        
        # Combine: Subject line (if we had it) + Body + PDF
        # We'll simulate a subject line from the sub_type for diversity
        combined_text = f"Body:\n{body_text}\n\nAttachment Text:\n{pdf_text}"
        
        processed_data.append({
            "email_id": row["email_id"],
            "investor_id": row["investor_id"],
            "input_text": combined_text,
            "label": row["sub_type"]
        })
        
    pdf_df = pd.DataFrame(processed_data)
    
    # Filter out bulk_instructions — these are routed by Tier 1 (broker detection),
    # not classified by Tier 4 ML. Including them would create a phantom class.
    before_filter = len(pdf_df)
    pdf_df = pdf_df[pdf_df["label"] != "bulk_instructions"]
    print(f"  Filtered out {before_filter - len(pdf_df)} bulk_instructions samples")
    print(f"  Remaining: {len(pdf_df)} samples")
    
    # 2. Split by investor_id to prevent data leakage
    print("Splitting by investor_id...")
    unique_investors = pdf_df["investor_id"].unique()
    
    # Exclude 'BROKER' from the random split pool if it has too many samples, 
    # or handle it separately. Actually, let's just split everything.
    train_investors, temp_investors = train_test_split(unique_investors, test_size=0.3, random_state=42)
    val_investors, test_investors = train_test_split(temp_investors, test_size=0.5, random_state=42)
    
    train_df = pdf_df[pdf_df["investor_id"].isin(train_investors)]
    val_df = pdf_df[pdf_df["investor_id"].isin(val_investors)]
    test_df = pdf_df[pdf_df["investor_id"].isin(test_investors)]
    
    print(f"Split Summary:")
    print(f"  Train: {len(train_df)} samples ({len(train_investors)} investors)")
    print(f"  Val:   {len(val_df)} samples ({len(val_investors)} investors)")
    print(f"  Test:  {len(test_df)} samples ({len(test_investors)} investors)")
    
    # 3. Save parquets
    train_df.to_parquet(os.path.join(output_dir, "train.parquet"), index=False)
    val_df.to_parquet(os.path.join(output_dir, "val.parquet"), index=False)
    test_df.to_parquet(os.path.join(output_dir, "test.parquet"), index=False)
    
    # Save label mapping
    labels = sorted(pdf_df["label"].unique())
    label_map = {label: i for i, label in enumerate(labels)}
    with open(os.path.join(output_dir, "label_map.json"), "w") as f:
        json.dump(label_map, f, indent=2)
        
    print(f"Data preparation complete. Splits saved to {output_dir}/")

if __name__ == "__main__":
    manifest = "data/corpus_10k/manifest_10k.parquet"
    if os.path.exists(manifest):
        prepare_training_data(manifest)
    else:
        print(f"Manifest not found at {manifest}")
