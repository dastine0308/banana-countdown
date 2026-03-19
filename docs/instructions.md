# 🍌 Banana Countdown
### ENSF617 Final Project — Technical Instructions
*Sequential Multi-Model Pipeline: YOLO + Regression CNN*

---

## 1. Project Overview

Banana Countdown is a complete End-to-End Computer Vision project built with Python using a two-stage sequential multi-model pipeline. The system first detects a banana and classifies its ripeness stage using YOLO, then predicts how many days of shelf life remain using a CNN regression model.

**What the AI learns to detect:**
- Fresh Unripe
- Fresh Ripe
- Ripe
- Overripe
- Rotten
- Unripe

**Core Concept:**
Upload a banana photo → YOLO draws a bounding box + returns ripeness label + confidence score → Regression CNN predicts remaining shelf-life days → Result displayed in the UI.

---

## 2. Tech Stack

### 2.1 Datasets

| Dataset | Source | Purpose | Label Type |
| --- | --- | --- | --- |
| Ripeness Classes | Roboflow banana dataset | Train YOLO detector | 6 class labels + bounding boxes |
| Shelf-Life Days | Kaggle: days-death-to-a-banana | Train regression CNN | Numeric (`days_remaining`) |

> **Note:** Two separate datasets trained independently. The YOLO dataset requires bounding box annotations; the Kaggle dataset requires only day-count labels. Neither dataset is committed to GitHub — see Section 5 for download instructions.

### 2.2 Components

| Component | Technology | Purpose |
| --- | --- | --- |
| **Stage 1 — Detection** | YOLO (Ultralytics), OpenCV | Localize banana, classify ripeness stage, draw bounding box |
| **Stage 2 — Regression** | ResNet-18, PyTorch | Predict numeric shelf-life days from cropped banana image |
| **Experiment Tracking** | Weights & Biases (W&B) | Log training metrics, compare runs — team: ENSF-617-group-16 |
| **Backend** | Flask | REST API: receives image, runs both models, returns JSON result |
| **Frontend** | React, Next.js | User interface for image upload and result display |

---

## 3. System Architecture

### 3.1 Sequential Pipeline — End-to-End Workflow

```
User uploads banana image via React/Next.js frontend
      ↓
Flask (app.py) receives image via POST /predict endpoint
      ↓
┌─────────────────────────────────────────┐
│  Stage 1 — YOLO inference (full image)  │
│  Output: bounding box [x1,y1,x2,y2]     │
│          + class label + confidence     │
└─────────────────────────────────────────┘
      ↓
OpenCV crops banana region using bounding box coordinates
      ↓
┌─────────────────────────────────────────┐
│  Stage 2 — Regression CNN (cropped img) │
│  Output: days_remaining (float, e.g. 3.5)│
└─────────────────────────────────────────┘
      ↓
Flask assembles JSON response
      ↓
OpenCV annotates image: box + label + confidence + days
      ↓
Frontend displays annotated image + shelf-life prediction
```

### 3.2 JSON Response Schema

```json
{
  "detections": [
    {
      "class_label":    "Overripe",
      "confidence":     0.91,
      "bounding_box":   [120, 45, 380, 290],
      "days_remaining": 1.5
    }
  ],
  "annotated_image": "<base64-encoded PNG>"
}
```

### 3.3 Model Layer Detail

| | Stage 1 — YOLO | Stage 2 — Regression CNN |
| --- | --- | --- |
| **Input** | Full uploaded image | Cropped banana (from YOLO box) |
| **Output** | Box + class label + confidence | `days_remaining` (float) |
| **Pretrained on** | COCO (transfer learning) | ImageNet (transfer learning) |
| **Fine-tuned on** | Banana ripeness dataset | Kaggle days-to-death dataset |
| **Loss function** | YOLO composite (box + cls) | SmoothL1Loss (regression) |
| **Eval metrics** | Precision, Recall, mAP | MAE, RMSE, R² |

---

## 4. Core Features (MVP)

### Feature 1: Upload a Banana Image

