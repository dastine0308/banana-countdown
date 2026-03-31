"""
predictor.py — Sequential multi-model pipeline
  Stage 1: YOLO  → bounding box + class label + confidence
  Stage 2: CNN   → days_remaining (regression)
"""

import base64
import os
import cv2
import numpy as np
import torch
import torchvision.transforms as T
from torchvision import models
from ultralytics import YOLO

# ── Class metadata ────────────────────────────────────────────────────────────
CLASS_NAMES = {
    0: "Fresh Ripe",
    1: "Fresh Unripe",
    2: "Overripe",
    3: "Ripe",
    4: "Rotten",
    5: "Unripe",
}

BOX_COLORS = {
    "Fresh Unripe": (0,   200,  0),    # green
    "Fresh Ripe":   (0,   220, 100),   # green-yellow
    "Ripe":         (0,   200, 255),   # yellow
    "Overripe":     (0,   140, 255),   # orange
    "Rotten":       (0,    0,  200),   # red
    "Unripe":       (180, 180,   0),   # olive
}

# ── Regression CNN ────────────────────────────────────────────────────────────
REGRESSION_INPUT_SIZE = 224

regression_transform = T.Compose([
    T.ToPILImage(),
    T.Resize((REGRESSION_INPUT_SIZE, REGRESSION_INPUT_SIZE)),
    T.ToTensor(),
    T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])


def build_regression_model(weights_path: str):
    """ResNet-18 with a single linear output (regression head)."""
    model = models.resnet18(weights=None)
    model.fc = torch.nn.Linear(model.fc.in_features, 1)
    state = torch.load(weights_path, map_location="cpu")
    model.load_state_dict(state)
    model.eval()
    return model


# ── Main predictor class ──────────────────────────────────────────────────────
class BananaPredictor:
    def __init__(self, yolo_path: str, regression_path: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Stage 1 — YOLO
        self.yolo = YOLO(yolo_path)

        # Stage 2 — Regression CNN
        self.regressor = build_regression_model(regression_path).to(self.device)

        # YOLO inference thresholds (tunable via env vars)
        self.yolo_conf = float(os.getenv("YOLO_CONF", "0.5"))
        self.yolo_iou = float(os.getenv("YOLO_IOU", "0.5"))
        self.yolo_max_det = int(os.getenv("YOLO_MAX_DET", "10"))

    def _predict_days(self, image_bgr: np.ndarray, box) -> float:
        """Crop banana region, run regression CNN, return days remaining."""
        x1, y1, x2, y2 = map(int, box)
        # Clamp to image bounds
        h, w = image_bgr.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)

        if x1 == x2 or y1 == y2:
            return 0.0  # Invalid box, treat as 0 days remaining

        crop = image_bgr[y1:y2, x1:x2]
        crop_rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

        tensor = regression_transform(crop_rgb).unsqueeze(0).to(self.device)
        with torch.no_grad():
            days = self.regressor(tensor).item()

        return round(max(0.0, days), 1)   # clamp negative predictions to 0

    def _annotate(self, image: np.ndarray, detections: list) -> str:
        """Draw all bounding boxes + labels on image, return base64 PNG."""
        annotated = image.copy()
        for det in detections:
            x1, y1, x2, y2 = map(int, det["bounding_box"])
            label = det["class_label"]
            conf  = det["confidence"]
            days  = det["days_remaining"]
            color = BOX_COLORS.get(label, (255, 255, 255))

            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            tag = f"{label} {conf:.0%} | {days}d left"
            (tw, th), _ = cv2.getTextSize(tag, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(annotated, (x1, y1 - th - 8), (x1 + tw + 4, y1), color, -1)
            cv2.putText(annotated, tag, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)

        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 75]
        _, buf = cv2.imencode(".jpg", annotated, encode_param)
        return base64.b64encode(buf).decode("utf-8")

    def run(self, image_bgr: np.ndarray) -> dict:
        """
        Full sequential pipeline.
        Returns a dict with detections list + annotated_image base64.
        """
        # ── Stage 1: YOLO ─────────────────────────────────────────────────────
        yolo_results = self.yolo.predict(
            source=image_bgr,
            conf=self.yolo_conf,
            iou=self.yolo_iou,
            max_det=self.yolo_max_det,
            verbose=False,
        )[0]

        detections = []
        for box in yolo_results.boxes:
            coords     = box.xyxy[0].tolist()          # [x1, y1, x2, y2]
            class_id   = int(box.cls[0].item())
            confidence = round(float(box.conf[0].item()), 4)
            if confidence < self.yolo_conf:
                continue
            label      = CLASS_NAMES.get(class_id, "Unknown")

            # ── Stage 2: Regression CNN ────────────────────────────────────────
            days = self._predict_days(image_bgr, coords)

            detections.append({
                "class_label":   label,
                "confidence":    confidence,
                "bounding_box":  [round(c, 1) for c in coords],
                "days_remaining": days,
            })

        if not detections:
            return {}

        # ── Annotate & encode ─────────────────────────────────────────────────
        annotated_b64 = self._annotate(image_bgr, detections)

        return {
            "detections":     detections,
            "annotated_image": annotated_b64,
        }
