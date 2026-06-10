from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _load_config() -> Dict[str, Any]:
    path = ROOT / "mcp-config.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_args(args: List[str]) -> List[str]:
    resolved: List[str] = []
    for arg in args:
        path = Path(arg)
        if path.is_absolute():
            if path.exists():
                resolved.append(str(path))
                continue
            for anchor in ("servers", "agent", "shared", "data"):
                if anchor in path.parts:
                    rel_parts = path.parts[path.parts.index(anchor) :]
                    candidate = ROOT.joinpath(*rel_parts)
                    if candidate.exists():
                        resolved.append(str(candidate))
                        break
            else:
                resolved.append(arg)
            continue
        candidate = ROOT / arg
        if candidate.exists():
            resolved.append(str(candidate))
        else:
            resolved.append(arg)
    return resolved


def _resolve_command(command: str) -> str:
    command_path = Path(command)
    if command_path.is_absolute() and not command_path.exists():
        return sys.executable
    return command


def _parse_tool_text(text: str) -> Dict[str, Any]:
    try:
        value = json.loads(text)
    except Exception:
        return {"ok": True, "text": text, "fallback_used": False, "warnings": []}
    if isinstance(value, dict):
        return value
    return {"ok": True, "data": value, "fallback_used": False, "warnings": []}


class MCPToolClient:
    def __init__(self) -> None:
        self.config = _load_config()

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except Exception as exc:
            raise RuntimeError(
                "mcp package is not installed. Run `pip install -r requirements.txt` from the project root."
            ) from exc

        servers = self.config.get("mcpServers", {})
        if server_name not in servers:
            raise ValueError(f"MCP server not found in config: {server_name}")
        spec = servers[server_name]
        env = os.environ.copy()
        env.update(spec.get("env", {}))
        env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")
        params = StdioServerParameters(
            command=_resolve_command(spec["command"]),
            args=_resolve_args(spec.get("args", [])),
            env=env,
        )

        with open(os.devnull, "w", encoding="utf-8") as errlog:
            async with stdio_client(params, errlog=errlog) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    result = await session.call_tool(tool_name, arguments)

        if getattr(result, "isError", False):
            return {
                "ok": False,
                "error": "MCP tool returned an error",
                "server": server_name,
                "tool": tool_name,
                "fallback_used": False,
                "warnings": [],
            }

        content = getattr(result, "content", []) or []
        if not content:
            return {"ok": True, "data": None, "fallback_used": False, "warnings": []}
        first = content[0]
        text = getattr(first, "text", None)
        if text is None:
            text = str(first)
        return _parse_tool_text(text)
