# 运行说明

这份文档用于快速验证“矿权日报 Agent”项目。建议按顺序执行：先本地运行，再 Docker 运行，最后在 Cursor 里验证 MCP 工具。

## GitHub 下载后最快运行

建议把 `mining-rights-daily-agent` 作为 GitHub 仓库根目录推送。别人下载或 clone 后，目录里应直接看到：

```text
mcp-config.json
agent/
servers/
RUN.md
Dockerfile
docker-compose.yml
```

Docker 是最稳的 5 分钟验收路径，不要求对方本机安装 Python 依赖：

```bash
git clone <your-repo-url>
cd mining-rights-daily-agent
docker compose up --build
```

正常输出会包含 LangGraph trace 和 Markdown 日报。如果 trace 里没有出现 `simple_workflow fallback`，说明 Docker 里走通了 LangGraph + MCP 主流程。

如果对方是下载 ZIP，也只需要解压后进入项目根目录再执行：

```bash
docker compose up --build
```

## 演示数据说明

当前项目用于面试演示和 MCP 流程验证，默认使用 `data/` 目录下的 sample fallback 数据：

- 新闻：`data/sample_articles.json`
- PDF 储量：`data/sample_resources.json` 和 `sample://pilbara-ni-43-101.pdf`
- 价格：`data/sample_prices.json`

工具返回和日报中都会标记 `fallback_used`、`warnings`、`confidence`、`needs_review`。这些 sample 数据不能视为实时市场数据或正式投资尽调结论。

生产环境需要替换为真实 API / 数据源，例如：

- 真实新闻源或新闻搜索 API。
- 真实 NI 43-101 / 技术报告 PDF 下载与解析服务。
- 真实 LME、SHFE、价格供应商或内部行情 API。

## 0. 从项目根目录打开

请先进入项目根目录，也就是包含 `mcp-config.json`、`agent/`、`servers/` 的目录：

```bash
cd mining-rights-daily-agent
```

如果你在 Cursor 里打开项目，也要直接打开这个目录：

```text
mining-rights-daily-agent
```

不要只打开外层作品集目录，否则 Cursor 可能找不到 `.cursor/mcp.json`。

## 1. 本地 Python 运行

本项目需要 Python 3.10 或更高版本，推荐 Python 3.11。

创建虚拟环境：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell 示例：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```bash
pip install -r requirements.txt
```

如果默认 PyPI 下载很慢，可以使用清华镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn
```

运行默认日报：

```bash
python agent/main.py "给我生成一份关于 Pilbara 锂矿的今日简报"
```

正常输出会包含 LangGraph trace：

```text
parse_input
classify_intent
resolve_project_context
route_tools
collect_news
collect_resources
collect_prices
write_report
quality_check
final_output
```

并生成一份 Markdown 日报，包含：

- `## 1. 新闻摘要`
- `## 2. 储量数据`
- `## 3. 价格走势`
- `## 4. 风险提示`
- `## 5. 引用来源`
- `## 6. 数据可靠性`

## 2. 快速自检

运行 smoke test：

```bash
python scripts/smoke_test.py
```

看到下面输出就说明本地 MCP 工具和 Agent 都能跑通：

```text
PASS mining-news-mcp.search
PASS mineral-pdf-mcp.extract_resources
PASS lme-price-mcp.get_trend
PASS agent daily brief
```

## 3. 单独测试 Agent 能力

生成完整日报：

```bash
python agent/main.py "给我生成一份关于 Pilbara 锂矿的今日简报"
```

只查新闻：

```bash
python agent/main.py "帮我查一下 Pilbara 最近 7 天相关新闻"
```

只查价格：

```bash
python agent/main.py "锂价最近 30 天趋势怎么样"
```

只抽取 PDF 储量：

```bash
python agent/main.py "从 sample://pilbara-ni-43-101.pdf 里抽取 Indicated 和 Inferred Resources"
```

## 4. Docker 运行

确保 Docker Desktop 已启动，然后在项目根目录运行：

```bash
docker compose up --build
```

第一次构建会下载 `python:3.11-slim` 和 Python 依赖，可能较慢。第二次以后会使用缓存，速度会快很多。

正常输出会包含完整 trace 和 Markdown 日报。如果 trace 里没有出现 `simple_workflow fallback`，说明 Docker 里也走通了 LangGraph + MCP 主流程。

Docker 运行不依赖本机 `.venv`，也不需要先执行 `pip install`。仓库里的 `.dockerignore` 已排除 `.venv`、`__pycache__` 等本地生成文件。

## 5. Cursor MCP 验证

