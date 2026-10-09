# servers/mineral_pdf_mcp.py
from mcp.server.fastmcp import FastMCP
import httpx, re, tempfile, os

mcp = FastMCP("mineral-pdf-mcp")


@mcp.tool()
async def extract_resources(pdf_url: str) -> str:
    """从 NI 43-101 / JORC 技术报告中提取矿产资源量数据。

    解析 Indicated / Inferred / Measured 分类的矿石吨位与品位。

    Args:
        pdf_url: PDF 技术报告的 URL
    """
    # 1. 下载 PDF
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        resp = await client.get(pdf_url)
        resp.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(resp.content)
        tmp_path = f.name

    try:
        import pdfplumber
        full_text = ""
        with pdfplumber.open(tmp_path) as pdf:
            for page in pdf.pages[:80]:  # 限制页数避免超时
                text = page.extract_text() or ""
                full_text += text + "\n"
    finally:
        os.unlink(tmp_path)

    # 2. 提取资源量表格数据
    result = _extract_resource_tables(full_text)
    return result


def _extract_resource_tables(text: str) -> str:
    """从 PDF 文本中提取资源量分类数据。"""
    patterns = {
        "Measured": r"(?i)measured[^\d]*?([\d,.]+)\s*(?:Mt|million tonnes?)",
        "Indicated": r"(?i)indicated[^\d]*?([\d,.]+)\s*(?:Mt|million tonnes?)",
        "Inferred": r"(?i)inferred[^\d]*?([\d,.]+)\s*(?:Mt|million tonnes?)",
        "Measured+Indicated": r"(?i)(?:measured\s*[&+]\s*indicated|M\s*[&+]\s*I)[^\d]*?([\d,.]+)\s*(?:Mt|million tonnes?)",
    }

    grade_patterns = {
        "Li2O": r"(?i)([\d.]+)\s*%\s*(?:Li2?O|lithium oxide)",
        "Ta2O5": r"(?i)([\d,.]+)\s*(?:ppm|parts per million)\s*(?:Ta2?O5|tantalum)",
        "Fe2O3": r"(?i)([\d.]+)\s*%\s*(?:Fe2?O3|iron oxide)",
    }

    result_lines = ["# NI 43-101 / JORC 资源量提取结果\n"]
    result_lines.append("## 矿石吨位\n")
    for category, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            result_lines.append(f"- **{category}**: {match.group(1)} Mt")

    result_lines.append("\n## 品位\n")
    for mineral, pattern in grade_patterns.items():
        match = re.search(pattern, text)
        if match:
            result_lines.append(f"- **{mineral}**: {match.group(1)}")

    # 提取含金属量
    contained = re.search(r"(?i)contain(?:ing|ed)?\s*([\d,.]+)\s*(?:Mt|million tonnes?)\s*(?:of\s*)?(?:Li2?O|lithium oxide)", text)
    if contained:
        result_lines.append(f"\n## 含锂金属量\n- **Contained Li2O**: {contained.group(1)} Mt")

    if len(result_lines) <= 2:
        result_lines.append("⚠️ 未能自动识别资源量表格，请人工核验原文。")

    return "\n".join(result_lines)


if __name__ == "__main__":
    mcp.run()