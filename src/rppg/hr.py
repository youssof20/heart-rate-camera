"""Heart rate estimation via FFT."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from rppg.filter import bandpass
from rppg.signal import detrend


@dataclass
class HrEstimate:
    bpm: float | None
    confidence: float
    filtered_signal: np.ndarray
    dominant_hz: float | None


def estimate_bpm(
    green_values: np.ndarray,
    fps: float,
    low_hz: float = 0.75,
    high_hz: float = 2.5,
    order: int = 4,
    snr_threshold: float = 1.8,
    trend_window_seconds: float = 1.5,
) -> HrEstimate:
    if len(green_values) < int(fps * 4):
        return HrEstimate(
            bpm=None,
            confidence=0.0,
            filtered_signal=np.array([]),
            dominant_hz=None,
        )

    detrended = detrend(green_values, fps, trend_window_seconds)
    filtered = bandpass(detrended, fps, low_hz, high_hz, order)

    n = len(filtered)
    freqs = np.fft.rfftfreq(n, d=1.0 / fps)
    spectrum = np.abs(np.fft.rfft(filtered))

    band_mask = (freqs >= low_hz) & (freqs <= high_hz)
    if not np.any(band_mask):
        return HrEstimate(
            bpm=None,
            confidence=0.0,
            filtered_signal=filtered,
            dominant_hz=None,
        )

    band_freqs = freqs[band_mask]
    band_spectrum = spectrum[band_mask]
    peak_idx = int(np.argmax(band_spectrum))
    peak_mag = band_spectrum[peak_idx]
    peak_hz = band_freqs[peak_idx]

    # SNR: peak vs median of band
    median_mag = float(np.median(band_spectrum)) + 1e-9
    snr = float(peak_mag / median_mag)
    confidence = min(1.0, snr / (snr_threshold * 2))

    if snr < snr_threshold:
        return HrEstimate(
            bpm=None,
            confidence=confidence,
            filtered_signal=filtered,
            dominant_hz=peak_hz,
        )

    bpm = peak_hz * 60.0
    return HrEstimate(
        bpm=float(bpm),
        confidence=confidence,
        filtered_signal=filtered,
        dominant_hz=float(peak_hz),
    )
