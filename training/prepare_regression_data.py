import os, re, random, shutil, platform
from collections import Counter

# __file__ ensures paths are correct regardless of where the script is run from
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR   = os.path.join(REPO_ROOT, "data", "regression_raw", "banana_images_jpg")
DEST_DIR  = os.path.join(REPO_ROOT, "data", "regression")

# ── Step 1: parse filenames ───────────────────────────────────────────────────
rows = []
for fname in os.listdir(RAW_DIR):
    if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
        continue
    match = re.search(r"day_(\d+)", fname)
    if not match:
        continue
    rows.append({"fname": fname, "day_shot": int(match.group(1))})

# ── Step 2: compute days_remaining ───────────────────────────────────────────
max_day = max(r["day_shot"] for r in rows)
for r in rows:
    r["days_remaining"] = max_day - r["day_shot"]

# ── Step 3: shuffle & split 80/10/10 ─────────────────────────────────────────
random.seed(42)
random.shuffle(rows)
n       = len(rows)
n_train = int(n * 0.8)
n_val   = int(n * 0.1)

splits = (["train"] * n_train +
          ["val"]   * n_val   +
          ["test"]  * (n - n_train - n_val))

for row, split in zip(rows, splits):
    row["split"] = split

# ── Step 4: copy into folder structure ───────────────────────────────────────
print("Copying files...")
for row in rows:
    dest_folder = os.path.join(DEST_DIR, row["split"], str(row["days_remaining"]))
    os.makedirs(dest_folder, exist_ok=True)
    shutil.copy(
        os.path.join(RAW_DIR, row["fname"]),
        os.path.join(dest_folder, row["fname"])
    )

# ── Step 5: summary ───────────────────────────────────────────────────────────
split_counts = Counter(row["split"] for row in rows)
day_vals     = sorted(set(row["days_remaining"] for row in rows))
print(f"Total images   : {n}")
print(f"Train/Val/Test : {split_counts['train']} / {split_counts['val']} / {split_counts['test']}")
print(f"days_remaining : {min(day_vals)} → {max(day_vals)} days")
print(f"Saved to       → {DEST_DIR}/")