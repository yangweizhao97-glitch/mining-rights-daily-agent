from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from shared.price_core import get_price as get_price_core
from shared.price_core import get_trend as get_trend_core
from shared.utils import json_response


mcp = FastMCP("lme-price-mcp")


@mcp.tool()
def get_price(commodity: str, date: str = "") -> str:
    """Get the price for a commodity on or before a given date."""
    return json_response(get_price_core(commodity=commodity, target_date=date or None))


@mcp.tool()
def get_trend(commodity: str, days: int = 30) -> str:
    """Get a recent commodity price trend."""
    return json_response(get_trend_core(commodity=commodity, days=days))


if __name__ == "__main__":
    mcp.run()

