import os
import base64
import numpy as np
import cv2
from flask import Flask, request, jsonify
from flask_cors import CORS
from predictor import BananaPredictor

app = Flask(__name__)
CORS(app)

# Load both models once at startup
predictor = BananaPredictor(
    yolo_path=os.path.join("models", "bestmodel.pt"),
    regression_path=os.path.join("models", "regression_best.pth"),
)

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/predict", methods=["POST"])
def predict():
    if "image" not in request.files:
        return jsonify({"error": "No image field in request"}), 400

    file = request.files["image"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file type. Use JPG or PNG."}), 400

    # Decode image bytes → numpy array (BGR)
    img_bytes = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(img_bytes, cv2.IMREAD_COLOR)

    if image is None:
        return jsonify({"error": "Could not decode image"}), 400

    # Run sequential pipeline
    results = predictor.run(image)

    if not results:
        return jsonify({"error": "No banana detected in image"}), 200

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
