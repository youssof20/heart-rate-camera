#!/usr/bin/env python3
"""Live rPPG heart-rate demo with OpenCV HUD."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rppg.capture import WebcamCapture
from rppg.config import load_config
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
        "--reference-bpm",
        type=float,
        default=None,
        help="Pulse ox or manual reference BPM (shows live error)",
    )
    parser.add_argument(
        "--signal-method",
        choices=["chrom", "green"],
        default=None,
        help="Override config signal_method",
    )
    parser.add_argument(
        "--events-log",
        type=Path,
        default=None,
        help="Optional path to append stress-test event markers",
    )
    args = parser.parse_args()

    config = load_config()
    if args.signal_method:
        config["signal_method"] = args.signal_method

    cam = WebcamCapture(device_index=args.camera, mirror=not args.no_mirror)
    pipeline = PulsePipeline(config)
    events_log = args.events_log
    method = config.get("signal_method", "chrom")

    print(f"Signal: {method} | Controls: q=quit m/b/o/d/t events")
    if args.reference_bpm:
        print(f"Reference BPM: {args.reference_bpm}")

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
                reference_bpm=args.reference_bpm,
                signal_method=state.signal_method,
                snr=state.snr,
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
