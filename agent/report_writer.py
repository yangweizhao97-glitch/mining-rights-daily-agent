from __future__ import annotations

from typing import Any, Dict, List


def _bullet(text: str) -> str:
    return f"- {text}"


def _format_news(news: Dict[str, Any]) -> str:
    articles = news.get("articles") or news.get("items") or []
    if not articles:
        return "- 暂无可用新闻；请查看数据可靠性说明。"
    lines: List[str] = []
    for item in articles[:5]:
        title = item.get("title", "Untitled")
        url = item.get("url", "")
        source = item.get("source", "")
        snippet = item.get("summary") or item.get("snippet") or ""
        if url:
            lines.append(_bullet(f"[{title}]({url})（{source}）：{snippet}"))
        else:
            lines.append(_bullet(f"{title}（{source}）：{snippet}"))
    return "\n".join(lines)


def _format_resources(resources_payload: Dict[str, Any]) -> str:
    resources = resources_payload.get("resources", [])
    if not resources:
        return "- 未抽取到可靠储量数据；建议人工复核 PDF。"
    lines: List[str] = []
    for item in resources:
        lines.append(
            _bullet(
                "{category}: {ore_tonnage} {ore_unit}, grade {grade} {grade_unit}, metal {metal} {metal_unit} "
                "(page {page})".format(
                    category=item.get("category", "Unknown"),
                    ore_tonnage=item.get("ore_tonnage", "N/A"),
                    ore_unit=item.get("ore_tonnage_unit", ""),
                    grade=item.get("grade", "N/A"),
                    grade_unit=item.get("grade_unit", ""),
                    metal=item.get("metal_content", "N/A"),
                    metal_unit=item.get("metal_content_unit", ""),
                    page=item.get("page", "N/A"),
                )
            )
        )
    confidence = resources_payload.get("confidence")
    needs_review = resources_payload.get("needs_review")
    lines.append(_bullet(f"抽取置信度：{confidence}; needs_review={needs_review}"))
    return "\n".join(lines)


def _format_prices(prices: Dict[str, Any]) -> str:
    if not prices:
        return "- 暂无价格数据。"
    commodity = prices.get("commodity", "commodity")
    unit = prices.get("unit", "")
    currency = prices.get("currency", "")
    if "trend" not in prices:
        return "\n".join(
            [
                _bullet(f"{commodity}: {prices.get('date')} price={prices.get('price')} {currency}/{unit}"),
                _bullet(f"数据源：{prices.get('source', 'unknown')}"),
            ]
        )
    trend = prices.get("trend", {})
    return "\n".join(
        [
            _bullet(
                f"{commodity}: {trend.get('start_price')} -> {trend.get('end_price')} {currency}/{unit}, "
                f"change {trend.get('change_pct')}%, direction={trend.get('direction')}"
            ),
            _bullet(f"数据源：{prices.get('source', 'unknown')}"),
        ]
    )


def _format_risks(state: Dict[str, Any]) -> str:
    warnings = state.get("warnings", [])
    risks = [
        "锂价仍有波动风险，短期项目现金流对价格恢复敏感。",
        "PDF 抽取结果应结合原始报告页码复核，尤其是低置信度或 sample fallback 场景。",
        "政策与资金支持偏利好，但审批、物流和下游需求仍可能影响项目节奏。",
    ]
    if warnings:
        risks.append("本次运行存在 fallback 或警告，不能视为完整实时尽调结论。")
    return "\n".join(_bullet(item) for item in risks)


def _format_references(state: Dict[str, Any]) -> str:
    refs: List[str] = []
    news = state.get("news") or {}
    for item in news.get("articles", [])[:5]:
        if item.get("url"):
            refs.append(_bullet(f"{item.get('title', 'Article')}: {item['url']}"))
    resources = state.get("resources") or {}
    if resources.get("source_pdf"):
        refs.append(_bullet(f"Resource PDF: {resources['source_pdf']}"))
    prices = state.get("prices") or {}
    if prices.get("source"):
        refs.append(_bullet(f"Price source: {prices['source']}"))
    return "\n".join(refs) if refs else "- 暂无引用来源。"


def _format_reliability(state: Dict[str, Any]) -> str:
    lines: List[str] = []
    intent_name = (state.get("intent") or {}).get("intent", "daily_brief")
    if intent_name == "news_search":
        items = [("新闻数据", "news")]
    elif intent_name == "resource_extract":
        items = [("储量数据", "resources")]
    elif intent_name in {"price_query", "price_trend"}:
        items = [("价格数据", "prices")]
    else:
        items = [("新闻数据", "news"), ("储量数据", "resources"), ("价格数据", "prices")]

    for label, key in items:
        payload = state.get(key) or {}
        fallback = payload.get("fallback_used", False)
        warnings = "; ".join(payload.get("warnings", []) or [])
        extra = ""
        if key == "resources":
            extra = f"; confidence={payload.get('confidence')}; needs_review={payload.get('needs_review')}"
        lines.append(_bullet(f"{label}: fallback_used={fallback}{extra}. {warnings}".strip()))
    return "\n".join(lines)


def write_report(state: Dict[str, Any]) -> str:
    context = state.get("project_context") or {}
    target = context.get("target") or state.get("intent", {}).get("target") or "矿权项目"
    intent_name = (state.get("intent") or {}).get("intent", "daily_brief")

    if intent_name == "news_search":
        return "\n\n".join(
            [
                f"# {target} 新闻查询",
                "## 新闻摘要\n\n" + _format_news(state.get("news") or {}),
                "## 引用来源\n\n" + _format_references(state),
                "## 数据可靠性\n\n" + _format_reliability(state),
            ]
        )

    if intent_name == "resource_extract":
        return "\n\n".join(
            [
                f"# {target} 储量抽取",
                "## 储量数据\n\n" + _format_resources(state.get("resources") or {}),
                "## 引用来源\n\n" + _format_references(state),
                "## 数据可靠性\n\n" + _format_reliability(state),
            ]
        )

    if intent_name in {"price_query", "price_trend"}:
        heading = "价格查询" if intent_name == "price_query" else "价格走势"
        return "\n\n".join(
            [
                f"# {target} {heading}",
                f"## {heading}\n\n" + _format_prices(state.get("prices") or {}),
                "## 引用来源\n\n" + _format_references(state),
                "## 数据可靠性\n\n" + _format_reliability(state),
            ]
        )

    return "\n\n".join(
        [
            f"# {target} 今日简报",
            "## 1. 新闻摘要\n\n" + _format_news(state.get("news") or {}),
            "## 2. 储量数据\n\n" + _format_resources(state.get("resources") or {}),
            "## 3. 价格走势\n\n" + _format_prices(state.get("prices") or {}),
            "## 4. 风险提示\n\n" + _format_risks(state),
            "## 5. 引用来源\n\n" + _format_references(state),
            "## 6. 数据可靠性\n\n" + _format_reliability(state),
        ]
    )
