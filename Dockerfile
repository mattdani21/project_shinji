# syntax=docker/dockerfile:1
#
# Tessera AI Indexer — on-prem container.
#
# Build:    docker build -t tessera-indexer .
# Run:      docker run --rm -v /host/models:/app/models -v /host/inbox:/app/data/inbox tessera-indexer check
#
# Notes:
#  - Model binaries (model.onnx, tier4_model.joblib) are NOT committed to git;
#    mount or COPY them into /app/models at runtime for deep-learning Tier 4.
#    Without them the container still runs Tier 1 (QR) + TF-IDF fallback.
#  - All inference runs inside the container — no data leaves the host.

FROM python:3.11-slim AS builder

WORKDIR /build
COPY pyproject.toml README.md ./
COPY indexer ./indexer
COPY generator ./generator
RUN pip install --no-cache-dir build wheel \
    && python -m build --wheel

FROM python:3.11-slim

WORKDIR /app

# Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Wheel + runtime deps (core only; add `[onnx]` by editing the line below for
# the deep-learning Tier 4: pip install "/tmp/*.whl[onnx]")
COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir "/tmp/"*.whl

# Models directory (binaries mountable at runtime) + runtime data dirs
COPY models/ ./models/
RUN mkdir -p /app/data/workqueues /app/data/human_review /app/data/inbox

ENTRYPOINT ["tessera-indexer"]
CMD ["--help"]
