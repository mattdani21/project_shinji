# Tessera AI Indexer — Google Colab Training Handguide

> **Budget: ~$1.00–$1.50 | Time: ~30 minutes**

---

## Cost Breakdown

| Item | Compute Units | Cost |
|---|---|---|
| T4 GPU @ ~1.7 CU/hour | ~1.4 CU (for ~50 min total runtime) | ~$0.14 |
| Pip install overhead | ~0.2 CU | ~$0.02 |
| Tokenization (CPU-bound) | ~0.3 CU | ~$0.03 |
| Training (5 epochs, ~6.7k samples) | ~5–7 CU | ~$0.50–$0.70 |
| Eval + ONNX export | ~1 CU | ~$0.10 |
| **Total** | **~8–10 CU** | **~$0.80–$1.00** |

> [!TIP]
> Buy the **100 CU pack ($9.99)** via Pay-As-You-Go. You'll use ~10 CU, leaving 90 for future runs. CUs expire after 90 days.

### Cost Optimizations Already Applied
- **max_length = 256** (not 512) — our texts average ~200 tokens. Halves memory and training time.
- **fp16 mixed precision** — 2× speed on T4 GPU.
- **Batch size 32** (train) / 64 (eval) — fewer gradient steps.
- **Freeze 10/12 layers** — only fine-tune last 2 + classifier head. Tiny trainable footprint.
- **Early stopping** — if validation loss stops improving for 2 epochs, training stops automatically.
- **save_total_limit=2** — only keeps 2 checkpoints, saves disk space.

---

## Step-by-Step Guide

### Step 0: Buy Compute Units

1. Go to [colab.research.google.com](https://colab.research.google.com)
2. Click your profile icon (top right) → **Colab settings** or **Manage subscription**
3. Under **Pay-As-You-Go**, buy **100 compute units ($9.99)**
4. You do NOT need Colab Pro — Pay-As-You-Go is sufficient

### Step 1: Create a New Notebook

1. Click **File → New Notebook**
2. Go to **Runtime → Change runtime type**
3. Set **Hardware accelerator** to **T4 GPU**
4. Click **Save**

> [!WARNING]
> Do NOT select A100 or L4 — they burn CUs 3-5× faster. T4 is more than enough for this workload.

### Step 2: Upload Your Files

In the left sidebar, click the **📁 Files** icon, then click the **Upload** button (⬆️).

Upload these 4 files from your local `data/splits/` directory:

```
data/splits/train.parquet    (1.0 MB)
data/splits/val.parquet      (284 KB)
data/splits/test.parquet     (228 KB)
data/splits/label_map.json   (4 KB)
```

Wait for all 4 uploads to complete. They'll appear in the root `/content/` directory.

### Step 3: Install Dependencies (Cell 1)

Create a new code cell and paste:

```python
!pip install -q transformers[torch] datasets accelerate scikit-learn pandas pyarrow onnxruntime onnx seaborn
```

Run this cell. Wait ~2 minutes for installation.

> [!TIP]
> The `-q` flag suppresses verbose output. If you see errors, remove `-q` to debug.

### Step 4: Run Training (Cell 2)

Create a **new code cell** below Cell 1. Open the file:

```
training/colab_notebook.py
```

Copy the **entire contents** of that file and paste it into Cell 2.

Add this at the very bottom of the cell:

```python
train_tessera_model()
```

Run the cell. You'll see progress like:

```
============================================================
  TESSERA AI INDEXER — XLM-RoBERTa Fine-Tuning
============================================================

[1/7] Loading datasets...
  Classes (6): ['claim_death', 'claim_retirement', ...]
  Train: 6677 | Val: 1894 | Test: 1429

[2/7] Tokenizing...
[3/7] Loading model...
  Device: cuda
  Trainable: 14,549,766 / 278,049,286 params (5.2%)

[4/7] Configuring training...
[5/7] Training (this takes ~15-25 min on T4)...
```

### Step 5: Wait for Training

Training runs ~15–25 minutes. You'll see epoch-by-epoch progress:

```
Epoch 1/5: loss=0.82, eval_accuracy=0.91
Epoch 2/5: loss=0.34, eval_accuracy=0.95
Epoch 3/5: loss=0.18, eval_accuracy=0.97
...
```

> [!IMPORTANT]
> **Do NOT close the browser tab.** Colab will disconnect if you navigate away. Keep the tab active.

If early stopping kicks in (eval loss stops improving), it may finish in 3-4 epochs instead of 5.

### Step 6: Review Results

After training, you'll see:

1. **Test Accuracy** — should be ~95%+ with this data
2. **Classification Report** — per-class precision/recall/F1
3. **Confusion Matrix** — visual heatmap (displayed inline)

Screenshot the confusion matrix — it's useful for the investor pitch.

### Step 7: Download Model Artifacts

After training completes, the output folder `tessera-encoder-v1/` will contain:

```
tessera-encoder-v1/
├── model.onnx              (~1.1 GB — the production model)
├── label_map.json           (class-to-index mapping)
├── training_config.json     (hyperparameters for reproducibility)
└── confusion_matrix.png     (for the pitch deck)
```

**To download:**

1. In the left sidebar, click **📁 Files**
2. Navigate to `tessera-encoder-v1/`
3. Right-click each file → **Download**

Or use this code cell to zip everything:

```python
!zip -r /content/tessera-encoder-v1.zip /content/tessera-encoder-v1/
from google.colab import files
files.download('/content/tessera-encoder-v1.zip')
```

### Step 8: Place Model Locally

Unzip the download and copy the folder into your project:

```bash
# From your Downloads folder:
unzip tessera-encoder-v1.zip
cp -r tessera-encoder-v1/ ~/Codebase/project_shinji/models/tessera-encoder-v1/
```

Your models directory should look like:

```
models/
├── tier4_model.joblib              (existing TF-IDF fallback)
└── tessera-encoder-v1/
    ├── model.onnx
    ├── label_map.json
    └── training_config.json
```

### Step 9: Verify Locally

```bash
cd ~/Codebase/project_shinji
PYTHONPATH=. python3 training/calibrate.py
```

This runs the ONNX model against the test set and prints calibration stats.

### Step 10: Disconnect Colab

**Immediately after downloading**, go to **Runtime → Disconnect and delete runtime**.

This stops CU consumption. Don't leave the runtime idle.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "No GPU available" | Runtime → Change runtime type → T4 GPU. If still no GPU, you may need to buy more CUs. |
| "Out of memory" | Reduce `per_device_train_batch_size` from 32 to 16 in the script. |
| Training is very slow | Confirm you're on T4 (not CPU). Check with `!nvidia-smi`. |
| Upload fails | Try dragging files directly into the Files panel. |
| ONNX export fails | Make sure `onnx` package is installed (Cell 1). |
| "CUDA out of memory" | Restart runtime, reduce batch size to 16. |

---

## After Colab: What Happens Automatically

Once the model is in `models/tessera-encoder-v1/`:
- `tier4.py` will **automatically detect** the ONNX model and use it
- The TF-IDF model remains as a fallback if ONNX fails
- `main_demo.py` will use the ONNX model for classification
- Run `PYTHONPATH=. python3 training/calibrate.py` to see production accuracy
