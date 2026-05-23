"""Study session recording."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class SessionMetadata:
    subject_id: str
    fitzpatrick: str
    reference_bpm: float
    reference_source: str  # oximeter | manual
    lighting: str = "normal"
    notes: str = ""
    started_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class SessionRecorder:
    metadata: SessionMetadata
    output_dir: Path

    def __post_init__(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = f"{self.metadata.subject_id}_{stamp}"
        self.csv_path = self.output_dir / f"{base}.csv"
        self.json_path = self.output_dir / f"{base}.json"
        self._csv_file = self.csv_path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(
            self._csv_file,
            fieldnames=["t_sec", "green_mean", "bpm_est", "face_detected", "event"],
        )
        self._writer.writeheader()
        self._start_time: float | None = None
        self._events: list[dict] = []

    def write_row(
        self,
        timestamp: float,
        green_mean: float,
        bpm_est: float | None,
        face_detected: bool,
        event: str = "",
    ) -> None:
        if self._start_time is None:
            self._start_time = timestamp
        t_sec = timestamp - self._start_time
        self._writer.writerow(
            {
                "t_sec": f"{t_sec:.3f}",
                "green_mean": f"{green_mean:.4f}",
                "bpm_est": f"{bpm_est:.2f}" if bpm_est is not None else "",
                "face_detected": int(face_detected),
                "event": event,
            }
        )
        self._csv_file.flush()

    def log_event(self, timestamp: float, tag: str) -> None:
        if self._start_time is None:
            self._start_time = timestamp
        self._events.append({"t_sec": timestamp - self._start_time, "tag": tag})

    def close(self) -> None:
        self._csv_file.close()
        meta = asdict(self.metadata)
        meta["events"] = self._events
        meta["csv_path"] = str(self.csv_path)
        self.json_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
