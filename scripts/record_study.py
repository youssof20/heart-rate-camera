#!/usr/bin/env python3
"""Record a structured study session with ground-truth metadata."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rppg.capture import WebcamCapture
from rppg.pipeline import PulsePipeline
from rppg.session import SessionMetadata, SessionRecorder
from rppg.signal import extract_green_mean
from rppg.viz import draw_hud, draw_roi

EVENT_KEYS = {
    ord("m"): "motion",
    ord("b"): "breath_hold",
    ord("o"): "occlusion",
    ord("d"): "dark",
    ord("t"): "torch",
}


def prompt_metadata(args: argparse.Namespace) -> SessionMetadata:
    subject_id = args.subject_id or input("Subject ID: ").strip()
    fitzpatrick = args.fitzpatrick or input("Fitzpatrick (I-VI): ").strip().upper()
    reference_bpm = args.reference_bpm
    if reference_bpm is None:
        reference_bpm = float(input("Reference BPM (oximeter or manual): "))
    reference_source = args.reference_source or input("Reference source (oximeter/manual): ").strip().lower()
    lighting = args.lighting or input("Lighting (normal/dim/bright_torch) [normal]: ").strip() or "normal"
    notes = args.notes or input("Notes (optional): ").strip()
    return SessionMetadata(
        subject_id=subject_id,
        fitzpatrick=fitzpatrick,
        reference_bpm=reference_bpm,
        reference_source=reference_source,
        lighting=lighting,
        notes=notes,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Record rPPG study session")
    parser.add_argument("--subject-id", default=None)
    parser.add_argument("--fitzpatrick", default=None)
    parser.add_argument("--reference-bpm", type=float, default=None)
    parser.add_argument("--reference-source", default=None, choices=["oximeter", "manual"])
    parser.add_argument("--lighting", default=None)
    parser.add_argument("--notes", default="")
    parser.add_argument("--duration", type=float, default=60.0, help="Recording seconds")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "sessions",
    )
    args = parser.parse_args()

    metadata = prompt_metadata(args)
    recorder = SessionRecorder(metadata=metadata, output_dir=args.output_dir)
    cam = WebcamCapture(device_index=args.camera)
    pipeline = PulsePipeline()

    print(f"Recording {args.duration}s to {recorder.csv_path}")
    print("Press q to stop early. Event keys: m b o d t")

    cv2 = __import__("cv2")
    start = None

    try:
        cam.open()
        while True:
            packet = cam.read()
            if packet is None:
                continue
            if start is None:
                start = packet.timestamp

            state = pipeline.process_frame(packet.frame, packet.timestamp)
            green = 0.0
            if state.roi and state.roi.mask is not None:
                gm = extract_green_mean(packet.frame, state.roi.mask)
                green = gm if gm is not None else 0.0

            recorder.write_row(
                timestamp=packet.timestamp,
                green_mean=green,
                bpm_est=state.bpm_display,
                face_detected=state.face_detected,
            )

            frame = packet.frame.copy()
            if state.roi:
                draw_roi(frame, state.roi.polygon)
            draw_hud(
                frame,
                bpm=state.bpm_display,
                status=state.status,
                confidence=state.confidence,
                waveform=state.filtered_signal if len(state.filtered_signal) else None,
                reference_bpm=metadata.reference_bpm,
                signal_method=state.signal_method,
                snr=state.snr,
            )
            elapsed = packet.timestamp - start
            cv2.putText(
                frame,
                f"REC {elapsed:.0f}/{args.duration:.0f}s",
                (20, frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )
            cv2.imshow("Study Recording", frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q") or elapsed >= args.duration:
                break
            if key in EVENT_KEYS:
                tag = EVENT_KEYS[key]
                recorder.log_event(packet.timestamp, tag)
                recorder.write_row(
                    packet.timestamp, green, state.bpm_display, state.face_detected, event=tag
                )
    finally:
        recorder.close()
        pipeline.close()
        cam.release()
        cv2.destroyAllWindows()
        print(f"Saved: {recorder.csv_path}")
        print(f"Metadata: {recorder.json_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
