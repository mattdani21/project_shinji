# Tessera AI Indexer

Tessera AI Indexer is a sophisticated document indexing and workflow automation platform. It is designed to intelligently route inbound communications (emails with PDF attachments) to the appropriate business queues (e.g., Repurchase, Maintenance, Claims, New Business).

The system employs a multi-tiered classification architecture, starting with deterministic heuristics (QR codes) and falling back to a highly accurate, locally run deep learning model (XLM-RoBERTa exported to ONNX). This ensures **100% data sovereignty and privacy** as no data leaves the local environment for inference.

## Architecture

The indexing pipeline is managed by a **Rule Engine** (`indexer/rules/engine.py`) that processes documents through four cascading tiers:

1.  **Tier 1: Deterministic Metadata Extraction (QR Codes)**
    Scans PDF attachments for QR codes. If a valid, complete form is found, it routes instantly with 100% confidence. Also detects "Broker Bulk" submissions containing multiple forms.
2.  **Tier 2: OCR & Template Matching**
    Routes legacy forms without QR codes by matching their printed structure
    (form-ref codes, header titles, section markers, field labels) against a
    template registry — deterministic, explainable confidence, with
    completeness semantics (unsigned forms go to human review with an RFI
    note). Scanned PDFs are handled by an optional pytesseract OCR hook.
3.  **Tier 3: Named Entity Recognition (NER) & Taxonomy**
    Extracts policy numbers, SA ID numbers, client names and amounts from
    unstructured text, and classifies the form type from weighted keyword
    evidence (the taxonomy), including Afrikaans coverage — a cheap
    deterministic tier that runs before the ML fallback.
4.  **Tier 4: Deep Learning Classification (XLM-RoBERTa)**
    The final safety net for entirely unstructured, messy, or ambiguous emails. Uses a fine-tuned XLM-RoBERTa model running locally via ONNX to classify the intent of the email body. It includes a TF-IDF fallback if the ONNX model is unavailable.

## Features

-   **Multi-Tier Routing:** Fast, deterministic routing when possible; intelligent ML inference when necessary.
-   **Local ONNX Inference:** The Tier 4 model runs locally on CPU/GPU without external API calls, ensuring data privacy and low latency.
-   **Human-In-The-Loop (HITL):** Documents that fall below a configured confidence threshold are routed to a human review queue.
-   **Adversarial Robustness:** Tested against messy, ambiguous, and non-English (e.g., Afrikaans) inputs.
-   **Synthetic Data Generation:** Includes a robust pipeline to generate diverse, realistic synthetic corporate communication data for training.

## Installation

### From the wheel (recommended)

The indexer ships as a standard Python wheel with pinned (compatible-release)
dependencies — no bare `pip install` lists.

```bash
# Core install: Tier 1 (QR routing), Tier 4 TF-IDF fallback, work queues, HITL
pip install tessera-indexer

# Deep-learning Tier 4 (XLM-RoBERTa ONNX inference, fully local)
pip install "tessera-indexer[onnx]"

# Synthetic corpus generation (PDF + QR form generator)
pip install "tessera-indexer[gen]"
```

Build the wheel from source:

```bash
pip install build
python -m build --wheel        # → dist/tessera_indexer-<version>-py3-none-any.whl
```

### Container (on-prem installs)

```bash
docker build -t tessera-indexer .
docker run --rm -v /host/models:/app/models -v /host/inbox:/app/data/inbox \
  tessera-indexer check
```

All inference runs inside the container — no data leaves the host.

### On-prem installs

Follow the [on-prem install checklist](docs/on_prem_install.md) — prerequisites,
model placement, config, one-command verification, and the data-sovereignty
(firewall/egress) checks that make the product sellable to large investors.

### Pilots

The [pilot runbook](pilot/runbook.md) covers running a pilot against a real
inbound queue (IMAP watcher or batch replay), the HITL review loop, and the
measurement report (accuracy, HITL rate, throughput, RFI threshold sweep).
`pilot/simulate.py` + `pilot/metrics.py` validate the machinery on a synthetic
stream before business mail is connected.

### From source (development)

```bash
git clone https://github.com/mattdani21/project_shinji
cd project_shinji
pip install -e ".[dev]"         # editable install + test/build tooling
```

Requires Python 3.9+.

## Usage

### CLI (installed)

```bash
tessera-indexer check          # smoke-test an install: taxonomy, tiers, models
tessera-indexer config         # print the effective configuration
tessera-indexer classify --file email_body.txt   # route one email body (JSON)
tessera-indexer ingest-batch /path/to/inbox      # batch-process a directory
tessera-indexer --version
```

### Configuration

Installs are config-driven. All paths and the HITL threshold live in one YAML
file instead of code:

| Key | Default | Meaning |
|---|---|---|
| `taxonomy_path` | bundled with wheel | taxonomy YAML |
| `schema_dir` | bundled with wheel | form schemas |
| `onnx_model_dir` | `models/tessera-encoder-v1` | deep-learning Tier 4 model |
| `tfidf_model_path` | `models/tier4_model.joblib` | TF-IDF fallback model |
| `queue_dir` | `data/workqueues` | routed work-queue files |
| `review_dir` | `data/human_review` | HITL review exports |
| `inbox_dir` | `data/inbox` | watcher-mode inbox |
| `hitl_threshold` | `0.85` | below this confidence → human review |

Resolution order: `--config PATH` → `$TESSERA_INDEXER_CONFIG` →
`./tessera_indexer.yaml` (working dir) → built-in defaults. **Relative paths
resolve against the config file's directory**, so a self-contained deploy dir
(config + models/ + data/) works from any working directory. An annotated
example ships in the wheel at `indexer/config/example.yaml`.

```bash
tessera-indexer config --config /path/to/tessera_indexer.yaml   # inspect effective config
tessera-indexer check --config /path/to/tessera_indexer.yaml    # verify an install
```

### Running the Demo (from source)

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
-   **`indexer/`**: Core logic for the Rule Engine, Classification Tiers, Work Queues, and HITL exporter. Ships as the `tessera-indexer` wheel; taxonomy schemas are bundled as package data (`indexer/taxonomy/`).
-   **`training/`**: Scripts for data preparation, model training (Colab), and local calibration.
-   **`models/`**: Stores the ONNX model binaries and TF-IDF fallback models (Note: Large binaries are excluded from Git).
-   **`data/`**: Stores generated corpora, training splits, and output queues.
-   **`docs/`**: Documentation, including the Colab Handguide.
-   **`main_demo.py`**: The primary entry point to demonstrate the system end-to-end.
