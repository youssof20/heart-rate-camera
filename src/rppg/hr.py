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
    snr: float = 0.0


def _magnitude_at_hz(band_freqs: np.ndarray, band_spectrum: np.ndarray, hz: float) -> float:
    idx = int(np.argmin(np.abs(band_freqs - hz)))
    return float(band_spectrum[idx])


def _resolve_harmonic_peak(
    peak_hz: float,
    peak_mag: float,
    band_freqs: np.ndarray,
    band_spectrum: np.ndarray,
    low_hz: float,
    high_hz: float,
    harmonic_ratio: float = 0.5,
) -> tuple[float, float]:
    """Prefer fundamental over 2x harmonic when half-frequency peak is strong."""
    half_hz = peak_hz / 2.0
    if half_hz < low_hz:
        return peak_hz, peak_mag

    half_mag = _magnitude_at_hz(band_freqs, band_spectrum, half_hz)
    if half_mag > harmonic_ratio * peak_mag:
        return half_hz, half_mag

    double_hz = peak_hz * 2.0
    if double_hz <= high_hz:
        double_mag = _magnitude_at_hz(band_freqs, band_spectrum, double_hz)
        if peak_mag < harmonic_ratio * double_mag:
            return double_hz, double_mag

    return peak_hz, peak_mag


def estimate_bpm(
    pulse_signal: np.ndarray,
    fps: float,
    low_hz: float = 0.75,
    high_hz: float = 2.5,
    order: int = 4,
    snr_threshold: float = 1.8,
    trend_window_seconds: float = 1.5,
    harmonic_ratio: float = 0.5,
) -> HrEstimate:
    if len(pulse_signal) < int(fps * 4):
        return HrEstimate(
            bpm=None,
            confidence=0.0,
            filtered_signal=np.array([]),
            dominant_hz=None,
            snr=0.0,
        )

    detrended = detrend(pulse_signal, fps, trend_window_seconds)
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
            snr=0.0,
        )

    band_freqs = freqs[band_mask]
    band_spectrum = spectrum[band_mask]
    peak_idx = int(np.argmax(band_spectrum))
    peak_mag = float(band_spectrum[peak_idx])
    peak_hz = float(band_freqs[peak_idx])

    peak_hz, peak_mag = _resolve_harmonic_peak(
        peak_hz, peak_mag, band_freqs, band_spectrum, low_hz, high_hz, harmonic_ratio
    )

    median_mag = float(np.median(band_spectrum)) + 1e-9
    snr = peak_mag / median_mag
    confidence = min(1.0, snr / (snr_threshold * 2))

    if snr < snr_threshold:
        return HrEstimate(
            bpm=None,
            confidence=confidence,
            filtered_signal=filtered,
            dominant_hz=peak_hz,
            snr=snr,
        )

    bpm = peak_hz * 60.0
    return HrEstimate(
        bpm=float(bpm),
        confidence=confidence,
        filtered_signal=filtered,
        dominant_hz=float(peak_hz),
        snr=snr,
    )
