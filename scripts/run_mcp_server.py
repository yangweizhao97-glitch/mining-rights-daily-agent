from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _venv_python() -> Path:
    if os.name == "nt":
        return ROOT / ".venv" / "Scripts" / "python.exe"
    return ROOT / ".venv" / "bin" / "python"


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_mcp_server.py <server_script.py>", file=sys.stderr)
        return 2

    server_script = Path(sys.argv[1])
    if not server_script.is_absolute():
        server_script = ROOT / server_script
    if not server_script.exists():
        print(f"MCP server script not found: {server_script}", file=sys.stderr)
        return 2

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    venv_python = _venv_python()
    current = Path(sys.executable).resolve()
    if venv_python.exists() and venv_python.resolve() != current:
        os.execve(str(venv_python), [str(venv_python), str(server_script), *sys.argv[2:]], env)

    if sys.version_info < (3, 10):
        print("Python 3.10+ is required. Create .venv with Python 3.11 first.", file=sys.stderr)
        return 1

    os.environ.update(env)
    sys.argv = [str(server_script), *sys.argv[2:]]
    runpy.run_path(str(server_script), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
