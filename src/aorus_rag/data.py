from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def default_spec_path() -> Path:
    return project_root() / "data" / "aorus_master_16_am6h_specs.json"


def load_spec(path: str | Path | None = None) -> dict[str, Any]:
    spec_path = Path(path) if path else default_spec_path()
    with spec_path.open("r", encoding="utf-8") as f:
        return json.load(f)
