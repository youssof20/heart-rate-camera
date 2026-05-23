"""Webcam capture with timestamps."""

from __future__ import annotations

import time
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass
class FramePacket:
    frame: np.ndarray
    timestamp: float


class WebcamCapture:
    def __init__(self, device_index: int = 0, mirror: bool = True, width: int = 640, height: int = 480):
        self.device_index = device_index
        self.mirror = mirror
        self.width = width
        self.height = height
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> None:
        self._cap = cv2.VideoCapture(self.device_index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open camera index {self.device_index}")
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def read(self) -> FramePacket | None:
        if self._cap is None:
            raise RuntimeError("Camera not opened")
        ok, frame = self._cap.read()
        if not ok:
            return None
        if self.mirror:
            frame = cv2.flip(frame, 1)
        return FramePacket(frame=frame, timestamp=time.perf_counter())

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
