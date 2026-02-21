"""PPTX 输出适配器 - 生成 PowerPoint 演示文稿."""

from __future__ import annotations

import re
from pathlib import Path

from loguru import logger
from pptx import Presentation

from src.core.models import Report


def write_pptx(report: Report, output_path: str) -> str:
    """将报告写入 PPTX 文件.

    Args:
        report: 报告对象
        output_path: 输出文件路径

    Returns:
        实际写入的文件路径
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    prs = Presentation()

    # 标题幻灯片
    slide_layout = prs.slide_layouts[0]  # Title Slide
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = report.title
    slide.placeholders[1].text = (
        f"生成时间：{report.generated_at.strftime('%Y-%m-%d %H:%M')}\n"
        f"来源：{', '.join(report.source_files)}"
    )

    # 解析 Markdown 内容为幻灯片
    _markdown_to_slides(prs, report.content)

    prs.save(output_path)
    logger.info(f"PPTX report written to: {path}")
    return str(path)


def _markdown_to_slides(prs: Presentation, markdown_text: str) -> None:
    """将 Markdown 内容转换为 PPT 幻灯片.

    策略：每个 ## 标题创建一个新幻灯片，内容放在正文区。
    """
    lines = markdown_text.split("\n")
    current_title = ""
    current_content: list[str] = []

    def flush_slide():
        if not current_title and not current_content:
            return
        slide_layout = prs.slide_layouts[1]  # Title and Content
        slide = prs.slides.add_slide(slide_layout)
        if current_title:
            slide.shapes.title.text = current_title

        content = "\n".join(current_content).strip()
        if content and len(slide.placeholders) > 1:
            # 清理 Markdown 标记
            content = re.sub(r"\*\*(.+?)\*\*", r"\1", content)
            content = re.sub(r"\*(.+?)\*", r"\1", content)
            content = re.sub(r"`(.+?)`", r"\1", content)

            # 限制内容长度，避免超出幻灯片
            if len(content) > 800:
                content = content[:797] + "..."

            slide.placeholders[1].text = content

    for line in lines:
        # ## 标题 → 新幻灯片
        h2_match = re.match(r"^##\s+(.+)$", line)
        if h2_match:
            flush_slide()
            current_title = h2_match.group(1)
            current_content = []
            continue

        # # 标题 → 跳过（已在标题幻灯片）
        if re.match(r"^#\s+", line):
            continue

        # 分隔线 → 跳过
        if re.match(r"^---+$", line.strip()):
            continue

        # 其他内容
        stripped = line.strip()
        if stripped:
            # 将列表项保持原样
            current_content.append(stripped)

    flush_slide()