**User Flow:**
- User opens the web app and sees an upload interface
- User selects or drags a banana photo (JPG/PNG)
- Image preview is shown before submission
- User clicks Analyze to trigger the pipeline

**Technical Implementation:**
- Next.js frontend: file input or drag-and-drop zone
- Image sent as multipart/form-data via POST to `/predict`
- Flask validates file type and size before passing to models

---

### Feature 2: YOLO Bounding Box Detection

**User Flow:**
- After upload, the returned image shows a colored bounding box drawn around the banana
- A label tag on the box displays the ripeness class and confidence score (e.g. `Overripe 91%`)
- Multiple boxes appear if multiple bananas are in the image

**Technical Implementation:**
- Load fine-tuned `bestmodel.pt` via Ultralytics YOLO API
- Run `model.predict(image)` to get boxes, labels, and confidence scores
- Use OpenCV `cv2.rectangle()` and `cv2.putText()` to draw annotations
- Encode annotated image as base64 PNG for JSON response

---

### Feature 3: Shelf-Life Days Prediction

**User Flow:**
- Beneath the annotated image, the app displays: `Estimated shelf life: ~2 days`
- The number updates per detected banana if multiple are present

**Technical Implementation:**
- After YOLO inference, extract bounding box coordinates
- Crop: `cropped = image[y1:y2, x1:x2]` using OpenCV
- Resize cropped image to 224×224 (ResNet-18 input size)
- Run regression CNN forward pass → single float output
- Round to 1 decimal place and return as `days_remaining` in JSON

---

## 5. Model Training

### 5.1 Environment Setup

Create a `.env` file in repo root (never commit this):
```bash
KAGGLE_USERNAME=your_kaggle_username
KAGGLE_KEY=your_kaggle_api_key
WANDB_API_KEY=your_wandb_api_key
```

Log in to W&B:
```bash
export $(cat .env | xargs)
wandb login
```

---

### 5.2 Stage 1 — YOLO Fine-Tuning (`train_yolo.py`)

- Base model: `yolo11n.pt` (COCO-pretrained YOLO11 nano — transfer learning)
- Dataset config: `data.yaml` defines train/val/test splits and 6 class names
- Freeze base layers, fine-tune on banana ripeness dataset
- W&B logs: loss, mAP50, mAP50-95, precision, recall per epoch
- Output: `backend/models/bestmodel.pt`

```bash
# Run from repo root
python training/train_yolo.py
```

---

### 5.3 Stage 2 — Regression CNN Training

#### Step 1 — Download Kaggle Dataset

```bash
export $(cat .env | xargs)
kaggle datasets download -d anishkumar00/days-death-to-a-banana
unzip days-death-to-a-banana.zip -d data/regression_raw
```

Raw files land in `data/regression_raw/banana_images_jpg/` with naming format:
```
banana_01_day_01.jpg   ← banana 1, photographed on day 1 (freshest)
banana_01_day_02.jpg   ← banana 1, photographed on day 2
banana_02_day_01.jpg   ← banana 2, photographed on day 1
...
```

`day_01` = freshest (most days remaining), `day_N` = oldest (fewest days remaining).

#### Step 2 — Prepare Dataset (`prepare_regression_data.py`)

```bash
# Run from repo root
python training/prepare_regression_data.py
```

This script:
- Parses day number from each filename using `re.search(r"day_(\d+)", fname)`
- Computes `days_remaining = max_day - day_shot`
- Shuffles with `random.seed(42)` for reproducibility
- Splits 80% train / 10% val / 10% test
- Copies images into folder structure:

```
data/regression/
  train/
    0/    ← images with 0 days remaining
    1/    ← images with 1 day remaining
    ...
  val/
    0/
    1/
    ...
  test/
    0/
    1/
    ...
```

> This folder structure allows PyTorch `ImageFolder` to load data without a CSV file.

#### Step 3 — Train (`train_regression.py`)

```bash
# Run from repo root
python training/train_regression.py
```

