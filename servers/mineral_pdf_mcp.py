from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mcp.server.fastmcp import FastMCP

from shared.pdf_core import extract_resources as extract_resources_core
from shared.utils import json_response


mcp = FastMCP("mineral-pdf-mcp")


@mcp.tool()
def extract_resources(pdf_url: str) -> str:
    """Extract Indicated and Inferred resource rows from a NI 43-101-style PDF."""
    return json_response(extract_resources_core(pdf_url=pdf_url))


if __name__ == "__main__":
    mcp.run()

