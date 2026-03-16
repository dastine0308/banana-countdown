# 🍌 Banana Countdown
### ENSF617 Final Project — Computer Vision
*Sequential Multi-Model Pipeline: YOLO Detection + CNN Regression*

---

## Overview

Banana Countdown is an end-to-end Computer Vision web app that:
1. **Detects** a banana in an uploaded image and classifies its ripeness stage (YOLO)
2. **Predicts** how many days of shelf life remain (Regression CNN)

Upload a photo → get a bounding box, ripeness label, confidence score, and shelf-life countdown.

![Pipeline](docs/pipeline.png)

---

## Ripeness Classes (6)

| Class | Description |
|---|---|
| Fresh Unripe | Newly harvested, fully green |
| Unripe | Green, not yet ready |
| Fresh Ripe | Just turned yellow |
| Ripe | Perfect eating condition |
| Overripe | Soft, browning — best for baking |
| Rotten | Discard |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Stage 1 — Detection | YOLO (Ultralytics), OpenCV |
| Stage 2 — Regression | ResNet-18, PyTorch |
| Experiment Tracking | Weights & Biases (W&B) |
| Backend | Flask |
| Frontend | React, Next.js |

---

## Repo Structure

```
banana-countdown/
├── backend/
│   ├── app.py               # Flask REST API
│   ├── predictor.py         # Sequential pipeline logic
│   ├── requirements.txt
│   └── models/              # Place bestmodel.pt & regression_best.pth here
├── frontend/
│   └── ...                  # Next.js app
├── training/
│   ├── train_yolo.py        # Stage 1: YOLO fine-tuning
│   ├── train_regression.py  # Stage 2: Regression CNN training
│   └── data.yaml            # YOLO dataset config
├── docs/
│   └── instructions.md      # Full project instructions
└── README.md
```

---

## Quickstart

### 1. Clone & install backend
```bash
git clone https://github.com/YOUR_USERNAME/banana-countdown.git
cd banana-countdown/backend
pip install -r requirements.txt
```

### 2. Add model weights
Place your trained model files in `backend/models/`:
- `bestmodel.pt` — fine-tuned YOLO weights
- `regression_best.pth` — regression CNN weights

### 3. Run the backend
```bash
python app.py
# API available at http://localhost:5000
```

### 4. Run the frontend
```bash
cd frontend
npm install
npm run dev
# UI available at http://localhost:3000
```

---

## API

### `POST /predict`

**Request:** `multipart/form-data` with field `image` (JPG or PNG)

**Response:**
```json
{
  "class_label":     "Overripe",
  "confidence":      0.91,
  "bounding_box":    [120, 45, 380, 290],
  "days_remaining":  1.5,
  "annotated_image": "<base64-encoded PNG>"
}
```

---

## Training

### Stage 1 — YOLO Fine-Tuning
```bash
cd training
python train_yolo.py
```
Trains `yolo11n.pt` on the banana ripeness dataset. Logs to W&B. Saves `bestmodel.pt`.

### Stage 2 — Regression CNN
```bash
python train_regression.py
```
Fine-tunes ResNet-18 on the [Kaggle days-to-death dataset](https://www.kaggle.com/datasets/anishkumar00/days-death-to-a-banana). Logs to W&B. Saves `regression_best.pth`.

---

## Datasets

| Dataset | Purpose | Labels |
|---|---|---|
| [Banana Ripeness (Roboflow)](https://universe.roboflow.com) | YOLO training | Bounding boxes + 6 class labels |
| [Days to Death (Kaggle)](https://www.kaggle.com/datasets/anishkumar00/days-death-to-a-banana) | Regression CNN training | Day count (numeric) |

---

## References

- [Ultralytics YOLO Docs](https://docs.ultralytics.com)
- [Weights & Biases Docs](https://docs.wandb.ai)
- [PyTorch Transfer Learning Tutorial](https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html)
- [Original inspiration repo](https://github.com/nightfury217836/Banana-Ripness-Detector)
