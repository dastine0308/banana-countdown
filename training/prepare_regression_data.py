"""
prepare_regression_data.py

Pipeline:
  1. Parse filenames  → day_shot → days_remaining
  2. Augment minority classes (days_remaining where n < MIN_SAMPLES)
     - Augmented images are saved to a temp folder (not mixed into RAW_DIR)
  3. Stratified 80/10/10 split
  4. Copy into data/regression/train|val|test/<days_remaining>/

Usage:
    python scripts/prepare_regression_data.py

    # To re-run from scratch:
    rm -rf data/regression
    python scripts/prepare_regression_data.py
"""

import os
import re
import random
import shutil
from collections import Counter, defaultdict

from PIL import Image
import torchvision.transforms as T

# ── Config ────────────────────────────────────────────────────────────────────
REPO_ROOT   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR     = os.path.join(REPO_ROOT, "data", "regression_raw", "banana_images_jpg")
AUG_DIR     = os.path.join(REPO_ROOT, "data", "regression_aug_tmp")   # temp augmented images
DEST_DIR    = os.path.join(REPO_ROOT, "data", "regression")

RANDOM_SEED  = 42
TRAIN_RATIO  = 0.8
VAL_RATIO    = 0.1
# TEST_RATIO  = 1 - TRAIN_RATIO - VAL_RATIO = 0.1

# Classes with fewer than MIN_SAMPLES will be augmented up to TARGET_SAMPLES
MIN_SAMPLES    = 20
TARGET_SAMPLES = 40

# Augmentation pipeline for minority oversampling
AUG_TRANSFORM = T.Compose([
    T.RandomHorizontalFlip(p=0.5),
    T.RandomVerticalFlip(p=0.3),
    T.RandomRotation(degrees=20),
    T.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.3, hue=0.1),
    T.RandomResizedCrop(size=224, scale=(0.75, 1.0)),
    T.RandomGrayscale(p=0.05),
])


