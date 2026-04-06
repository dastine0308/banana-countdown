# Build from repo: docker build -f backend/Dockerfile -t banana-api backend
# Requires backend/models/bestmodel.pt and backend/models/regression_best.pth locally (not in git).

FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# opencv-python-headless: no GL/X11; keep glib (common) + OpenMP for numpy/torch
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# CPU-only PyTorch (smaller image; Azure student tier is typically CPU)
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements-docker.txt .
# ultralytics declares opencv-python; uninstall GUI wheel so only headless provides cv2
RUN pip install -r requirements-docker.txt \
    && pip uninstall -y opencv-python \
    && pip install --no-cache-dir --force-reinstall --no-deps "opencv-python-headless>=4.8.0"

COPY app.py predictor.py ./
COPY models/ ./models/

EXPOSE 8000

# Azure sets PORT; default 8000 for local runs. One worker avoids loading weights per process.
CMD ["/bin/sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers 1 --threads 1 --timeout 120 app:app"]
