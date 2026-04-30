"""
Google Colab Training Script for Tessera AI Indexer (XLM-RoBERTa)
Optimized for minimum compute unit consumption on Colab Pay-As-You-Go.

COST ESTIMATE: ~8-12 compute units (~$1.00-$1.20)
  - T4 GPU burns ~1.7 CU/hour
  - Total runtime: ~25-40 min (tokenize + train + export)
  - Budget ceiling: buy 100 CU for $9.99, you'll use <15

INSTRUCTIONS:
  See the Colab Handguide in docs/ for step-by-step.
"""

# ============================================================
# CELL 1: Install Dependencies (run this cell first, alone)
# ============================================================
# !pip install -q transformers[torch] datasets accelerate scikit-learn pandas pyarrow onnxruntime onnx seaborn

# ============================================================
# CELL 2: Upload & Train (run after Cell 1 finishes)
# ============================================================
import os
import json
import torch
import pandas as pd
import numpy as np
from datasets import Dataset, DatasetDict
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import onnxruntime as ort
import matplotlib.pyplot as plt
import seaborn as sns

def train_tessera_model():
    print("=" * 60)
    print("  TESSERA AI INDEXER — XLM-RoBERTa Fine-Tuning")
    print("=" * 60)

    MODEL_NAME = "xlm-roberta-base"
    OUTPUT_DIR = "./tessera-encoder-v1"
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # ── 1. Load Data ──────────────────────────────────────────
    print("\n[1/7] Loading datasets...")
    train_df = pd.read_parquet("train.parquet")
    val_df = pd.read_parquet("val.parquet")
    test_df = pd.read_parquet("test.parquet")

    with open("label_map.json", "r") as f:
        label_map = json.load(f)

    # IMPORTANT: Remove classes with zero training samples
    # (bulk_instructions is routed by Tier 1, not classified by Tier 4)
    labels_in_data = set(train_df["label"].unique())
    label_map = {k: v for k, v in label_map.items() if k in labels_in_data}

    # Re-index to 0..N-1 (contiguous)
    sorted_labels = sorted(label_map.keys())
    label_map = {label: i for i, label in enumerate(sorted_labels)}
    reverse_label_map = {v: k for k, v in label_map.items()}
    num_labels = len(label_map)

    print(f"  Classes ({num_labels}): {sorted_labels}")
    print(f"  Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

    def convert_to_ds(df):
        df = df.copy()
        df["label"] = df["label"].map(label_map)
        # Drop any rows where label is NaN (class not in label_map)
        df = df.dropna(subset=["label"])
        df["label"] = df["label"].astype(int)
        return Dataset.from_pandas(df, preserve_index=False)

    ds = DatasetDict({
        "train": convert_to_ds(train_df),
        "validation": convert_to_ds(val_df),
        "test": convert_to_ds(test_df)
    })

    # ── 2. Tokenize ───────────────────────────────────────────
    print("\n[2/7] Tokenizing...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    def tokenize_function(examples):
        return tokenizer(
            examples["input_text"],
            padding="max_length",
            truncation=True,
            max_length=256  # Reduced from 512 — our avg text is ~1000 chars (~200 tokens). Saves 50% memory + time.
        )

    tokenized_ds = ds.map(tokenize_function, batched=True)

    # ── 3. Model Setup ────────────────────────────────────────
    print("\n[3/7] Loading model...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"  Device: {device}")
    if device == "cpu":
        print("  ⚠️  WARNING: No GPU detected. Training will be very slow.")
        print("  Go to Runtime → Change runtime type → T4 GPU")

    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=num_labels
    ).to(device)

    # Freeze embeddings + first 10 of 12 encoder layers (transfer learning)
    # Only layers 10, 11, and the classifier head are trainable
    for param in model.roberta.embeddings.parameters():
        param.requires_grad = False
    for i in range(10):
        for param in model.roberta.encoder.layer[i].parameters():
            param.requires_grad = False

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(f"  Trainable: {trainable:,} / {total:,} params ({trainable/total:.1%})")

    # ── 4. Training ───────────────────────────────────────────
    print("\n[4/7] Configuring training...")

    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=32,  # Larger batch = fewer steps = faster
        per_device_eval_batch_size=64,
        num_train_epochs=5,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        logging_steps=50,
        save_total_limit=2,  # Only keep best + latest checkpoint (save disk)
        fp16=True if device == "cuda" else False,  # Mixed precision = 2x speed on T4
        dataloader_num_workers=2,
        report_to="none"
    )

    def compute_metrics(eval_pred):
        logits, labels = eval_pred
        predictions = np.argmax(logits, axis=-1)
        return {"accuracy": accuracy_score(labels, predictions)}

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_ds["train"],
        eval_dataset=tokenized_ds["validation"],
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)]
    )

    # ── 5. Train ──────────────────────────────────────────────
    print("\n[5/7] Training (this takes ~15-25 min on T4)...")
    trainer.train()

    # ── 6. Evaluate ───────────────────────────────────────────
    print("\n[6/7] Evaluating on test set...")
    results = trainer.evaluate(tokenized_ds["test"])
    print(f"  Test Accuracy: {results['eval_accuracy']:.2%}")

    preds = trainer.predict(tokenized_ds["test"])
    pred_labels = np.argmax(preds.predictions, axis=-1)
    true_labels = tokenized_ds["test"]["label"]

    print("\nClassification Report:")
    report = classification_report(
        true_labels, pred_labels,
        target_names=sorted_labels
    )
    print(report)

    # Confusion Matrix
    cm = confusion_matrix(true_labels, pred_labels)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=sorted_labels,
                yticklabels=sorted_labels)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title(f'Tessera AI Indexer — Test Accuracy: {results["eval_accuracy"]:.1%}')
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "confusion_matrix.png"), dpi=150)
    plt.show()

    # ── 7. Export to ONNX ─────────────────────────────────────
    print("\n[7/7] Exporting to ONNX...")
    model.eval()
    dummy_input = tokenizer(
        "dummy text for export",
        return_tensors="pt",
        padding="max_length",
        max_length=256  # Must match training max_length
    ).to(device)

    onnx_path = os.path.join(OUTPUT_DIR, "model.onnx")
    torch.onnx.export(
        model,
        (dummy_input["input_ids"], dummy_input["attention_mask"]),
        onnx_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["logits"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence"},
            "attention_mask": {0: "batch_size", 1: "sequence"},
            "logits": {0: "batch_size"}
        },
        opset_version=14
    )

    # Save the CORRECTED label map (without bulk_instructions)
    with open(os.path.join(OUTPUT_DIR, "label_map.json"), "w") as f:
        json.dump(label_map, f, indent=2)

    # Save config for reference
    config = {
        "model_name": MODEL_NAME,
        "max_length": 256,
        "num_labels": num_labels,
        "labels": sorted_labels,
        "test_accuracy": results['eval_accuracy'],
        "frozen_layers": 10
    }
    with open(os.path.join(OUTPUT_DIR, "training_config.json"), "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n{'=' * 60}")
    print(f"  DONE! Model exported to {OUTPUT_DIR}/")
    print(f"  Files to download:")
    print(f"    - model.onnx")
    print(f"    - label_map.json")
    print(f"    - training_config.json")
    print(f"    - confusion_matrix.png")
    print(f"{'=' * 60}")
    print(f"\n  Next: Download the {OUTPUT_DIR}/ folder and place it")
    print(f"  into your local models/ directory.")

if __name__ == "__main__":
    train_tessera_model()