Key implementation details:
- Base model: ResNet-18 pretrained on ImageNet (transfer learning)
- Base layers frozen; only the final `fc` layer is trained
- Final layer replaced: `nn.Linear(512, 1)` — single regression output
- Custom `RegressionImageFolder` wrapper converts folder name (`"3"`) → `float` label (`3.0`)
- Loss: `SmoothL1Loss` (less sensitive to outliers than MSE)
- Optimizer: `Adam` on `model.fc.parameters()` only
- W&B logs: `train_loss`, `val_loss`, `val_MAE`, `val_RMSE`, `val_R²` per epoch
- Output: `backend/models/regression_best.pth` (saved on best val MAE)

#### Step 4 — Evaluate

Target metrics on test set:

| Metric | Target |
| --- | --- |
| MAE | < 1.0 day |
| RMSE | < 1.5 days |
| R² | > 0.85 |

---

### 5.4 Why This Is Transfer Learning (Both Models)

Both models leverage weights pretrained on large datasets (COCO for YOLO, ImageNet for ResNet-18) and fine-tune only the final layers on banana-specific data. This reduces training time and data requirements significantly.

---

## 6. Development Roadmap

### Phase 1: Setup & Environment
- [ ] Clone repo and install dependencies
- [ ] Create `.env` from `.env.example`, fill in Kaggle + W&B credentials
- [ ] Verify W&B login: `wandb login`
- [ ] Verify `yolo11n.pt` loads correctly with Ultralytics

### Phase 2: YOLO Training (Stage 1)
- [ ] Prepare banana ripeness dataset with bounding box labels
- [ ] Configure `training/data.yaml` with 6 class names and split paths
- [ ] Run `python training/train_yolo.py`
- [ ] Evaluate with Precision, Recall, mAP on validation set in W&B
- [ ] Confirm `backend/models/bestmodel.pt` saved

### Phase 3: Regression CNN Training (Stage 2)
- [ ] Download Kaggle dataset: `kaggle datasets download -d anishkumar00/days-death-to-a-banana`
- [ ] Unzip to `data/regression_raw/`
- [ ] Run `python training/prepare_regression_data.py` to build folder structure
- [ ] Verify `data/regression/train|val|test/<day>/` structure is correct
- [ ] Run `python training/train_regression.py`
- [ ] Evaluate MAE, RMSE, R² on test set in W&B
- [ ] Confirm `backend/models/regression_best.pth` saved

### Phase 4: Backend Integration
- [ ] Verify both model weights exist in `backend/models/`
- [ ] Test Flask `/predict` endpoint with Postman or curl
- [ ] Confirm JSON response includes `class_label`, `confidence`, `bounding_box`, `days_remaining`

### Phase 5: Frontend & Demo
- [ ] Run Next.js frontend: `cd frontend && npm run dev`
- [ ] Upload test banana images covering all 6 ripeness stages
- [ ] Verify annotated image and shelf-life prediction display correctly
- [ ] Prepare demo with multiple banana scenarios

---

## 7. Example Use Cases for Demo

| Scenario | YOLO Output | Regression Output | What User Sees |
| --- | --- | --- | --- |
| Fresh banana just purchased | Fresh Unripe — 94% | ~7 days | Green box, 7 days shelf life |
| Perfectly ripe banana | Ripe — 89% | ~2 days | Yellow box, 2 days left |
| Overripe, soft banana | Overripe — 91% | ~0.5 days | Orange box, less than 1 day |
| Rotten banana | Rotten — 96% | ~0 days | Red box, discard |
| Two bananas in one photo | Two separate boxes | Two day estimates | Both annotated independently |

---

## 8. Relevant Documentation & Links

- **GitHub Repo (original):** https://github.com/nightfury217836/Banana-Ripness-Detector
- **Kaggle Dataset (shelf life):** https://www.kaggle.com/datasets/anishkumar00/days-death-to-a-banana
- **Ultralytics YOLO Docs:** https://docs.ultralytics.com
- **Weights & Biases Docs:** https://docs.wandb.ai
- **PyTorch Transfer Learning Tutorial:** https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html
- **Flask REST API Docs:** https://flask.palletsprojects.com
