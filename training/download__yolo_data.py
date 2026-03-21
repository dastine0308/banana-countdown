import os
from roboflow import Roboflow
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Set an absolute path to your project's data folder
# This finds the directory this script is in, goes up to the root, then into data/yolo
root_dir = Path(__file__).resolve().parent.parent
data_dir = root_dir / "data" / "yolo"

print(f"Targeting directory: {data_dir}")

rf = Roboflow(api_key=os.getenv("ROBOFLOW_API_KEY"))
project = rf.workspace("fruit-ripening").project("banana-ripening-process")
version = project.version(2)

# Explicitly download to the data/yolo folder in your project root
dataset = version.download("yolov11", location=str(data_dir))

print(f"✅ Download complete! Look in: {data_dir}")