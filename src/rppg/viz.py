"""Visualization helpers for live display."""

from __future__ import annotations

import cv2
import numpy as np


def draw_roi(frame: np.ndarray, polygon: np.ndarray | None, color=(0, 255, 128)) -> None:
    if polygon is None:
        return
    pts = polygon.astype(np.int32).reshape((-1, 1, 2))
    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)


def draw_hud(
    frame: np.ndarray,
    bpm: float | None,
    status: str,
    confidence: float,
    waveform: np.ndarray | None = None,
    waveform_height: int = 120,
) -> None:
    h, w = frame.shape[:2]
    bar_y = h - waveform_height

    # Waveform panel background
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, bar_y), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

    if waveform is not None and len(waveform) > 2:
        wf = waveform.astype(np.float64)
        wf = wf - np.mean(wf)
        std = np.std(wf) + 1e-9
        wf = wf / std
        wf = np.clip(wf, -3, 3)

        n = len(wf)
        xs = np.linspace(0, w - 1, n).astype(int)
        mid = bar_y + waveform_height // 2
        scale = waveform_height * 0.35

        points = [(int(xs[i]), int(mid - wf[i] * scale)) for i in range(n)]
        for i in range(1, len(points)):
            cv2.line(frame, points[i - 1], points[i], (0, 220, 255), 2)

    # BPM text
    if bpm is not None:
        bpm_text = f"{bpm:.0f} BPM"
        color = (0, 255, 128)
    else:
        bpm_text = "-- BPM"
        color = (180, 180, 180)

    cv2.putText(frame, bpm_text, (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 2.0, color, 4, cv2.LINE_AA)
    cv2.putText(
        frame,
        status,
        (20, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (200, 200, 200),
        2,
        cv2.LINE_AA,
    )
    conf_text = f"conf {confidence:.0%}" if confidence > 0 else ""
    if conf_text:
        cv2.putText(
            frame,
            conf_text,
            (20, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (160, 160, 160),
            1,
            cv2.LINE_AA,
        )
