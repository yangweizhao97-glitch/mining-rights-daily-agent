from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
warnings.showwarning = lambda *args, **kwargs: None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.graph import run_agent_sync


def main() -> int:
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        query = "给我生成一份关于 Pilbara 锂矿的今日简报"
    state = run_agent_sync(query)
    print("TRACE")
    for item in state.get("trace", []):
        print(f"- {item}")
    if state.get("warnings"):
        print("\nWARNINGS")
        for item in state["warnings"]:
            print(f"- {item}")
    print("\n" + (state.get("report") or ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
