from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from shared.news_core import fetch_article as fetch_article_core
from shared.news_core import search_articles
from shared.utils import json_response


mcp = FastMCP("mining-news-mcp")


@mcp.tool()
def search(query: str, days: int = 7) -> str:
    """Search recent mining news by query and day range."""
    return json_response(search_articles(query=query, days=days))


@mcp.tool()
def fetch_article(url: str) -> str:
    """Fetch a mining news article by URL."""
    return json_response(fetch_article_core(url=url))


if __name__ == "__main__":
    mcp.run()

