"""CHROM rPPG (de Haan & Jeanne, 2013)."""

from __future__ import annotations

import numpy as np


def chrom_pulse_signal(r: np.ndarray, g: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Build CHROM pulse waveform from per-frame RGB spatial means."""
    r = np.asarray(r, dtype=np.float64)
    g = np.asarray(g, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)

    if len(r) < 3:
        return g - np.mean(g) if len(g) else np.array([])

    r_m = float(np.mean(r))
    g_m = float(np.mean(g))
    b_m = float(np.mean(b))
    if min(r_m, g_m, b_m) < 1e-6:
        return g - np.mean(g)

    rn = r / r_m
    gn = g / g_m
    bn = b / b_m

    xs = 3.0 * rn - 2.0 * gn
    ys = 1.5 * rn + gn - 1.5 * bn

    std_xs = float(np.std(xs))
    std_ys = float(np.std(ys))
    alpha = std_xs / std_ys if std_ys > 1e-9 else 0.0

    return xs - alpha * ys
