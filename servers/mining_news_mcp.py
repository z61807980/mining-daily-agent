# servers/mining_news_mcp.py
from mcp.server.fastmcp import FastMCP
import httpx
from datetime import datetime, timedelta

mcp = FastMCP("mining-news-mcp")

NEWS_SOURCES = {
    "mining_weekly": "https://www.miningweekly.com/rss/",
    "mining_com": "https://www.mining.com/feed/",
    "resources_review": "https://resourcesreview.com.au/feed/",
}

@mcp.tool()
async def search(query: str, days: int = 3) -> str:
    """搜索矿业相关新闻。

    Args:
        query: 搜索关键词，如 "Pilbara lithium"
        days: 回溯天数，默认 3 天
    """
    cutoff = datetime.now() - timedelta(days=days)
    results = []

    for source, rss_url in NEWS_SOURCES.items():
        async with httpx.AsyncClient(timeout=15, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}) as client:
            resp = await client.get(rss_url)
            # 解析 RSS，过滤关键词 + 时间
            items = _parse_rss(resp.text, query, cutoff)
            results.extend(items)

    if not results:
        return f"未找到最近 {days} 天内关于「{query}」的新闻。"

    lines = [f"# 新闻搜索结果：{query}（近 {days} 天）\n"]
    for i, item in enumerate(results[:20], 1):
        lines.append(
            f"**{i}. {item['title']}**\n"
            f"   - 来源：{item['source']} | 日期：{item['date']}\n"
            f"   - 链接：{item['url']}\n"
            f"   - 摘要：{item['summary'][:200]}...\n"
        )
    return "\n".join(lines)


@mcp.tool()
async def fetch_article(url: str) -> str:
    """抓取单篇新闻正文全文。

    Args:
        url: 文章 URL
    """
    async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        text = _extract_main_content(resp.text)
    return f"# 文章全文\n\n**URL**: {url}\n\n{text[:5000]}"


def _parse_rss(xml_text: str, keyword: str, cutoff) -> list[dict]:
    """解析 RSS 并过滤。生产环境建议用 feedparser。"""
    import feedparser
    feed = feedparser.parse(xml_text)
    items = []
    for entry in feed.entries:
        title = entry.get("title", "")
        summary = entry.get("summary", "")
        if keyword.lower() in (title + summary).lower():
            pub_date = entry.get("published_parsed")
            if pub_date:
                dt = datetime(*pub_date[:6])
                if dt >= cutoff:
                    items.append({
                        "title": title,
                        "summary": summary,
                        "url": entry.get("link", ""),
                        "date": dt.strftime("%Y-%m-%d"),
                        "source": feed.feed.get("title", "Unknown"),
                    })
    return items


def _extract_main_content(html: str) -> str:
    """提取 HTML 正文（简化版，生产建议用 readability-lxml）。"""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    article = soup.find("article") or soup.find("main") or soup.body
    return article.get_text(separator="\n", strip=True) if article else ""


if __name__ == "__main__":
    mcp.run()  # stdio transport