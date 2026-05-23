"""Ensure MediaPipe task models are available locally."""

from __future__ import annotations

import urllib.request
from pathlib import Path

MODEL_DIR = Path(__file__).resolve().parents[2] / "models"
FACE_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)


def ensure_face_landmarker() -> str:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    path = MODEL_DIR / "face_landmarker.task"
    if not path.exists():
        print(f"Downloading face landmarker model to {path}...")
        urllib.request.urlretrieve(FACE_LANDMARKER_URL, path)
    return str(path)
