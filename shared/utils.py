from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"


def load_json(relative_path: str) -> Any:
    path = PROJECT_ROOT / relative_path
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def json_response(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2)


def normalize_text(value: str) -> str:
    return " ".join(str(value or "").strip().lower().split())


def is_sample_url(value: str) -> bool:
    return str(value or "").startswith("sample://")