# ── Helpers ───────────────────────────────────────────────────────────────────
def list_images(folder):
    return [
        f for f in os.listdir(folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]


def augment_class(day_remaining, src_paths, target_count, aug_dir):
    """
    Generate augmented images for one class until we reach target_count total.
    Saves to aug_dir/<days_remaining>/ and returns list of new file paths.
    """
    out_dir = os.path.join(aug_dir, str(day_remaining))
    os.makedirs(out_dir, exist_ok=True)

    new_paths = []
    needed    = target_count - len(src_paths)
    idx       = 0

    while len(new_paths) < needed:
        src_path = src_paths[idx % len(src_paths)]
        img      = Image.open(src_path).convert("RGB")
        aug_img  = AUG_TRANSFORM(img)

        out_fname = f"aug_{day_remaining}_{idx:04d}.jpg"
        out_path  = os.path.join(out_dir, out_fname)
        aug_img.save(out_path, quality=95)
        new_paths.append(out_path)
        idx += 1

    print(f"  days_remaining={day_remaining}: "
          f"{len(src_paths)} original + {len(new_paths)} augmented "
          f"= {len(src_paths) + len(new_paths)} total")
    return new_paths


# ── Step 1: Parse filenames ───────────────────────────────────────────────────
print("=" * 60)
print("Step 1: Parsing filenames …")
rows = []
for fname in os.listdir(RAW_DIR):
    if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
        continue
    match = re.search(r"day_(\d+)", fname)
    if not match:
        continue
    rows.append({
        "fname":    fname,
        "path":     os.path.join(RAW_DIR, fname),
        "day_shot": int(match.group(1)),
    })

max_day = max(r["day_shot"] for r in rows)
for r in rows:
    r["days_remaining"] = max_day - r["day_shot"]

# Group by class
groups = defaultdict(list)
for r in rows:
    groups[r["days_remaining"]].append(r["path"])

print(f"  Total raw images : {len(rows)}")
print(f"  max_day          : {max_day}")
print(f"  Classes          : {sorted(groups.keys())}")
print()


# ── Step 2: Augment minority classes ─────────────────────────────────────────
print("Step 2: Augmenting minority classes …")

# Clear previous augmentation temp folder
if os.path.exists(AUG_DIR):
    shutil.rmtree(AUG_DIR)
os.makedirs(AUG_DIR, exist_ok=True)

# all_paths[days_remaining] = [path1, path2, ...]  (original + augmented)
all_paths = {}
for day, paths in groups.items():
    if len(paths) < MIN_SAMPLES:
        aug_paths = augment_class(day, paths, TARGET_SAMPLES, AUG_DIR)
        all_paths[day] = paths + aug_paths
    else:
        all_paths[day] = paths
        print(f"  days_remaining={day}: {len(paths)} images (no augmentation needed)")

print()
print("  Post-augmentation counts:")
for day in sorted(all_paths.keys()):
    print(f"    days_remaining={day}: {len(all_paths[day])} images")
print()


# ── Step 3: Stratified 80/10/10 split ────────────────────────────────────────
print("Step 3: Stratified split (80/10/10) …")
random.seed(RANDOM_SEED)

split_records = []   # [{"path": ..., "days_remaining": ..., "split": ...}]

for day in sorted(all_paths.keys()):
    paths = all_paths[day][:]
    random.shuffle(paths)
    n = len(paths)

    # Guarantee at least 1 sample in val and test
    n_test  = round(n * (1 - TRAIN_RATIO - VAL_RATIO))
    n_val   = round(n * VAL_RATIO)
    n_train = n - n_val - n_test

    for i, path in enumerate(paths):
        if i < n_train:
            split = "train"
        elif i < n_train + n_val:
            split = "val"
        else:
            split = "test"
        split_records.append({
            "path":           path,
            "days_remaining": day,
            "split":          split,
        })

split_counts = Counter(r["split"] for r in split_records)
print(f"  Train: {split_counts['train']}  "
      f"Val: {split_counts['val']}  "
      f"Test: {split_counts['test']}  "
      f"Total: {len(split_records)}")
print()

# Per-class split summary
print("  Per-class split breakdown:")
class_splits = defaultdict(Counter)
for r in split_records:
    class_splits[r["days_remaining"]][r["split"]] += 1
for day in sorted(class_splits.keys()):
    c = class_splits[day]
    print(f"    days_remaining={day}: "
          f"train={c['train']}  val={c['val']}  test={c['test']}")
print()


# ── Step 4: Copy into folder structure ───────────────────────────────────────
print("Step 4: Copying files into data/regression/ …")

# Clear destination
if os.path.exists(DEST_DIR):
    shutil.rmtree(DEST_DIR)
os.makedirs(DEST_DIR, exist_ok=True)

for r in split_records:
    dest_folder = os.path.join(DEST_DIR, r["split"], str(r["days_remaining"]))
    os.makedirs(dest_folder, exist_ok=True)
    fname = os.path.basename(r["path"])
    shutil.copy(r["path"], os.path.join(dest_folder, fname))

print(f"  Done → {DEST_DIR}/")
print()


# ── Step 5: Final summary ─────────────────────────────────────────────────────
print("=" * 60)
print("Final dataset summary:")
for split in ["train", "val", "test"]:
    split_dir = os.path.join(DEST_DIR, split)
    total = 0
    print(f"\n  {split}/")
    for cls in sorted(os.listdir(split_dir), key=lambda x: int(x)):
        cls_dir = os.path.join(split_dir, cls)
        if not os.path.isdir(cls_dir):
            continue
        n = len(list_images(cls_dir))
        print(f"    days_remaining={cls}: {n} images")
        total += n
    print(f"    total: {total} images")

print()
print("✅ prepare_regression_data.py complete.")
print(f"   Augmented temp files kept at: {AUG_DIR}")
print("   (You may delete AUG_DIR after training if disk space is a concern.)")