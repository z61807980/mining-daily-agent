# servers/lme_price_mcp.py
from mcp.server.fastmcp import FastMCP
from datetime import datetime, timedelta
from decimal import Decimal

mcp = FastMCP("lme-price-mcp")

# 价格缓存（生产环境替换为 Fastmarkets/LME API）
_PRICE_CACHE = {
    "lithium_carbonate": {
        "2026-08-01": 20500, "2026-08-02": 20800,
        "2026-08-03": 21200, "2026-08-04": 21000,
        "2026-08-05": 21500, "2026-08-06": 21800,
        "2026-08-07": 22000, "2026-08-08": 21900,
        "2026-08-09": 22100, "2026-08-10": 22300,
    },
    "spodumene_sc6": {
        "2026-08-01": 1990, "2026-08-02": 2010,
        "2026-08-03": 2040, "2026-08-04": 2025,
        "2026-08-05": 2060, "2026-08-06": 2080,
        "2026-08-07": 2100, "2026-08-08": 2090,
        "2026-08-09": 2130, "2026-08-10": 2150,
    },
}


@mcp.tool()
async def get_price(commodity: str, date: str) -> str:
    """获取指定商品在指定日期的价格。

    Args:
        commodity: 商品名称（lithium_carbonate / spodumene_sc6）
        date: 日期，格式 YYYY-MM-DD
    """
    data = _PRICE_CACHE.get(commodity)
    if not data:
        return f"未知商品：{commodity}。支持：{list(_PRICE_CACHE.keys())}"

    price = data.get(date)
    if price is None:
        available = sorted(data.keys())
        return (
            f"日期 {date} 无数据。最近可用日期："
            f"{available[-3:] if available else '无'}"
        )

    unit = "USD/tonne LCE" if "carbonate" in commodity else "USD/tonne SC6 CIF"
    return (
        f"**{commodity}** — {date}\n"
        f"- 价格：**{price:,} {unit}**\n"
        f"- 数据源：LME / Fastmarkets\n"
    )


@mcp.tool()
async def get_trend(commodity: str, days: int = 7) -> str:
    """获取商品价格走势。

    Args:
        commodity: 商品名称
        days: 回溯天数
    """
    data = _PRICE_CACHE.get(commodity)
    if not data:
        return f"未知商品：{commodity}"

    sorted_dates = sorted(data.keys())[-days:]
    if not sorted_dates:
        return "无足够数据"

    prices = [data[d] for d in sorted_dates]
    first, last = prices[0], prices[-1]
    change = ((last - first) / first) * 100

    trend_icon = "📈" if change > 0 else "📉" if change < 0 else "➡️"
    max_price = max(prices)
    min_price = min(prices)

    lines = [
        f"# {commodity} 价格走势（近 {days} 天）\n",
        f"- 起始价：{first:,}",
        f"- 最新价：{last:,}",
        f"- 区间涨跌：{trend_icon} **{change:+.1f}%**",
        f"- 区间最高：{max_price:,} | 区间最低：{min_price:,}\n",
        "## 每日明细\n",
    ]
    for d, p in zip(sorted_dates, prices):
        bar_len = int((p - min_price) / (max_price - min_price + 1) * 20)
        lines.append(f"  {d}  {'█' * bar_len} {p:,}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()