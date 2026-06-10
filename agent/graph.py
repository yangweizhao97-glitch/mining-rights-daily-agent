from __future__ import annotations

import asyncio
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.intent import classify_intent as classify_user_intent
from agent.mcp_client import MCPToolClient
from agent.report_writer import write_report as render_report
from shared.news_core import fetch_article as direct_fetch_article
from shared.news_core import search_articles as direct_search_articles
from shared.pdf_core import extract_resources as direct_extract_resources
from shared.price_core import get_price as direct_get_price
from shared.price_core import get_trend as direct_get_trend
from shared.utils import load_json, normalize_text

warnings.filterwarnings("ignore")
warnings.showwarning = lambda *args, **kwargs: None


class AgentState(TypedDict, total=False):
    user_query: str
    intent: Dict[str, Any]
    project_context: Dict[str, Any]
    tool_plan: List[str]
    news: Optional[Dict[str, Any]]
    resources: Optional[Dict[str, Any]]
    prices: Optional[Dict[str, Any]]
    report: Optional[str]
    warnings: List[str]
    trace: List[str]


def _append(state: AgentState, key: str, value: str) -> List[str]:
    items = list(state.get(key, []))
    items.append(value)
    return items


def _find_project_context(intent: Dict[str, Any]) -> Dict[str, Any]:
    registry: Dict[str, Any] = load_json("data/project_registry.json")
    target = normalize_text(intent.get("target", ""))
    for key, value in registry.items():
        if normalize_text(key) in target or target in normalize_text(key):
            return dict(value)
    if "pilbara" in target or "lithium" in target:
        return dict(registry["pilbara lithium"])
    return {
        "target": intent.get("target", "Pilbara lithium project"),
        "commodity": intent.get("commodity", "lithium"),
        "news_query": intent.get("target", "Pilbara lithium"),
        "default_pdf_url": intent.get("pdf_url") or "sample://pilbara-ni-43-101.pdf",
    }


async def parse_input(state: AgentState) -> AgentState:
    query = str(state.get("user_query", "")).strip()
    return {
        "user_query": query,
        "warnings": [],
        "trace": [f"parse_input user_query={query}"],
    }


async def classify_intent(state: AgentState) -> AgentState:
    intent = classify_user_intent(state["user_query"])
    return {
        "intent": intent,
        "trace": _append(
            state,
            "trace",
            "classify_intent intent={intent} target={target} commodity={commodity} days={days}".format(
                intent=intent["intent"],
                target=intent.get("target"),
                commodity=intent.get("commodity"),
                days=intent.get("days"),
            ),
        ),
    }


async def resolve_project_context(state: AgentState) -> AgentState:
    context = _find_project_context(state.get("intent", {}))
    intent_pdf = state.get("intent", {}).get("pdf_url")
    if intent_pdf:
        context["default_pdf_url"] = intent_pdf
    return {
        "project_context": context,
        "trace": _append(
            state,
            "trace",
            "resolve_project_context target={target} commodity={commodity} pdf={pdf}".format(
                target=context.get("target"),
                commodity=context.get("commodity"),
                pdf=context.get("default_pdf_url"),
            ),
        ),
    }


async def route_tools(state: AgentState) -> AgentState:
    intent_name = state.get("intent", {}).get("intent", "daily_brief")
    routes = {
        "daily_brief": ["search", "fetch_article", "extract_resources", "get_trend"],
        "news_search": ["search", "fetch_article"],
        "resource_extract": ["extract_resources"],
        "price_query": ["get_price"],
        "price_trend": ["get_trend"],
        "risk_analysis": ["search", "extract_resources", "get_trend"],
    }
    tool_plan = routes.get(intent_name, [])
    if not tool_plan:
        return {
            "tool_plan": [],
            "warnings": _append(state, "warnings", "unknown intent; no tool plan generated"),
            "trace": _append(state, "trace", "route_tools unknown intent"),
        }
    return {
        "tool_plan": tool_plan,
        "trace": _append(state, "trace", f"route_tools tools={tool_plan}"),
    }


async def collect_news(state: AgentState) -> AgentState:
    if "search" not in state.get("tool_plan", []):
        return {}
    client = MCPToolClient()
    context = state.get("project_context", {})
    days = int(state.get("intent", {}).get("days", 7))
    query = context.get("news_query") or state.get("intent", {}).get("target", "")
    search_result = await client.call_tool("mining-news-mcp", "search", {"query": query, "days": days})
    articles: List[Dict[str, Any]] = []
    for item in search_result.get("items", [])[:3]:
        if "fetch_article" in state.get("tool_plan", []) and item.get("url"):
            fetched = await client.call_tool("mining-news-mcp", "fetch_article", {"url": item["url"]})
            articles.append(fetched if fetched.get("ok") else item)
        else:
            articles.append(item)
    payload = dict(search_result)
    payload["articles"] = articles
    warnings = list(state.get("warnings", [])) + list(payload.get("warnings", []))
    return {
        "news": payload,
        "warnings": warnings,
        "trace": _append(state, "trace", f"collect_news count={len(articles)} fallback={payload.get('fallback_used')}"),
    }


async def collect_resources(state: AgentState) -> AgentState:
    if "extract_resources" not in state.get("tool_plan", []):
        return {}
    client = MCPToolClient()
    context = state.get("project_context", {})
    pdf_url = context.get("default_pdf_url") or state.get("intent", {}).get("pdf_url") or "sample://pilbara-ni-43-101.pdf"
    payload = await client.call_tool("mineral-pdf-mcp", "extract_resources", {"pdf_url": pdf_url})
    warnings = list(state.get("warnings", [])) + list(payload.get("warnings", []))
    return {
        "resources": payload,
        "warnings": warnings,
        "trace": _append(
            state,
            "trace",
            "collect_resources rows={rows} confidence={confidence} fallback={fallback}".format(
                rows=len(payload.get("resources", [])),
                confidence=payload.get("confidence"),
                fallback=payload.get("fallback_used"),
            ),
        ),
    }


