"""End-to-end pulse processing pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from rppg.config import load_config
from rppg.hr import HrEstimate, estimate_bpm
from rppg.roi import ForeheadRoiExtractor, RoiResult
from rppg.signal import SignalBuffer, SignalSample, extract_green_mean


@dataclass
class PipelineState:
    bpm: float | None = None
    bpm_display: float | None = None
    confidence: float = 0.0
    face_detected: bool = False
    ready: bool = False
    status: str = "Settling..."
    filtered_signal: np.ndarray = field(default_factory=lambda: np.array([]))
    roi: RoiResult | None = None


class PulsePipeline:
    def __init__(self, config: dict | None = None):
        self.config = config or load_config()
        self.buffer = SignalBuffer(self.config["buffer_seconds"])
        self.roi_extractor = ForeheadRoiExtractor(self.config)
        self._bpm_smooth_alpha = float(self.config["bpm_smooth_alpha"])
        self._warmup_seconds = float(self.config["warmup_seconds"])
        self._bpm_display: float | None = None

    def process_frame(self, frame_bgr: np.ndarray, timestamp: float) -> PipelineState:
        roi = self.roi_extractor.process(frame_bgr)
        green_mean = None
        if roi.detected and roi.mask is not None:
            green_mean = extract_green_mean(frame_bgr, roi.mask)

        face_ok = roi.detected and green_mean is not None
        self.buffer.add(
            SignalSample(
                timestamp=timestamp,
                green_mean=green_mean if green_mean is not None else 0.0,
                face_detected=face_ok,
            )
        )

        state = PipelineState(
            face_detected=face_ok,
            roi=roi,
            ready=self.buffer.duration >= self._warmup_seconds and face_ok,
        )

        if not face_ok:
            state.status = "Face not detected"
            return state

        if not state.ready:
            state.status = "Settling..."
            return state

        ts, greens = self.buffer.green_series()
        if len(greens) < int(self.buffer.estimate_fps() * 4):
            state.status = "Settling..."
            return state

        fps = self.buffer.estimate_fps()
        hr = estimate_bpm(
            greens,
            fps,
            low_hz=self.config["bandpass_low_hz"],
            high_hz=self.config["bandpass_high_hz"],
            order=self.config["bandpass_order"],
            snr_threshold=self.config["snr_threshold"],
            trend_window_seconds=self.config["trend_window_seconds"],
        )

        state.filtered_signal = hr.filtered_signal
        state.confidence = hr.confidence

        if hr.bpm is not None:
            state.bpm = hr.bpm
            if self._bpm_display is None:
                self._bpm_display = hr.bpm
            else:
                a = self._bpm_smooth_alpha
                self._bpm_display = a * hr.bpm + (1.0 - a) * self._bpm_display
            state.bpm_display = self._bpm_display
            state.status = "Measuring"
        else:
            state.bpm_display = self._bpm_display
            state.status = "Low signal"

        return state

    def close(self) -> None:
        self.roi_extractor.close()
