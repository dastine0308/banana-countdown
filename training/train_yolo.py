"""
train_yolo.py — Stage 1: Fine-tune YOLO on banana ripeness dataset
Logs metrics to Weights & Biases.
"""

import os
import wandb
from ultralytics import YOLO

# ── W&B setup ─────────────────────────────────────────────────────────────────
wandb.init(
    project="banana-countdown",
    name="yolo-finetune",
    config={
        "model":      "yolo11n.pt",
        "epochs":     50,
        "imgsz":      640,
        "batch":      16,
        "lr0":        0.01,
        "optimizer":  "AdamW",
        "dataset":    "data.yaml",
    }
)
cfg = wandb.config

# ── Load pretrained YOLO (transfer learning from COCO weights) ────────────────
model = YOLO(cfg.model)

# ── Train ─────────────────────────────────────────────────────────────────────
results = model.train(
    data=cfg.dataset,
    epochs=cfg.epochs,
    imgsz=cfg.imgsz,
    batch=cfg.batch,
    lr0=cfg.lr0,
    optimizer=cfg.optimizer,
    project="runs/detect",
    name="banana_yolo",
    exist_ok=True,
    device=0 if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu",
)

# ── Log final metrics to W&B ──────────────────────────────────────────────────
metrics = results.results_dict
wandb.log({
    "final/precision": metrics.get("metrics/precision(B)", 0),
    "final/recall":    metrics.get("metrics/recall(B)", 0),
    "final/mAP50":     metrics.get("metrics/mAP50(B)", 0),
    "final/mAP50-95":  metrics.get("metrics/mAP50-95(B)", 0),
})

# ── Save best weights ─────────────────────────────────────────────────────────
best_path = "runs/detect/banana_yolo/weights/best.pt"
os.makedirs("../backend/models", exist_ok=True)
import shutil
shutil.copy(best_path, "../backend/models/bestmodel.pt")
print(f"Saved best YOLO weights → ../backend/models/bestmodel.pt")

wandb.finish()
