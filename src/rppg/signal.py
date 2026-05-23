"""rPPG signal extraction and buffering."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np

from rppg.chrom import chrom_pulse_signal


@dataclass
class SignalSample:
    timestamp: float
    r_mean: float
    g_mean: float
    b_mean: float
    face_detected: bool

    @property
    def green_mean(self) -> float:
        return self.g_mean


class SignalBuffer:
    """Rolling buffer of RGB spatial means with timestamp-based FPS."""

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

    def _face_samples(self) -> list[SignalSample]:
        return [s for s in self._samples if s.face_detected]

    def rgb_series(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Return (timestamps, r, g, b) for face-detected samples."""
        samples = self._face_samples()
        if not samples:
            return np.array([]), np.array([]), np.array([]), np.array([])

        ts = np.array([s.timestamp for s in samples], dtype=np.float64)
        r = np.array([s.r_mean for s in samples], dtype=np.float64)
        g = np.array([s.g_mean for s in samples], dtype=np.float64)
        b = np.array([s.b_mean for s in samples], dtype=np.float64)
        return ts, r, g, b

    def green_series(self) -> tuple[np.ndarray, np.ndarray]:
        ts, r, g, b = self.rgb_series()
        return ts, g

    def pulse_series(self, method: str = "chrom") -> tuple[np.ndarray, np.ndarray]:
        """Return (timestamps, pulse waveform) using green or CHROM."""
        ts, r, g, b = self.rgb_series()
        if len(g) == 0:
            return ts, np.array([])

        if method == "green":
            pulse = g.astype(np.float64)
        elif method == "chrom":
            pulse = chrom_pulse_signal(r, g, b)
        else:
            raise ValueError(f"Unknown signal_method: {method}")

        return ts, pulse

    def estimate_fps(self) -> float:
        ts, _ = self.green_series()
        if len(ts) < 2:
            return 30.0
        duration = ts[-1] - ts[0]
        if duration <= 0:
            return 30.0
        return (len(ts) - 1) / duration


def extract_rgb_means(frame_bgr: np.ndarray, mask: np.ndarray | None) -> tuple[float, float, float] | None:
    if mask is None:
        return None
    b_ch, g_ch, r_ch = frame_bgr[:, :, 0], frame_bgr[:, :, 1], frame_bgr[:, :, 2]
    roi = mask > 0
    if not np.any(roi):
        return None
    return (
        float(np.mean(r_ch[roi])),
        float(np.mean(g_ch[roi])),
        float(np.mean(b_ch[roi])),
    )


def extract_green_mean(frame_bgr: np.ndarray, mask: np.ndarray | None) -> float | None:
    rgb = extract_rgb_means(frame_bgr, mask)
    return rgb[1] if rgb else None


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
