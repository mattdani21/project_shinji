# Tessera AI Indexer

Tessera AI Indexer is a sophisticated document indexing and workflow automation platform. It is designed to intelligently route inbound communications (emails with PDF attachments) to the appropriate business queues (e.g., Repurchase, Maintenance, Claims, New Business).

The system employs a multi-tiered classification architecture, starting with deterministic heuristics (QR codes) and falling back to a highly accurate, locally run deep learning model (XLM-RoBERTa exported to ONNX). This ensures **100% data sovereignty and privacy** as no data leaves the local environment for inference.

## Architecture

The indexing pipeline is managed by a **Rule Engine** (`indexer/rules/engine.py`) that processes documents through four cascading tiers:

1.  **Tier 1: Deterministic Metadata Extraction (QR Codes)**
    Scans PDF attachments for QR codes. If a valid, complete form is found, it routes instantly with 100% confidence. Also detects "Broker Bulk" submissions containing multiple forms.
2.  **Tier 2: OCR & Template Matching** *(Stubbed)*
    Designed for standard forms lacking QR codes but having known visual structures.
3.  **Tier 3: Named Entity Recognition (NER) & Taxonomy** *(Stubbed)*
    Looks for specific keywords, policy numbers, or ID numbers in unstructured text.
4.  **Tier 4: Deep Learning Classification (XLM-RoBERTa)**
    The final safety net for entirely unstructured, messy, or ambiguous emails. Uses a fine-tuned XLM-RoBERTa model running locally via ONNX to classify the intent of the email body. It includes a TF-IDF fallback if the ONNX model is unavailable.

## Features

-   **Multi-Tier Routing:** Fast, deterministic routing when possible; intelligent ML inference when necessary.
-   **Local ONNX Inference:** The Tier 4 model runs locally on CPU/GPU without external API calls, ensuring data privacy and low latency.
-   **Human-In-The-Loop (HITL):** Documents that fall below a configured confidence threshold are routed to a human review queue.
-   **Adversarial Robustness:** Tested against messy, ambiguous, and non-English (e.g., Afrikaans) inputs.
-   **Synthetic Data Generation:** Includes a robust pipeline to generate diverse, realistic synthetic corporate communication data for training.

## Installation

1.  Clone the repository.
2.  Ensure you have Python 3.9+ installed.
3.  Install dependencies:
    ```bash
    pip install pandas numpy scikit-learn reportlab qrcode onnxruntime transformers torch pyarrow
    ```

## Usage

### Running the Demo

The main demo processes a mix of clean and messy samples to showcase the routing logic (Auto-Routing vs. HITL).

```bash
python3 main_demo.py
```
This will output the routing decisions, confidence scores, and populate the `data/workqueues/` and `data/human_review/` directories.

### Generating Synthetic Data

If you want to generate a new corpus from scratch:

```bash
# Generates 10,000 samples across 6 classes + bulk instructions
PYTHONPATH=. python3 generator/scale_corpus.py
```

### Preparing Training Data

After generating a corpus, prepare the train/val/test splits for model training:

```bash
PYTHONPATH=. python3 training/prepare_data.py
```
This creates `train.parquet`, `val.parquet`, `test.parquet`, and `label_map.json` in `data/splits/`.

### Training the Model

The deep learning model is designed to be trained on a GPU-enabled environment like Google Colab.
1. See the [Colab Handguide](docs/colab_handguide.md) for step-by-step instructions.
2. The training script is located at `training/colab_notebook.py`.
3. Once trained, place the resulting `tessera-encoder-v1` folder (containing `model.onnx` and `model.onnx.data`) into the `models/` directory.

### Calibrating the Model

To verify the accuracy and confidence calibration of your trained ONNX model against the local test set:

```bash
PYTHONPATH=. python3 training/calibrate.py
```
This outputs an accuracy report and an RFI (Request for Information) threshold analysis to help you tune the HITL routing threshold.

## Project Structure

-   **`generator/`**: Scripts for creating synthetic emails, PDFs, and QR codes.
-   **`indexer/`**: Core logic for the Rule Engine, Classification Tiers, Work Queues, and HITL exporter.
-   **`training/`**: Scripts for data preparation, model training (Colab), and local calibration.
-   **`models/`**: Stores the ONNX model binaries and TF-IDF fallback models (Note: Large binaries are excluded from Git).
-   **`data/`**: Stores generated corpora, training splits, and output queues.
-   **`docs/`**: Documentation, including the Colab Handguide.
-   **`main_demo.py`**: The primary entry point to demonstrate the system end-to-end.
