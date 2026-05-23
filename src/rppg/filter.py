"""Bandpass filtering for pulse band."""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt


def bandpass(
    signal: np.ndarray,
    fps: float,
    low_hz: float = 0.75,
    high_hz: float = 2.5,
    order: int = 4,
) -> np.ndarray:
    if len(signal) < order * 3:
        return signal.copy()

    nyquist = fps / 2.0
    if high_hz >= nyquist:
        high_hz = nyquist * 0.95
    if low_hz <= 0:
        low_hz = 0.01

    b, a = butter(order, [low_hz / nyquist, high_hz / nyquist], btype="band")
    return filtfilt(b, a, signal)
