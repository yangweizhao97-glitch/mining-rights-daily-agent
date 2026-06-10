from __future__ import annotations

import re
from typing import Any, Dict


def _has_any(text: str, lowered: str, chinese_terms: list[str], english_terms: list[str]) -> bool:
    return any(term in text for term in chinese_terms) or any(term in lowered for term in english_terms)


def _extract_days(text: str, default: int = 7) -> int:
    match = re.search(r"(\d+)\s*(?:天|day|days)", text, re.IGNORECASE)
    if match:
        return max(1, int(match.group(1)))
    if "30" in text or "月" in text:
        return 30
    return default


def _extract_target(text: str) -> str:
    lowered = text.lower()
    if "pilbara" in lowered or "皮尔巴拉" in lowered:
        return "Pilbara lithium"
    if "barrick" in lowered:
        return "Barrick gold"
    if "锂" in text or "lithium" in lowered:
        return "Pilbara lithium"
    return "Pilbara lithium"


def _extract_commodity(text: str) -> str:
    lowered = text.lower()
    if "gold" in lowered or "黄金" in text or "金" in text:
        return "gold"
    if "copper" in lowered or "铜" in text:
        return "copper"
    if "nickel" in lowered or "镍" in text:
        return "nickel"
    if "zinc" in lowered or "锌" in text:
        return "zinc"
    if "lithium" in lowered or "锂" in text:
        return "lithium"
    return "lithium"


def _extract_pdf_url(text: str) -> str:
    match = re.search(r"(sample://[^\s\"'，。]+|https?://[^\s\"'，。]+|[^\s\"'，。]+\.pdf)", text)
    return match.group(1) if match else ""


def _extract_date(text: str) -> str:
    match = re.search(r"(20\d{2}-\d{1,2}-\d{1,2})", text)
    if not match:
        return ""
    year, month, day = match.group(1).split("-")
    return f"{year}-{int(month):02d}-{int(day):02d}"


def classify_intent(user_query: str) -> Dict[str, Any]:
    text = str(user_query or "").strip()
    lowered = text.lower()
    days = _extract_days(text)
    commodity = _extract_commodity(text)
    target = _extract_target(text)
    pdf_url = _extract_pdf_url(text)
    target_date = _extract_date(text)

    wants_brief = _has_any(text, lowered, ["日报", "简报", "今日"], ["brief"])
    wants_risk = _has_any(text, lowered, ["风险"], ["risk"])
    wants_resource = _has_any(text, lowered, ["储量", "资源量", "抽取"], ["ni 43-101", "inferred", "indicated", "resource"])
    wants_price = _has_any(text, lowered, ["价格", "走势", "涨跌", "锂价", "铜价", "镍价", "锌价"], ["price", "trend"])
    wants_news = _has_any(text, lowered, ["新闻", "发生", "消息", "资讯"], ["news", "article"])

    intent = "daily_brief"
    if wants_brief:
        intent = "daily_brief"
    elif wants_risk:
        intent = "risk_analysis"
    elif wants_resource:
        intent = "resource_extract"
    elif wants_price:
        intent = "price_trend"
    elif wants_news or "最近" in text:
        intent = "news_search"

    if target_date or "某天" in text or "date" in lowered:
        intent = "price_query"

    return {
        "intent": intent,
        "target": target,
        "commodity": commodity,
        "days": days,
        "date": target_date,
        "pdf_url": pdf_url,
        "need_news": intent in {"daily_brief", "news_search", "risk_analysis"},
        "need_resources": intent in {"daily_brief", "resource_extract", "risk_analysis"},
        "need_prices": intent in {"daily_brief", "price_query", "price_trend", "risk_analysis"},
        "confidence": 0.88,
    }
