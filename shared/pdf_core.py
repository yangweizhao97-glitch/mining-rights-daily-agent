from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from .utils import PROJECT_ROOT, is_sample_url, load_json, normalize_text


def _score_confidence(resources: List[Dict[str, Any]]) -> float:
    if not resources:
        return 0.0
    score = 0.55
    categories = {normalize_text(item.get("category", "")) for item in resources}
    if "indicated" in categories:
        score += 0.15
    if "inferred" in categories:
        score += 0.15
    complete_rows = 0
    for item in resources:
        required = ["ore_tonnage", "ore_tonnage_unit", "grade", "grade_unit", "metal_content", "metal_content_unit"]
        if all(item.get(k) not in (None, "") for k in required):
            complete_rows += 1
    score += min(0.15, complete_rows * 0.05)
    return round(min(score, 0.95), 2)


def _extract_from_text(text: str, source_pdf: str) -> Dict[str, Any]:
    resources: List[Dict[str, Any]] = []
    patterns = [
        r"(Indicated|Inferred)\D+([\d.]+)\s*Mt\D+([\d.]+)\s*(% Li2O|% Cu|g/t Au)\D+([\d.]+)\s*([A-Za-z0-9/% ]+)",
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            resources.append(
                {
                    "category": match.group(1).title(),
                    "ore_tonnage": float(match.group(2)),
                    "ore_tonnage_unit": "Mt",
                    "grade": float(match.group(3)),
                    "grade_unit": match.group(4),
                    "metal_content": float(match.group(5)),
                    "metal_content_unit": match.group(6).strip(),
                    "page": None,
                    "source_excerpt": match.group(0)[:300],
                }
            )

    confidence = _score_confidence(resources)
    return {
        "ok": True,
        "project": "Unknown project",
        "source_pdf": source_pdf,
        "resources": resources,
        "confidence": confidence,
        "needs_review": confidence < 0.8,
        "fallback_used": False,
        "warnings": [] if resources else ["no Indicated/Inferred resource rows found"],
    }


def _read_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n".join(pages)
    except Exception as exc:
        raise RuntimeError(f"failed to read PDF text: {exc}") from exc


def extract_resources(pdf_url: str) -> Dict[str, Any]:
    sample_map: Dict[str, Any] = load_json("data/sample_resources.json")
    if is_sample_url(pdf_url):
        payload = dict(sample_map.get(pdf_url, {}))
        if payload:
            payload.setdefault("ok", True)
            payload.setdefault("source_pdf", pdf_url)
            payload.setdefault("fallback_used", True)
            payload.setdefault("warnings", ["sample resource data used"])
            return payload

    path = Path(str(pdf_url)).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if path.exists() and path.suffix.lower() == ".pdf":
        extracted = _extract_from_text(_read_pdf_text(path), str(path))
        return extracted

    return {
        "ok": False,
        "project": "Unknown project",
        "source_pdf": pdf_url,
        "resources": [],
        "confidence": 0.0,
        "needs_review": True,
        "fallback_used": False,
        "warnings": ["PDF URL is not available; use sample://pilbara-ni-43-101.pdf for the demo"],
        "error": "unsupported or unavailable PDF source",
    }

