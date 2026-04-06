"""
Fine-tune ResNet-18 for shelf-life regression
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

"""

import os
import wandb
import torch
import torch.nn as nn
import torch.optim as optim
import platform
import matplotlib.pyplot as plt
import numpy as np
from torchvision import models, transforms
from torchvision.datasets import ImageFolder
from torch.utils.data import DataLoader
from sklearn.metrics import mean_absolute_error, r2_score


def per_class_mae(y_true, y_pred):
    """Calculate per-class MAE."""
    y_true = np.asarray(y_true, dtype=np.float64).ravel()
    y_pred = np.asarray(y_pred, dtype=np.float64).ravel()
    out = {}
    for c in np.unique(y_true):
        mask = y_true == c
        if not np.any(mask):
            continue
        out[int(c)] = float(np.mean(np.abs(y_pred[mask] - y_true[mask])))
    return out


def per_class_counts(y_true):
    y_true = np.asarray(y_true, dtype=np.float64).ravel()
    return {int(c): int(np.sum(y_true == c)) for c in np.unique(y_true)}


def main():
    # --- 1. Initialize W&B ---
    wandb.init(
        project="banana-countdown",
        entity="ENSF-617-group-16",
        config={
            "learning_rate": 1e-4,
            "epochs":        200,
            "batch_size":    32,
            "architecture":  "ResNet-18",
            "dataset":       "data/regression",
            "loss":          "SmoothL1",
            "weight_decay":  1e-5,
            "input_size":    224,
            "trainable_backbone": "layer3+layer4+fc",
        }
    )
    config = wandb.config

    # --- 2. Setup Device & Paths ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(device)

    # __file__ ensures paths are correct regardless of where the script is run from
    REPO_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TRAIN_DIR   = os.path.join(REPO_ROOT, "data", "regression", "train")
    VAL_DIR     = os.path.join(REPO_ROOT, "data", "regression", "val")
    TEST_DIR    = os.path.join(REPO_ROOT, "data", "regression", "test")
    WEIGHTS_OUT = os.path.join(REPO_ROOT, "backend", "models", "regression_best.pth")

    print(f"REPO_ROOT : {REPO_ROOT}")
    print(f"TRAIN_DIR : {TRAIN_DIR}")
    print(f"WEIGHTS   : {WEIGHTS_OUT}")

    # --- 3. Data Augmentation and Transforms ---
    data_transforms = {
        "train": transforms.Compose([
            transforms.Resize((config.input_size, config.input_size)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),          
            transforms.RandomRotation(15),            
            transforms.ColorJitter(
                brightness=0.4,   
                contrast=0.4,     
                saturation=0.4,   
                hue=0.1,          
            ),            
            transforms.RandomGrayscale(p=0.05),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            transforms.RandomErasing(p=0.2),
        ]),
        "val_test": transforms.Compose([
            transforms.Resize((config.input_size, config.input_size)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]),
    }

    # --- 4. Load Datasets ---
    class RegressionImageFolder(ImageFolder):
        """ImageFolder wrapper that converts class index → float days_remaining."""
        def __getitem__(self, idx):
            image, class_idx = super().__getitem__(idx)
            # folder name is the label e.g. "3" → 3.0
            days = torch.tensor(float(self.classes[class_idx]), dtype=torch.float32)
            return image, days

    train_dataset = RegressionImageFolder(TRAIN_DIR, data_transforms["train"])
    val_dataset   = RegressionImageFolder(VAL_DIR,   data_transforms["val_test"])
    test_dataset  = RegressionImageFolder(TEST_DIR,  data_transforms["val_test"])

    # Data Loaders
    is_mac     = platform.system() == "Darwin"
    is_windows = platform.system() == "Windows"

    num_workers = 0 if (is_mac or is_windows) else 4
    pin_memory  = False if (is_mac or is_windows) else True

    train_loader = DataLoader(train_dataset, batch_size=config.batch_size, shuffle=True,  num_workers=num_workers, pin_memory=pin_memory)
    val_loader   = DataLoader(val_dataset,   batch_size=config.batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory)
    test_loader  = DataLoader(test_dataset,  batch_size=config.batch_size, shuffle=False, num_workers=num_workers, pin_memory=pin_memory)

    # --- 5. Initialize ResNet-18 ---
    model = models.resnet18(weights=models.ResNet18_Weights.IMAGENET1K_V1)

    # Freeze stem + layer1–2; train layer3–4 + fc (finer features for adjacent-day confusion, e.g. day 6/7/8)
    for name, param in model.named_parameters():
        if "layer3" in name or "layer4" in name or "fc" in name:
            param.requires_grad = True
        else:
            param.requires_grad = False

    # Replace classifier head with single regression output
    model.fc = nn.Linear(model.fc.in_features, 1)
    model = model.to(device)

    # --- 6. Loss, Optimizer ---
    criterion = nn.SmoothL1Loss()
    optimizer = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=config.learning_rate,
        weight_decay=config.weight_decay
    )

    wandb.watch(model, log="all")
    best_val_mae = float("inf")
    patience = 25
    no_improve = 0

    # --- 7. Training & Validation Loop ---
    for epoch in range(config.epochs):
        # Training Phase
        model.train()
        train_loss = 0.0
        for inputs, labels in train_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(inputs).squeeze(1)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        avg_train_loss = train_loss / len(train_loader)

        # Validation Phase
        model.eval()
        val_loss = 0.0
        all_preds, all_labels = [], []
        with torch.no_grad():
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs).squeeze(1)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
                all_preds.extend(outputs.cpu().numpy())
                all_labels.extend(labels.cpu().numpy())

        avg_val_loss = val_loss / len(val_loader)
        mae  = mean_absolute_error(all_labels, all_preds)
        rmse = np.sqrt(np.mean((np.array(all_labels) - np.array(all_preds)) ** 2))
        r2   = r2_score(all_labels, all_preds)
        val_pcm = per_class_mae(all_labels, all_preds)

        # Log metrics
        log_dict = {
            "epoch":      epoch + 1,
            "train_loss": avg_train_loss,
            "val_loss":   avg_val_loss,
            "val_MAE":    mae,
            "val_RMSE":   rmse,
            "val_R2":     r2,
        }
        for day, m in val_pcm.items():
            log_dict[f"val_MAE_per_class/{day}"] = m
        wandb.log(log_dict)

        pcm_str = " ".join(f"d{k}:{v:.2f}" for k, v in sorted(val_pcm.items()))
        print(
            f"Epoch {epoch+1}/{config.epochs} | Train Loss: {avg_train_loss:.4f} | "
            f"Val MAE: {mae:.3f} | R²: {r2:.3f} | per-class: {pcm_str}"
        )

        # Save Best Model
        if mae < best_val_mae:
            best_val_mae = mae
            os.makedirs(os.path.dirname(WEIGHTS_OUT), exist_ok=True)
            torch.save(model.state_dict(), WEIGHTS_OUT)
            print(f"--> Best model saved → {WEIGHTS_OUT}")
            no_improve = 0
        else:
            no_improve += 1
            if no_improve >= patience:
                print(f"Early stopping at epoch {epoch + 1}")
                wandb.log({"early_stopping_epoch": epoch + 1})
                break
            
    # --- 8. Final Test Phase ---
    print("\n--- Final Evaluation on Test Set ---")
    model.load_state_dict(torch.load(WEIGHTS_OUT, weights_only=True))
    model.eval()

    test_loss = 0.0
    all_preds, all_labels = [], []

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs).squeeze(1)
            loss = criterion(outputs, labels)
            test_loss += loss.item()
            all_preds.extend(outputs.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    avg_test_loss = test_loss / len(test_loader)
    test_mae  = mean_absolute_error(all_labels, all_preds)
    test_rmse = np.sqrt(np.mean((np.array(all_labels) - np.array(all_preds)) ** 2))
    test_r2   = r2_score(all_labels, all_preds)

    test_pcm = per_class_mae(all_labels, all_preds)
    test_counts = per_class_counts(all_labels)

    test_log = {
        "test_loss": avg_test_loss,
        "test_MAE":  test_mae,
        "test_RMSE": test_rmse,
        "test_R2":   test_r2,
    }
    for day, m in test_pcm.items():
        test_log[f"test_MAE_per_class/{day}"] = m
    wandb.log(test_log)

    print(f"Test MAE: {test_mae:.3f} | Test RMSE: {test_rmse:.3f} | Test R²: {test_r2:.3f}")
    print("Test per-class MAE (true day → MAE, n):")
    for day in sorted(test_pcm.keys()):
        n = test_counts.get(day, 0)
        print(f"  day {day}: MAE={test_pcm[day]:.3f}  (n={n})")

    # --- Scatter plot: Predicted vs True ---
    fig1, ax1 = plt.subplots(figsize=(6, 6))
    ax1.scatter(all_labels, all_preds, alpha=0.5, color="steelblue")
    # perfect prediction line
    min_val = min(min(all_labels), min(all_preds))
    max_val = max(max(all_labels), max(all_preds))
    ax1.plot([min_val, max_val], [min_val, max_val], "r--", label="Perfect prediction")
    ax1.set_xlabel("True days remaining")
    ax1.set_ylabel("Predicted days remaining")
    ax1.set_title(f"Predicted vs True  (MAE={test_mae:.3f}, R²={test_r2:.3f})")
    ax1.legend()
    wandb.log({"test/predicted_vs_true": wandb.Image(fig1)})
    plt.close(fig1)

    # --- Residual plot: Error distribution ---
    residuals = np.array(all_preds) - np.array(all_labels)
    fig2, ax2 = plt.subplots(figsize=(6, 4))
    ax2.hist(residuals, bins=20, color="salmon", edgecolor="white")
    ax2.axvline(0, color="black", linestyle="--", label="Zero error")
    ax2.set_xlabel("Prediction error (pred - true)")
    ax2.set_ylabel("Count")
    ax2.set_title("Residual distribution")
    ax2.legend()
    wandb.log({"test/residual_distribution": wandb.Image(fig2)})
    plt.close(fig2)

    # --- 9. Upload weights to W&B Artifacts ---
    artifact = wandb.Artifact(
        name="regression-best",
        type="model",
        description=f"ResNet-18 regression model — best val MAE: {best_val_mae:.3f}"
    )
    artifact.add_file(WEIGHTS_OUT)
    wandb.log_artifact(artifact)
    print("Uploaded → W&B Artifacts: regression-best")

    wandb.finish()

if __name__ == "__main__":
    main()