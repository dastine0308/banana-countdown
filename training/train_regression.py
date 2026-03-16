"""
train_regression.py — Stage 2: Fine-tune ResNet-18 for shelf-life regression
Dataset: Kaggle days-death-to-a-banana
Logs metrics to Weights & Biases.

Expected dataset folder structure:
  data/regression/
    train/
      0/   ← images with 0 days remaining
      1/   ← images with 1 day remaining
      ...
    val/
      ...

OR a CSV-based dataset — see RegressionDataset below.
"""

import os
import shutil
import wandb
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import models, transforms
from PIL import Image
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, r2_score

# ── W&B setup ─────────────────────────────────────────────────────────────────
wandb.init(
    project="banana-countdown",
    name="regression-cnn",
    config={
        "base_model":   "resnet18",
        "pretrained":   True,
        "epochs":       40,
        "batch_size":   32,
        "lr":           1e-4,
        "weight_decay": 1e-5,
        "input_size":   224,
        "loss":         "SmoothL1",
        "dataset_csv":  "data/regression/labels.csv",  # path, image_path, days columns
    }
)
cfg = wandb.config

# ── Dataset ───────────────────────────────────────────────────────────────────
class RegressionDataset(Dataset):
    """
    Expects a CSV with columns: image_path, days
      image_path — relative path to image from project root
      days       — float, shelf life in days
    """
    def __init__(self, csv_path, split="train", transform=None):
        df = pd.read_csv(csv_path)
        self.df = df[df["split"] == split].reset_index(drop=True)
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        image = Image.open(row["image_path"]).convert("RGB")
        if self.transform:
            image = self.transform(image)
        label = torch.tensor(float(row["days"]), dtype=torch.float32)
        return image, label


train_tf = transforms.Compose([
    transforms.Resize((cfg.input_size, cfg.input_size)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

val_tf = transforms.Compose([
    transforms.Resize((cfg.input_size, cfg.input_size)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
])

train_ds = RegressionDataset(cfg.dataset_csv, split="train", transform=train_tf)
val_ds   = RegressionDataset(cfg.dataset_csv, split="val",   transform=val_tf)

train_loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True,  num_workers=2)
val_loader   = DataLoader(val_ds,   batch_size=cfg.batch_size, shuffle=False, num_workers=2)

# ── Model — ResNet-18 with regression head (transfer learning) ────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"

model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1 if cfg.pretrained else None)
model.fc = nn.Linear(model.fc.in_features, 1)   # single output neuron
model = model.to(device)

# ── Loss & optimizer ──────────────────────────────────────────────────────────
criterion = nn.SmoothL1Loss()
optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg.epochs)

# ── Training loop ─────────────────────────────────────────────────────────────
best_val_mae = float("inf")

for epoch in range(cfg.epochs):
    # Train
    model.train()
    train_losses = []
    for images, labels in train_loader:
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        preds = model(images).squeeze(1)
        loss = criterion(preds, labels)
        loss.backward()
        optimizer.step()
        train_losses.append(loss.item())

    scheduler.step()

    # Validate
    model.eval()
    all_preds, all_labels = [], []
    val_losses = []
    with torch.no_grad():
        for images, labels in val_loader:
            images, labels = images.to(device), labels.to(device)
            preds = model(images).squeeze(1)
            loss = criterion(preds, labels)
            val_losses.append(loss.item())
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    mae  = mean_absolute_error(all_labels, all_preds)
    rmse = np.sqrt(np.mean((np.array(all_labels) - np.array(all_preds)) ** 2))
    r2   = r2_score(all_labels, all_preds)

    wandb.log({
        "epoch":       epoch + 1,
        "train/loss":  np.mean(train_losses),
        "val/loss":    np.mean(val_losses),
        "val/MAE":     mae,
        "val/RMSE":    rmse,
        "val/R2":      r2,
        "lr":          scheduler.get_last_lr()[0],
    })

    print(f"Epoch {epoch+1:3d}/{cfg.epochs} | train_loss={np.mean(train_losses):.4f} "
          f"| val_MAE={mae:.3f} | val_RMSE={rmse:.3f} | R²={r2:.3f}")

    # Save best checkpoint
    if mae < best_val_mae:
        best_val_mae = mae
        torch.save(model.state_dict(), "regression_best.pth")
        print(f"  ✓ Saved best model (MAE={mae:.3f})")

# ── Copy to backend/models ────────────────────────────────────────────────────
os.makedirs("../backend/models", exist_ok=True)
shutil.copy("regression_best.pth", "../backend/models/regression_best.pth")
print("Saved regression weights → ../backend/models/regression_best.pth")

wandb.finish()
