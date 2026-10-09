\# 矿权日报 Agent (Mining Daily Brief Agent)



基于 \*\*MCP (Model Context Protocol)\*\* 协议构建的多 Server 协同 Agent。通过 LangGraph 编排 3 个本地 MCP Server，实现新闻聚合、NI 43-101 储量 PDF 解析与大宗商品价格行情的一站式日报生成。



\## 🏗️ 架构设计



\- \*\*Agent Client\*\*：采用 `LangGraph` + `LangChain ReAct` 架构，自主决定工具调用顺序。

\- \*\*MCP Servers\*\*（共 3 个）：

&#x20; 1. `mining-news-mcp`：提供 `search(query, days)` 与 `fetch\_article(url)`。

&#x20; 2. `mineral-pdf-mcp`：提供 `extract\_resources(pdf\_url)`，解析 NI 43-101 储量数据。

&#x20; 3. `lme-price-mcp`：提供 `get\_price(commodity, date)` 与 `get\_trend(commodity, days)`。

\- \*\*大模型\*\*：本地 Ollama `qwen3:8b`（已适配，无需付费 API Key）。

\- \*\*部署与验证\*\*：Docker + Docker Compose 一键启动，MCP Inspector 独立验证。



\## 📋 前置要求



在开始之前，请确保宿主机已安装：



1\. \*\*Docker Desktop\*\*：已启动并显示 `Engine running`。

2\. \*\*Ollama\*\*：用于本地大模型推理。

&#x20;  - 拉取模型（首次需执行，约 5GB）：

&#x20;    ```bash

&#x20;    ollama pull qwen3:8b

&#x20;    ```

&#x20;  - 确保 Ollama 服务允许 Docker 容器访问（设置环境变量 `OLLAMA\_HOST=0.0.0.0`，并放行防火墙 11434 端口）。

3\. \*\*Node.js\*\*（仅 MCP Inspector 验证时需要）：\[下载地址](https://nodejs.org/)（LTS 版本）。



\## 🚀 快速启动（一条命令跑起来）



在项目根目录下，确保终端已进入 `mining-daily-agent`，执行唯一需要的命令：



```bash

docker-compose up --build

```



\*\*预期表现\*\*：

1\. Docker 拉取 Python 3.12 基础镜像并安装依赖。

2\. 启动 3 个 MCP Server 容器 + 1 个 Agent 容器。

3\. Agent 自动调用 Ollama 推理，按流程调用 MCP 工具。

4\. 终端输出 `简报已生成，保存至 output/pilbara\_daily\_brief.md`，并且 `exited with code 0`。



\## 📁 查看生成结果



运行完成后，在项目 `output/` 目录下即可看到：

\- `pilbara\_daily\_brief.md` — 完整的 Markdown 格式矿权日报（含新闻摘要、储量数据、价格走势与风险提示）。



\## 🔌 MCP Server 独立验证（MCP Inspector）



除了 Agent 整体运行，本项目 3 个 Server 均可通过官方 \*\*MCP Inspector\*\* 独立接入验证（无需 LLM 环境）。



在终端执行（以 `lme-price-mcp` 为例）：



```bash

npx @modelcontextprotocol/inspector C:/Users/10747/Desktop/mining-daily-agent/.venv/Scripts/python.exe C:/Users/10747/Desktop/mining-daily-agent/servers/lme\_price\_mcp.py

```



浏览器会自动打开 `http://127.0.0.1:6274`，在 `Tools` 标签页中即可查看工具列表（`get\_price`、`get\_trend`），手动填入参数并点击 `Run Tool` 即可验证返回的 JSON 数据。



另外两个 Server 的验证命令：



```bash

npx @modelcontextprotocol/inspector C:/Users/10747/Desktop/mining-daily-agent/.venv/Scripts/python.exe C:/Users/10747/Desktop/mining-daily-agent/servers/mining\_news\_mcp.py

npx @modelcontextprotocol/inspector C:/Users/10747/Desktop/mining-daily-agent/.venv/Scripts/python.exe C:/Users/10747/Desktop/mining-daily-agent/servers/mineral\_pdf\_mcp.py

```



> \*\*提示\*\*：`npx` 在国内网络下可能超时，可先执行 `npm config set registry https://registry.npmmirror.com` 切换镜像源。



\## ⚙️ 环境变量说明（`.env`）



项目根目录提供了一个 `.env` 文件模板。在本地 Ollama 环境下，无需真实的外部 API Key，只需保留以下占位符即可：



```env

\# 占位符，防止 LangChain 初始化报错

OPENAI\_API\_KEY=ollama

\# 以下为生产环境预留，本地留空即可

NEWS\_API\_KEY=

LME\_API\_KEY=

```



\## 🖥️ 接入 Claude Desktop / Cursor



项目根目录的 `mcp-config.json` 遵循标准 MCP 配置格式，可直接接入支持 MCP 的 IDE 客户端。



\### Claude Desktop

复制 `mcp-config.json` 内容到 `%APPDATA%\\Claude\\claude\_desktop\_config.json`，重启应用即可看到 9 个可用工具。



\### Cursor

复制 `mcp-config.json` 内容到 `%USERPROFILE%\\.cursor\\mcp.json`，在 `Settings -> MCP` 中查看连接状态。

> \*\*注意\*\*：Cursor 免费版（Hobby）目前不支持 MCP 工具调用，需 Pro 及以上版本。本项目已通过官方 MCP Inspector 完成协议层验证。



\## 🛑 停止服务



如需停止并清理容器，执行：



```bash

docker-compose down

```



\## 🧪 验证截图



项目 `docs/screenshots/` 目录下包含 MCP Inspector 的验证截图：

\- `inspector-lme-price.png` — lme-price-mcp 工具列表与调用结果

\- `inspector-mining-news.png` — mining-news-mcp 工具列表与调用结果

\- `inspector-mineral-pdf.png` — mineral-pdf-mcp 工具列表



\## 📂 项目结构



```

mining-daily-agent/

├── agent/

│   └── main.py                # Agent 主流程（LangGraph + MultiServerMCPClient）

├── servers/

│   ├── mining\_news\_mcp.py     # 新闻聚合 MCP Server

│   ├── mineral\_pdf\_mcp.py     # PDF 储量解析 MCP Server

│   └── lme\_price\_mcp.py       # 价格行情 MCP Server

├── docs/screenshots/          # MCP Inspector 验证截图

├── output/                    # 生成的简报存放目录

├── mcp-config.json            # Claude Desktop / Cursor 配置

├── docker-compose.yml         # 一键启动 3 个 Server + 1 个 Agent

├── Dockerfile

├── requirements.txt

├── .env

├── .gitignore

├── .dockerignore

├── README.md

└── RUN.md

```

