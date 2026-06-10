from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from .utils import load_json, normalize_text


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return date.today()


def _commodity_key(commodity: str) -> str:
    text = normalize_text(commodity)
    aliases = {
        "li": "lithium",
        "lithium carbonate": "lithium",
        "锂": "lithium",
        "锂价": "lithium",
        "cu": "copper",
        "铜": "copper",
        "ni": "nickel",
        "镍": "nickel",
        "zn": "zinc",
        "锌": "zinc",
        "gold": "gold",
        "黄金": "gold",
    }
    return aliases.get(text, text or "lithium")


def _load_series(commodity: str) -> Dict[str, Any]:
    data: Dict[str, Any] = load_json("data/sample_prices.json")
    key = _commodity_key(commodity)
    if key not in data:
        key = "lithium"
    payload = dict(data[key])
    payload["commodity"] = key
    return payload


def get_price(commodity: str, target_date: Optional[str] = None) -> Dict[str, Any]:
    series = _load_series(commodity)
    target = _parse_date(target_date) if target_date else _parse_date(series["points"][-1]["date"])
    points = sorted(series["points"], key=lambda x: x["date"])
    selected = points[-1]
    for point in points:
        if _parse_date(point["date"]) <= target:
            selected = point

    return {
        "ok": True,
        "commodity": series["commodity"],
        "date": selected["date"],
        "price": selected["price"],
        "currency": series.get("currency", "USD"),
        "unit": series.get("unit", "t"),
        "source": series.get("source", "sample"),
        "fallback_used": True,
        "warnings": [f"sample {series['commodity']} price data used"],
    }


def get_trend(commodity: str, days: int = 30) -> Dict[str, Any]:
    series = _load_series(commodity)
    days = max(1, int(days or 30))
    points = sorted(series["points"], key=lambda x: x["date"])
    latest = _parse_date(points[-1]["date"])
    cutoff = latest - timedelta(days=days)
    filtered = [p for p in points if _parse_date(p["date"]) >= cutoff]
    if len(filtered) < 2:
        filtered = points[-min(len(points), 2) :]

    start_price = float(filtered[0]["price"])
    end_price = float(filtered[-1]["price"])
    change_pct = round(((end_price - start_price) / start_price) * 100, 2) if start_price else 0.0
    direction = "up" if change_pct > 0 else "down" if change_pct < 0 else "flat"

    return {
        "ok": True,
        "commodity": series["commodity"],
        "currency": series.get("currency", "USD"),
        "unit": series.get("unit", "t"),
        "points": filtered,
        "trend": {
            "start_price": start_price,
            "end_price": end_price,
            "change_pct": change_pct,
            "direction": direction,
        },
        "source": series.get("source", "sample"),
        "fallback_used": True,
        "warnings": [f"sample {series['commodity']} price data used"],
    }