当前项目的 MCP 配置是跨机器版本，不写死本机绝对路径。配置会先用系统 `python3` 启动：

```text
scripts/run_mcp_server.py
```

这个 wrapper 会自动寻找当前项目下的 `.venv`：

```text
.venv/bin/python
```

或 Windows：

```text
.venv\Scripts\python.exe
```

因此别人在自己的电脑上测试时，只需要先按第 1 步创建 `.venv` 并安装依赖，再打开 Cursor 验证即可。

Cursor 可以读取项目里的：

```text
.cursor/mcp.json
```

也可以手动导入根目录的：

```text
mcp-config.json
```

在 Cursor 中打开：

```text
Settings -> Tools & MCPs
```

确认能看到并启用这 3 个 MCP server：

- `mining-news-mcp`
- `mineral-pdf-mcp`
- `lme-price-mcp`

然后在 Cursor Agent 输入框中依次测试：

```text
请调用 mineral-pdf-mcp.extract_resources，参数 pdf_url=sample://pilbara-ni-43-101.pdf
```

```text
请调用 lme-price-mcp.get_trend，参数 commodity=lithium, days=30
```

```text
请调用 mining-news-mcp.search，参数 query=Pilbara lithium mining, days=7
```

如果 Cursor 弹出工具调用确认，点击 `Run`。如果希望后续少弹确认，可以点击 `Allowlist MCP Tool`。

如果对方电脑上 `python3` 命令不可用，可以把 `mcp-config.json` 和 `.cursor/mcp.json` 里的 `"command": "python3"` 改成：

```text
python
```

或 Windows 常见的：

```text
py
```

## 6. 一句话生成日报

三个 MCP 工具验证通过后，可以直接在 Cursor Agent 输入：

```text
给我生成一份关于 Pilbara 锂矿的今日简报
```

更稳定的演示输入是：

```text
请基于当前项目的 MCP 工具，生成一份关于 Pilbara 锂矿的今日简报。请依次调用 mining-news-mcp.search、mineral-pdf-mcp.extract_resources、lme-price-mcp.get_trend，然后输出 Markdown 报告。
```

演示时建议主动说明：当前结果来自 sample fallback 数据，用于验证 MCP server、Agent 编排和 Markdown 输出链路；生产版本需要接入真实新闻、PDF 和价格 API。

## 7. MCP 配置说明

根目录的 `mcp-config.json` 是主交付文件，`.cursor/mcp.json` 是 Cursor 项目级兼容配置。两者都使用同一套 portable 写法：

```json
"command": "python3",
"args": ["scripts/run_mcp_server.py", "servers/mining_news_mcp.py"]
```

`scripts/run_mcp_server.py` 只依赖 Python 标准库，会自动切换到项目内 `.venv` 后再启动 MCP server。这样项目移动目录或复制到其他电脑后，通常不需要改绝对路径。

如果 MCP server 启动失败，优先检查：

- 是否已经创建 `.venv`。
- 是否已经执行 `pip install -r requirements.txt`。
- 当前电脑是否能运行 `python3 --version`。
- 如果没有 `python3`，把配置里的 `command` 改成当前系统可用的 Python 命令。

## 8. 数据可靠性说明

当前版本为了保证面试演示稳定，默认启用了 sample fallback 数据：

- 新闻：示例新闻数据
- PDF：`sample://pilbara-ni-43-101.pdf`
- 价格：示例锂价趋势

工具返回和日报中都会明确标记：

- `fallback_used`
- `warnings`
- `confidence`
- `needs_review`

这些示例数据用于流程验证和格式展示，不能当作真实投资尽调结论。正式环境可以替换为真实新闻源、真实 PDF 报告和真实价格 API。

## 9. 常见问题

如果 Cursor 看不到 MCP server：

- 确认打开的是 `mining-rights-daily-agent` 项目根目录。
- 确认 `.cursor/mcp.json` 存在。
- 确认 `.venv/bin/python` 存在。
- 重启 Cursor 或在 Tools & MCPs 里重新启用 server。

如果 MCP server 启动失败：

- 先在终端运行：

```bash
source .venv/bin/activate
python scripts/smoke_test.py
```

- 如果 smoke test 失败，重新安装依赖：

```bash
pip install -r requirements.txt
```

- 如果报错显示找不到 `python3`，把 `mcp-config.json` 和 `.cursor/mcp.json` 里的 `"command": "python3"` 改成你电脑可用的 Python 命令，例如 `"python"`。

如果 Docker 第一次构建很慢：

- 属于正常现象，主要是在下载基础镜像和 Python 依赖。
- 构建成功后第二次会明显变快。
