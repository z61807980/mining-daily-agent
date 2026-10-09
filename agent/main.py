import asyncio
import os
from datetime import datetime

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama

MCP_CONFIG = {
    "mining-news": {
        "command": "python",
        "args": ["servers/mining_news_mcp.py"],
        "transport": "stdio",
    },
    "mineral-pdf": {
        "command": "python",
        "args": ["servers/mineral_pdf_mcp.py"],
        "transport": "stdio",
    },
    "lme-price": {
        "command": "python",
        "args": ["servers/lme_price_mcp.py"],
        "transport": "stdio",
    },
}

SYSTEM_PROMPT = """你是一位资深矿业分析师，负责生成「矿权日报」。

## 工作流程
1. 使用 mining-news 工具的 search(query, days) 搜索目标矿种/公司的最新新闻
2. 使用 mining-news 工具的 fetch_article(url) 抓取重要新闻全文
3. 使用 mineral-pdf 工具的 extract_resources(pdf_url) 提取技术报告中的储量数据。严禁编造 URL。如果找不到真实的 PDF 链接，请如实说明"未找到技术报告 PDF"，不要调用该工具。
4. 使用 lme-price 工具的 get_price / get_trend 获取价格行情
5. 综合以上信息，生成结构化 Markdown 简报

## 简报格式要求
- 使用 Markdown 格式
- 每个数据点必须附引用源链接
- 包含：新闻摘要、储量数据、价格走势、风险提示
- 语言：中文
"""


async def generate_daily_brief(query: str) -> str:
    """主流程：输入查询 → 生成矿权日报。"""
    client = MultiServerMCPClient(MCP_CONFIG)
    tools = await client.get_tools()

    model = ChatOllama(
        model="qwen3:8b",
        temperature=0,
        base_url="http://host.docker.internal:11434",
    )

    agent = create_react_agent(model, tools, prompt=SYSTEM_PROMPT)

    today = datetime.now().strftime("%Y-%m-%d")
    user_message = (
        f"请生成一份关于「{query}」的今日（{today}）矿权简报。\n"
        f"要求：\n"
        f"1. 搜索最近 3 天的相关新闻并抓取重点文章全文\n"
        f"2. 查找该矿种最新的 NI 43-101 或 JORC 资源量报告并提取储量数据\n"
        f"3. 获取锂精矿（SC6）和碳酸锂的近期价格走势\n"
        f"4. 综合分析后输出完整 Markdown 简报，附所有引用源链接\n"
    )

    result = await agent.ainvoke({"messages": [("human", user_message)]})
    return result["messages"][-1].content


async def main():
    brief = await generate_daily_brief("Pilbara 锂矿")

    os.makedirs("output", exist_ok=True)
    output_path = "output/pilbara_daily_brief.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(brief)

    print("=" * 50)
    print(f"简报已生成，保存至 {output_path}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())