async def collect_prices(state: AgentState) -> AgentState:
    if not any(tool in state.get("tool_plan", []) for tool in ["get_price", "get_trend"]):
        return {}
    client = MCPToolClient()
    context = state.get("project_context", {})
    commodity = context.get("commodity") or state.get("intent", {}).get("commodity", "lithium")
    if "get_price" in state.get("tool_plan", []):
        payload = await client.call_tool(
            "lme-price-mcp",
            "get_price",
            {"commodity": commodity, "date": state.get("intent", {}).get("date", "")},
        )
    else:
        days = int(state.get("intent", {}).get("days", 30))
        payload = await client.call_tool("lme-price-mcp", "get_trend", {"commodity": commodity, "days": days})
    warnings = list(state.get("warnings", [])) + list(payload.get("warnings", []))
    return {
        "prices": payload,
        "warnings": warnings,
        "trace": _append(state, "trace", f"collect_prices commodity={commodity} fallback={payload.get('fallback_used')}"),
    }


async def write_report(state: AgentState) -> AgentState:
    report = render_report(state)
    return {
        "report": report,
        "trace": _append(state, "trace", f"write_report chars={len(report)}"),
    }


async def quality_check(state: AgentState) -> AgentState:
    report = state.get("report") or ""
    intent_name = state.get("intent", {}).get("intent", "daily_brief")
    if intent_name == "news_search":
        required = ["## 新闻摘要", "## 引用来源", "## 数据可靠性"]
    elif intent_name == "resource_extract":
        required = ["## 储量数据", "## 引用来源", "## 数据可靠性"]
    elif intent_name == "price_query":
        required = ["## 价格查询", "## 引用来源", "## 数据可靠性"]
    elif intent_name == "price_trend":
        required = ["## 价格走势", "## 引用来源", "## 数据可靠性"]
    else:
        required = ["## 1. 新闻摘要", "## 2. 储量数据", "## 3. 价格走势", "## 4. 风险提示", "## 5. 引用来源", "## 6. 数据可靠性"]
    missing = [item for item in required if item not in report]
    warnings = list(state.get("warnings", []))
    if missing:
        warnings.append("report missing sections: " + ", ".join(missing))
    return {
        "warnings": warnings,
        "trace": _append(state, "trace", "quality_check passed" if not missing else f"quality_check missing={missing}"),
    }


async def final_output(state: AgentState) -> AgentState:
    return {
        "trace": _append(state, "trace", "final_output ready"),
    }


def _build_graph():
    from langgraph.graph import END, StateGraph

    graph = StateGraph(AgentState)
    graph.add_node("parse_input", parse_input)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("resolve_project_context", resolve_project_context)
    graph.add_node("route_tools", route_tools)
    graph.add_node("collect_news", collect_news)
    graph.add_node("collect_resources", collect_resources)
    graph.add_node("collect_prices", collect_prices)
    graph.add_node("write_report", write_report)
    graph.add_node("quality_check", quality_check)
    graph.add_node("final_output", final_output)

    graph.set_entry_point("parse_input")
    graph.add_edge("parse_input", "classify_intent")
    graph.add_edge("classify_intent", "resolve_project_context")
    graph.add_edge("resolve_project_context", "route_tools")
    graph.add_edge("route_tools", "collect_news")
    graph.add_edge("collect_news", "collect_resources")
    graph.add_edge("collect_resources", "collect_prices")
    graph.add_edge("collect_prices", "write_report")
    graph.add_edge("write_report", "quality_check")
    graph.add_edge("quality_check", "final_output")
    graph.add_edge("final_output", END)
    return graph.compile()


async def run_langgraph(user_query: str) -> AgentState:
    app = _build_graph()
    return await app.ainvoke({"user_query": user_query})


async def run_simple_workflow(user_query: str, reason: str) -> AgentState:
    intent = classify_user_intent(user_query)
    context = _find_project_context(intent)
    news = direct_search_articles(context.get("news_query", intent.get("target", "")), intent.get("days", 7))
    articles = [direct_fetch_article(item["url"]) for item in news.get("items", [])[:3] if item.get("url")]
    news["articles"] = articles
    resources = direct_extract_resources(intent.get("pdf_url") or context.get("default_pdf_url", "sample://pilbara-ni-43-101.pdf"))
    prices = direct_get_price(context.get("commodity", "lithium")) if intent.get("intent") == "price_query" else direct_get_trend(context.get("commodity", "lithium"), 30)
    state: AgentState = {
        "user_query": user_query,
        "intent": intent,
        "project_context": context,
        "tool_plan": ["simple_workflow_fallback"],
        "news": news,
        "resources": resources,
        "prices": prices,
        "warnings": [f"LangGraph fallback used: {reason}"],
        "trace": ["simple_workflow fallback", f"reason={reason}"],
    }
    state["report"] = render_report(state)
    return state


async def run_agent(user_query: str) -> AgentState:
    try:
        return await run_langgraph(user_query)
    except Exception as exc:
        if os.environ.get("AGENT_ALLOW_SIMPLE_FALLBACK") != "1":
            raise
        return await run_simple_workflow(user_query, str(exc))


def run_agent_sync(user_query: str) -> AgentState:
    return asyncio.run(run_agent(user_query))
