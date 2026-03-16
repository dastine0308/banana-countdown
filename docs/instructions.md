# 🍌 Banana Countdown

### ENSF617 Final Project — Technical Instructions

_Sequential Multi-Model Pipeline: YOLO + Regression CNN_

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

| Dataset          | Source                         | Purpose              | Label Type                      |
| ---------------- | ------------------------------ | -------------------- | ------------------------------- |
| Ripeness Classes | Original YOLO banana dataset   | Train YOLO detector  | 6 class labels + bounding boxes |
| Shelf-Life Days  | Kaggle: days-death-to-a-banana | Train regression CNN | Numeric (days remaining)        |

> **Note:** These are two separate datasets trained independently. The YOLO dataset requires bounding box annotations; the Kaggle dataset requires only day-count labels. They do not need to be combined.

### 2.2 Components

| Component                | Technology                         | Purpose                                                         |
| ------------------------ | ---------------------------------- | --------------------------------------------------------------- |
| **Stage 1 — Detection**  | YOLO (Ultralytics), OpenCV         | Localize banana, classify ripeness stage, draw bounding box     |
| **Stage 2 — Regression** | CNN (ResNet/EfficientNet), PyTorch | Predict numeric shelf-life days from cropped banana image       |
| **Experiment Tracking**  | Weights & Biases (W&B)             | Log training metrics, compare runs, visualize model performance |
| **Backend**              | Flask                              | REST API: receives image, runs both models, returns JSON result |
| **Frontend**             | React, Next.js                     | User interface for image upload and result display              |

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
  "class_label": "Overripe",
  "confidence": 0.91,
  "bounding_box": [120, 45, 380, 290],
  "days_remaining": 1.5,
  "annotated_image": "<base64-encoded PNG>"
}
```

### 3.3 Model Layer Detail

|                   | Stage 1 — YOLO                 | Stage 2 — Regression CNN       |
| ----------------- | ------------------------------ | ------------------------------ |
| **Input**         | Full uploaded image            | Cropped banana (from YOLO box) |
| **Output**        | Box + class label + confidence | days_remaining (float)         |
| **Pretrained on** | COCO (transfer learning)       | ImageNet (transfer learning)   |
| **Fine-tuned on** | Banana ripeness dataset        | Kaggle days-to-death dataset   |
| **Loss function** | YOLO composite (box + cls)     | MSE / MAE (regression)         |
| **Eval metrics**  | Precision, Recall, mAP         | MAE, RMSE, R²                  |

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
- Crop: `cropped = image[y1:y2, x1:x2]` using OpenCV/PIL
- Resize cropped image to regression CNN input size (e.g. 224×224)
- Run regression CNN forward pass → single float output
- Round to 1 decimal place and return as `days_remaining` in JSON response

---

## 5. Model Training

### 5.1 Stage 1 — YOLO Fine-Tuning (`train_yolo.py`)

- Base model: `yolo11n.pt` (COCO-pretrained YOLO11 nano — transfer learning)
- Dataset config: `data.yaml` defines train/val/test splits and 6 class names
- Key hyperparameters: epochs, imgsz, batch size, learning rate
- W&B integration: logs loss, mAP, precision, recall per epoch
- Output: saved as `bestmodel.pt`

### 5.2 Stage 2 — Regression CNN Training (`train_regression.py`)

- Base model: ResNet-18 pretrained on ImageNet (transfer learning)
- Replace final classification layer with a single linear output neuron
- Loss function: `SmoothL1Loss` (regression, not classification)
- Dataset: Kaggle days-death-to-a-banana
- W&B integration: logs MAE, RMSE, R² per epoch
- Output: saved as `regression_best.pth`

### 5.3 Why This Is Transfer Learning (Both Models)

Both models leverage weights pretrained on large datasets (COCO for YOLO, ImageNet for the regression CNN) and fine-tune on banana-specific data. This dramatically reduces the training data and compute required.

---

## 6. Development Roadmap

### Phase 1: Setup & Environment

- [ ] Initialize Next.js frontend and Flask backend repos
- [ ] Install dependencies: `ultralytics`, `torch`, `torchvision`, `flask`, `opencv-python`, `wandb`
- [ ] Configure W&B project for experiment tracking
- [ ] Verify `yolo11n.pt` loads correctly with Ultralytics

### Phase 2: YOLO Training (Stage 1)

- [ ] Prepare banana ripeness dataset with bounding box labels
- [ ] Configure `data.yaml` with 6 class names and split paths
- [ ] Run `train_yolo.py` to fine-tune `yolo11n.pt`
- [ ] Evaluate with Precision, Recall, mAP on validation set
- [ ] Save best checkpoint as `bestmodel.pt`

### Phase 3: Regression CNN Training (Stage 2)

- [ ] Download and prepare Kaggle days-death-to-a-banana dataset
- [ ] Build regression CNN (ResNet-18 with linear output head)
- [ ] Train on day-count labeled images, log to W&B
- [ ] Evaluate with MAE, RMSE, R² on validation set
- [ ] Save best checkpoint as `regression_best.pth`

### Phase 4: Backend Integration

- [ ] Build Flask `/predict` endpoint that loads both models
- [ ] Implement sequential pipeline: YOLO → crop → regression CNN
- [ ] Return JSON with all detection fields + `days_remaining`
- [ ] Test with Postman or curl

### Phase 5: Frontend & Demo

- [ ] Build Next.js upload UI with drag-and-drop
- [ ] Display annotated image and shelf-life prediction
- [ ] Handle loading state, errors, and multiple bananas
- [ ] Prepare demo images covering all 6 ripeness stages

---

## 7. Example Use Cases for Demo

| Scenario                    | YOLO Output           | Regression Output | What User Sees               |
| --------------------------- | --------------------- | ----------------- | ---------------------------- |
| Fresh banana just purchased | Fresh Unripe — 94%    | ~7 days           | Green box, 7 days shelf life |
| Perfectly ripe banana       | Ripe — 89%            | ~2 days           | Yellow box, 2 days left      |
| Overripe, soft banana       | Overripe — 91%        | ~0.5 days         | Orange box, less than 1 day  |
| Rotten banana               | Rotten — 96%          | ~0 days           | Red box, discard             |
| Two bananas in one photo    | Two boxes with labels | Two day estimates | Both annotated independently |

---

## 8. Relevant Documentation & Links

- **GitHub Repo (original):** https://github.com/nightfury217836/Banana-Ripness-Detector
- **Kaggle Dataset (shelf life):** https://www.kaggle.com/datasets/anishkumar00/days-death-to-a-banana
- **Roboflow Dataset (Banana Ripening Process Computer Vision Model):** https://universe.roboflow.com/fruit-ripening/banana-ripening-process
- **Ultralytics YOLO Docs:** https://docs.ultralytics.com
- **Weights & Biases Docs:** https://docs.wandb.ai
- **PyTorch Transfer Learning Tutorial:** https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html
- **Flask REST API Docs:** https://flask.palletsprojects.com
