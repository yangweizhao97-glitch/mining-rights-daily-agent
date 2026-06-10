from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, List

from .utils import load_json, normalize_text


def _parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return date.today()


def search_articles(query: str, days: int = 7) -> Dict[str, Any]:
    query_text = normalize_text(query)
    days = max(1, int(days or 7))
    cutoff = date.today() - timedelta(days=days)
    records: List[Dict[str, Any]] = load_json("data/sample_articles.json")

    matches: List[Dict[str, Any]] = []
    for item in records:
        haystack = normalize_text(
            " ".join(
                [
                    item.get("title", ""),
                    item.get("source", ""),
                    item.get("snippet", ""),
                    item.get("body", ""),
                    " ".join(item.get("tags", [])),
                ]
            )
        )
        published_at = _parse_date(item.get("published_at", ""))
        if query_text and all(token not in haystack for token in query_text.split()):
            continue
        if published_at < cutoff and days <= 30:
            continue
        matches.append(
            {
                "title": item.get("title", ""),
                "source": item.get("source", ""),
                "published_at": item.get("published_at", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
            }
        )

    if not matches:
        matches = [
            {
                "title": item.get("title", ""),
                "source": item.get("source", ""),
                "published_at": item.get("published_at", ""),
                "url": item.get("url", ""),
                "snippet": item.get("snippet", ""),
            }
            for item in records[:5]
        ]

    return {
        "ok": True,
        "query": query,
        "days": days,
        "items": matches[:10],
        "fallback_used": True,
        "warnings": ["sample article data used; live news fetch is not enabled in this demo"],
    }


def fetch_article(url: str) -> Dict[str, Any]:
    records: List[Dict[str, Any]] = load_json("data/sample_articles.json")
    for item in records:
        if item.get("url") == url:
            return {
                "ok": True,
                "title": item.get("title", ""),
                "source": item.get("source", ""),
                "published_at": item.get("published_at", ""),
                "url": item.get("url", ""),
                "summary": item.get("snippet", ""),
                "content": item.get("body", ""),
                "fallback_used": True,
                "warnings": ["sample article body used"],
            }

    return {
        "ok": False,
        "url": url,
        "error": "article not found in sample data",
        "fallback_used": True,
        "warnings": ["only sample article URLs are available in this demo"],
    }

