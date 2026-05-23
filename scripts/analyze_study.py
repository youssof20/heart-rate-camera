#!/usr/bin/env python3
"""Analyze recorded study sessions: MAE/RMSE by Fitzpatrick group."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def load_session_pairs(sessions_dir: Path) -> list[dict]:
    rows = []
    for json_path in sessions_dir.glob("*.json"):
        meta = json.loads(json_path.read_text(encoding="utf-8"))
        csv_path = Path(meta.get("csv_path", ""))
        if not csv_path.exists():
            # Try same stem
            csv_path = json_path.with_suffix(".csv")
        if not csv_path.exists():
            continue

        bpms = []
        with csv_path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("bpm_est") and row.get("face_detected") == "1":
                    try:
                        bpms.append(float(row["bpm_est"]))
                    except ValueError:
                        pass

        if len(bpms) < 10:
            continue

        # Use median of last 30s worth (~ half the samples if 30fps)
        tail_n = max(10, len(bpms) // 2)
        est_median = float(np.median(bpms[-tail_n:]))
        ref = float(meta["reference_bpm"])
        err = est_median - ref

        rows.append(
            {
                "subject_id": meta["subject_id"],
                "fitzpatrick": meta["fitzpatrick"],
                "lighting": meta.get("lighting", "normal"),
                "reference_source": meta.get("reference_source", ""),
                "reference_bpm": ref,
                "estimated_bpm": est_median,
                "error": err,
                "abs_error": abs(err),
                "squared_error": err**2,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze rPPG study sessions")
    parser.add_argument(
        "--sessions-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "sessions",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "reports",
    )
    args = parser.parse_args()

    if not args.sessions_dir.exists():
        print(f"No sessions directory: {args.sessions_dir}")
        return 1

    sessions = load_session_pairs(args.sessions_dir)
    if not sessions:
        print("No valid sessions found. Record data with scripts/record_study.py first.")
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Per-session summary CSV
    summary_path = args.output_dir / "summary.csv"
    fieldnames = list(sessions[0].keys())
    with summary_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sessions)

    # Aggregate by Fitzpatrick
    groups: dict[str, list[float]] = {}
    for s in sessions:
        groups.setdefault(s["fitzpatrick"], []).append(s["abs_error"])

    print("\n=== Accuracy by Fitzpatrick ===")
    for fitz, errors in sorted(groups.items()):
        mae = float(np.mean(errors))
        rmse = float(np.sqrt(np.mean([e**2 for e in errors])))
        print(f"  {fitz}: n={len(errors)}  MAE={mae:.1f} BPM  RMSE={rmse:.1f} BPM")

    overall_mae = float(np.mean([s["abs_error"] for s in sessions]))
    overall_rmse = float(np.sqrt(np.mean([s["squared_error"] for s in sessions])))
    print(f"\nOverall: n={len(sessions)}  MAE={overall_mae:.1f}  RMSE={overall_rmse:.1f}")

    # Boxplot
    labels = sorted(groups.keys())
    data = [groups[l] for l in labels]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.boxplot(data, labels=labels)
    ax.set_xlabel("Fitzpatrick scale")
    ax.set_ylabel("Absolute error (BPM)")
    ax.set_title("rPPG absolute error by skin tone")
    ax.axhline(overall_mae, color="red", linestyle="--", label=f"Overall MAE {overall_mae:.1f}")
    ax.legend()
    fig.tight_layout()
    plot_path = args.output_dir / "accuracy_by_skin_tone.png"
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)
    print(f"\nWrote {summary_path}")
    print(f"Wrote {plot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
