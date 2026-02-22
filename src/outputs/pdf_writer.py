"""PDF 输出适配器 - 生成 PDF 报告（Markdown → HTML → PDF）."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from src.core.models import Report

# CSS for the PDF report — A4, academic style
_CSS = """\
@page {
    size: A4;
    margin: 2.5cm;
    @bottom-center {
        content: counter(page);
        font-size: 9pt;
        color: #999;
    }
}

body {
    font-family: Calibri, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}

h1 {
    color: #1B3A5C;
    font-size: 22pt;
    border-bottom: 2px solid #2E75B6;
    padding-bottom: 6px;
    margin-top: 0;
}

h2 {
    color: #1B3A5C;
    font-size: 16pt;
    margin-top: 24pt;
    border-bottom: 1px solid #D6E4F0;
    padding-bottom: 4px;
}

h3 {
    color: #2E75B6;
    font-size: 13pt;
    margin-top: 18pt;
}

a {
    color: #2E75B6;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 12pt 0;
    font-size: 10pt;
}

thead th {
    background-color: #1B3A5C;
    color: #fff;
    padding: 8px 10px;
    text-align: left;
    font-weight: 600;
}

tbody td {
    padding: 6px 10px;
    border-bottom: 1px solid #E5E7EB;
}

tbody tr:nth-child(even) {
    background-color: #F9FAFB;
}

code {
    font-family: "Cascadia Code", "Fira Code", Consolas, monospace;
    background-color: #F3F4F6;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 10pt;
}

pre {
    background-color: #F3F4F6;
    padding: 12px;
    border-radius: 6px;
    overflow-x: auto;
    font-size: 10pt;
    line-height: 1.4;
}

pre code {
    background: none;
    padding: 0;
}

blockquote {
    border-left: 3px solid #2E75B6;
    margin-left: 0;
    padding-left: 12px;
    color: #555;
}

ul, ol {
    padding-left: 20px;
}

li {
    margin-bottom: 4px;
}

hr {
    border: none;
    border-top: 1px solid #D6E4F0;
    margin: 18pt 0;
}
"""

_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<style>{css}</style>
</head>
<body>
<h1>{title}</h1>
<p style="color:#999;font-size:9pt;">
    {generated_at} &nbsp;|&nbsp; {source_files}
</p>
<hr>
{body}
</body>
</html>
"""


def write_pdf(report: Report, output_path: str) -> str:
    """将报告写入 PDF 文件.

    Args:
        report: 报告对象
        output_path: 输出文件路径

    Returns:
        实际写入的文件路径
    """
    try:
        import markdown2
        import weasyprint
    except ImportError:
        raise ImportError(
            "PDF output requires weasyprint and markdown2. "
            "Install with: uv sync --extra pdf"
        )

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Markdown → HTML
    body_html = markdown2.markdown(
        report.content,
        extras=["fenced-code-blocks", "tables", "cuddled-lists"],
    )

    # Build full HTML document
    html = _HTML_TEMPLATE.format(
        css=_CSS,
        title=report.title,
        generated_at=report.generated_at.strftime("%Y-%m-%d %H:%M"),
        source_files=", ".join(report.source_files) if report.source_files else "",
        body=body_html,
    )

    # HTML → PDF
    weasyprint.HTML(string=html).write_pdf(str(path))

    logger.info(f"PDF report written to: {path}")
    return str(path)
