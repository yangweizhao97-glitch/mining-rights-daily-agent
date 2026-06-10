from __future__ import annotations

import asyncio
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
warnings.showwarning = lambda *args, **kwargs: None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.graph import run_agent
from agent.mcp_client import MCPToolClient


async def main() -> int:
    client = MCPToolClient()
    checks = [
        ("mining-news-mcp", "search", {"query": "Pilbara lithium", "days": 7}),
        ("mineral-pdf-mcp", "extract_resources", {"pdf_url": "sample://pilbara-ni-43-101.pdf"}),
        ("lme-price-mcp", "get_trend", {"commodity": "lithium", "days": 30}),
    ]
    for server, tool, args in checks:
        result = await client.call_tool(server, tool, args)
        if not result.get("ok"):
            print(f"FAIL {server}.{tool}: {result}")
            return 1
        print(f"PASS {server}.{tool}")

    state = await run_agent("给我生成一份关于 Pilbara 锂矿的今日简报")
    report = state.get("report") or ""
    required = ["## 1. 新闻摘要", "## 2. 储量数据", "## 3. 价格走势", "## 4. 风险提示", "## 5. 引用来源", "## 6. 数据可靠性"]
    missing = [item for item in required if item not in report]
    if missing:
        print(f"FAIL agent report missing sections: {missing}")
        return 1
    print("PASS agent daily brief")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
