"""
train_yolo.py — Stage 1: Fine-tune YOLO on banana ripeness dataset
Logs metrics to Weights & Biases.
"""

import shutil
import wandb
import torch
from pathlib import Path
from ultralytics import YOLO

def main():

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
            "dataset":    "training/data.yaml",
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
        device=0 if torch.cuda.is_available() else "cpu",
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
    # Using Path() makes this work perfectly on Windows (E:\...) and Linux
    best_path = Path("runs/detect/banana_yolo/weights/best.pt")
    backend_model_path = Path("backend/models/bestmodel.pt")

    # Create directory if it doesn't exist
    backend_model_path.parent.mkdir(parents=True, exist_ok=True)

    if best_path.exists():
        shutil.copy(best_path, backend_model_path)
        print(f"Saved best YOLO weights to: {backend_model_path}")
    else:
        print(f"Warning: {best_path} not found. Check training logs.")

    # Upload the model to your team's W&B cloud
    artifact = wandb.Artifact("yolo-banana-model", type="model")
    artifact.add_file(backend_model_path)
    wandb.log_artifact(artifact)

    wandb.finish()

if __name__ == '__main__':
    main()