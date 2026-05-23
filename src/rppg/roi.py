"""Forehead ROI extraction via MediaPipe Face Landmarker."""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from rppg.config import load_config
from rppg.models import ensure_face_landmarker


@dataclass
class RoiResult:
    polygon: np.ndarray | None
    mask: np.ndarray | None
    detected: bool
    confidence: float = 0.0


class ForeheadRoiExtractor:
    """Extract forehead polygon and binary mask from face landmarks."""

    def __init__(self, config: dict | None = None):
        self.config = config or load_config()
        self.landmark_indices = self.config["forehead_landmark_indices"]
        self.min_confidence = float(self.config.get("min_face_confidence", 0.5))
        self.ema_alpha = float(self.config.get("roi_ema_alpha", 0.3))
        self._smoothed_polygon: np.ndarray | None = None

        base_options = python.BaseOptions(model_asset_path=ensure_face_landmarker())
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=self.min_confidence,
            min_face_presence_confidence=self.min_confidence,
            min_tracking_confidence=self.min_confidence,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)

    def process(self, frame_bgr: np.ndarray) -> RoiResult:
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_image)

        if not result.face_landmarks:
            self._smoothed_polygon = None
            return RoiResult(polygon=None, mask=None, detected=False, confidence=0.0)

        landmarks = result.face_landmarks[0]
        points = []
        for idx in self.landmark_indices:
            if idx >= len(landmarks):
                continue
            lm = landmarks[idx]
            points.append([lm.x * w, lm.y * h])

        if len(points) < 3:
            return RoiResult(polygon=None, mask=None, detected=False, confidence=0.0)

        polygon = np.array(points, dtype=np.float32)
        hull = cv2.convexHull(polygon.astype(np.int32)).reshape(-1, 2).astype(np.float32)

        if self._smoothed_polygon is None or self._smoothed_polygon.shape != hull.shape:
            self._smoothed_polygon = hull.copy()
        else:
            self._smoothed_polygon = (
                self.ema_alpha * hull + (1.0 - self.ema_alpha) * self._smoothed_polygon
            )

        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillConvexPoly(mask, self._smoothed_polygon.astype(np.int32), 255)

        return RoiResult(
            polygon=self._smoothed_polygon,
            mask=mask,
            detected=True,
            confidence=1.0,
        )

    def close(self) -> None:
        self._landmarker.close()
