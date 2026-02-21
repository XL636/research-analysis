"""Markdown 输出适配器."""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from src.core.models import Report


def write_markdown(report: Report, output_path: str) -> str:
    """将报告写入 Markdown 文件.

    Args:
        report: 报告对象
        output_path: 输出文件路径

    Returns:
        实际写入的文件路径
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    content = report.content

    # 确保报告有元信息头
    if not content.startswith("# "):
        header = f"# {report.title}\n\n"
        header += f"> 生成时间：{report.generated_at.strftime('%Y-%m-%d %H:%M')}\n"
        if report.source_files:
            header += f"> 来源文件：{', '.join(report.source_files)}\n"
        header += "\n---\n\n"
        content = header + content

    path.write_text(content, encoding="utf-8")
    logger.info(f"Report written to: {path}")
    return str(path)
