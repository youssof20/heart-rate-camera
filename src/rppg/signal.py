"""rPPG signal extraction and buffering."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

import numpy as np


@dataclass
class SignalSample:
    timestamp: float
    green_mean: float
    face_detected: bool


class SignalBuffer:
    """Rolling buffer of green-channel means with timestamp-based FPS."""

    def __init__(self, buffer_seconds: float = 18.0):
        self.buffer_seconds = buffer_seconds
        self._samples: deque[SignalSample] = deque()

    def add(self, sample: SignalSample) -> None:
        self._samples.append(sample)
        cutoff = sample.timestamp - self.buffer_seconds
        while self._samples and self._samples[0].timestamp < cutoff:
            self._samples.popleft()

    def __len__(self) -> int:
        return len(self._samples)

    @property
    def duration(self) -> float:
        if len(self._samples) < 2:
            return 0.0
        return self._samples[-1].timestamp - self._samples[0].timestamp

    def green_series(self) -> tuple[np.ndarray, np.ndarray]:
        """Return (timestamps, green_values) for detected-face samples only."""
        if not self._samples:
            return np.array([]), np.array([])

        ts = []
        vals = []
        for s in self._samples:
            if s.face_detected:
                ts.append(s.timestamp)
                vals.append(s.green_mean)
        return np.asarray(ts, dtype=np.float64), np.asarray(vals, dtype=np.float64)

    def estimate_fps(self) -> float:
        ts, _ = self.green_series()
        if len(ts) < 2:
            return 30.0
        duration = ts[-1] - ts[0]
        if duration <= 0:
            return 30.0
        return (len(ts) - 1) / duration


def extract_green_mean(frame_bgr: np.ndarray, mask: np.ndarray | None) -> float | None:
    if mask is None:
        return None
    green = frame_bgr[:, :, 1]
    roi_pixels = green[mask > 0]
    if roi_pixels.size == 0:
        return None
    return float(np.mean(roi_pixels))


def detrend(signal: np.ndarray, fps: float, window_seconds: float = 1.5) -> np.ndarray:
    if len(signal) < 3:
        return signal.copy()
    window = max(3, int(fps * window_seconds))
    if window % 2 == 0:
        window += 1
    if window >= len(signal):
        window = len(signal) - 1 if len(signal) % 2 == 0 else len(signal)
        if window < 3:
            return signal - np.mean(signal)
    kernel = np.ones(window) / window
    trend = np.convolve(signal, kernel, mode="same")
    return signal - trend
