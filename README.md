# MCP Mining Rights Daily Agent

This project implements task #2: a 24-hour MCP-based "mining rights daily brief" Agent.

The goal is verification first:

1. `mcp-config.json` can be imported into Cursor / Claude Desktop.
2. Three MCP servers expose the required tools.
3. A lightweight LangGraph Agent calls the MCP tools and generates a Markdown daily brief.
4. Sample fallback data keeps the demo stable when live sources are unavailable.

## Quick Start From GitHub

Use `mining-rights-daily-agent` as the repository root. After cloning, the fastest verification path is Docker:

```bash
git clone <your-repo-url>
cd mining-rights-daily-agent
docker compose up --build
```

This should print a LangGraph trace and a Markdown daily brief. Docker does not require a local virtual environment or a prior `pip install`.

## Demo Data Notice

This repository is configured for interview demonstration and MCP workflow verification. It uses sample fallback data from `data/` by default. Reports and tool responses explicitly include `fallback_used`, `warnings`, `confidence`, and `needs_review` where relevant.

The sample data is not live market, regulatory, or investment due-diligence data. A production deployment should replace it with real news APIs, real NI 43-101 / technical report PDF sources, and real LME / SHFE / commodity price APIs.

## Architecture

```text
User query
  -> parse_input
  -> classify_intent
  -> resolve_project_context
  -> route_tools
  -> collect_news
  -> collect_resources
  -> collect_prices
  -> write_report
  -> quality_check
  -> final_output
```

The Agent uses LangGraph as a lightweight state machine. It does not implement complex multi-agent review loops.

## MCP Servers

| Server | Tools | Purpose |
| --- | --- | --- |
| `mining-news-mcp` | `search(query, days)`, `fetch_article(url)` | Mining news search and article fetch |
| `mineral-pdf-mcp` | `extract_resources(pdf_url)` | Extract Indicated / Inferred resources |
| `lme-price-mcp` | `get_price(commodity, date)`, `get_trend(commodity, days)` | Price and trend lookup |

## Project Registry

`data/project_registry.json` maps natural-language targets to:

- `target`
- `commodity`
- `news_query`
- `default_pdf_url`

This lets the sample prompt work even though the user does not provide a PDF URL:

```text
给我生成一份关于 Pilbara 锂矿的今日简报
```

## Run From Project Root

All commands should be run from the directory that contains:

```text
mcp-config.json
agent/
servers/
```

Example:

```bash
cd mining-rights-daily-agent
```

## Local Run

Python 3.10+ is required because the MCP Python SDK requires Python 3.10 or newer. Python 3.11 is recommended.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python agent/main.py "给我生成一份关于 Pilbara 锂矿的今日简报"
```

If the default PyPI connection is slow:

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

## Smoke Test

```bash
python scripts/smoke_test.py
```

## Docker

```bash
docker compose up --build
```

## Cursor / Claude Desktop

Import root `mcp-config.json`.

The MCP config is portable by default:

```text
python3 scripts/run_mcp_server.py servers/<server>.py
```

`scripts/run_mcp_server.py` uses only the Python standard library. It first looks for the project virtual environment:

```text
.venv/bin/python
```

or on Windows:

```text
.venv\Scripts\python.exe
```

If `python3` is not available on another machine, change the `command` field in `mcp-config.json` and `.cursor/mcp.json` to the local Python launcher, such as `python` or `py`.

## Data Reliability

This demo uses sample fallback data by design. Tool responses and reports include:

- `fallback_used`
- `warnings`
- resource `confidence`
- resource `needs_review`

Sample fallback is not presented as live market or live regulatory data.

## Known Limits

- Live news crawling is not enabled in this first version.
- Lithium price uses sample fallback under `lme-price-mcp`.
- PDF extraction supports sample URLs and basic local PDF text extraction.
- No CriticMaster / Revise Loop is implemented; that belongs to task #3, not this task.
