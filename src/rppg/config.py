"""Load shared pipeline configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "pipeline.json"


def load_config(path: Path | str | None = None) -> dict[str, Any]:
    config_path = Path(path) if path else _DEFAULT_CONFIG_PATH
    with config_path.open(encoding="utf-8") as f:
        return json.load(f)
