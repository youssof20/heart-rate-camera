#!/usr/bin/env python3
"""Live rPPG heart-rate demo with OpenCV HUD."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Setup path before rppg imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rppg.capture import WebcamCapture
from rppg.pipeline import PulsePipeline
from rppg.viz import draw_hud, draw_roi

EVENT_KEYS = {
    ord("m"): "motion",
    ord("b"): "breath_hold",
    ord("o"): "occlusion",
    ord("d"): "dark",
    ord("t"): "torch",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Live rPPG heart rate from webcam")
    parser.add_argument("--camera", type=int, default=0, help="Camera device index")
    parser.add_argument("--no-mirror", action="store_true", help="Disable horizontal flip")
    parser.add_argument(
        "--events-log",
        type=Path,
        default=None,
        help="Optional path to append stress-test event markers",
    )
    args = parser.parse_args()

    cam = WebcamCapture(device_index=args.camera, mirror=not args.no_mirror)
    pipeline = PulsePipeline()
    events_log = args.events_log

    print("Controls: q=quit | m=motion b=breath-hold o=occlusion d=dark t=torch")

    try:
        cam.open()
        while True:
            packet = cam.read()
            if packet is None:
                continue

            state = pipeline.process_frame(packet.frame, packet.timestamp)
            frame = packet.frame.copy()

            if state.roi is not None:
                draw_roi(frame, state.roi.polygon)

            waveform = state.filtered_signal if len(state.filtered_signal) > 0 else None
            draw_hud(
                frame,
                bpm=state.bpm_display,
                status=state.status,
                confidence=state.confidence,
                waveform=waveform,
            )

            cv2 = __import__("cv2")
            cv2.imshow("rPPG Heart Rate", frame)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break
            if key in EVENT_KEYS:
                tag = EVENT_KEYS[key]
                t = time.perf_counter()
                print(f"[event] {tag} @ {t:.2f}")
                if events_log:
                    events_log.parent.mkdir(parents=True, exist_ok=True)
                    with events_log.open("a", encoding="utf-8") as f:
                        f.write(f"{t:.3f},{tag}\n")

    except KeyboardInterrupt:
        pass
    finally:
        pipeline.close()
        cam.release()
        __import__("cv2").destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
