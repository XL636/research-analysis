"""PDF 解析器 - 使用 PyMuPDF 提取文本和结构."""

from __future__ import annotations

from pathlib import Path

import pymupdf
from loguru import logger

from src.core.models import DocumentSection, FileType, ParsedDocument


def parse_pdf(file_path: str) -> ParsedDocument:
    """解析 PDF 文件，提取结构化内容."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    logger.info(f"Parsing PDF: {path.name}")

    doc = pymupdf.open(file_path)
    sections: list[DocumentSection] = []
    all_text_parts: list[str] = []
    title = ""
    authors: list[str] = []
    abstract = ""

    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        if not text.strip():
            continue

        all_text_parts.append(text)

        # 从第一页提取标题（通常是最大字体的文本）
        if page_num == 0 and not title:
            blocks = page.get_text("dict")["blocks"]
            max_size = 0
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        if span["size"] > max_size and len(span["text"].strip()) > 3:
                            max_size = span["size"]
                            title = span["text"].strip()

        # 尝试识别章节标题（启发式：短行 + 较大字号或数字开头）
        lines = text.split("\n")
        current_section_lines: list[str] = []
        current_title = ""

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # 启发式判断是否为章节标题
            is_heading = (
                len(stripped) < 100
                and (
                    stripped[0].isdigit()
                    or stripped.upper() == stripped
                    or stripped.startswith("Abstract")
                    or stripped.startswith("Introduction")
                    or stripped.startswith("Conclusion")
                    or stripped.startswith("References")
                    or stripped.startswith("Related Work")
                    or stripped.startswith("Method")
                    or stripped.startswith("Experiment")
                    or stripped.startswith("Result")
                    or stripped.startswith("Discussion")
                )
            )

            if is_heading and current_section_lines:
                sections.append(DocumentSection(
                    title=current_title,
                    content="\n".join(current_section_lines),
                    level=2 if current_title else 1,
                ))
                current_section_lines = []
                current_title = stripped

                # 提取 Abstract
                if stripped.lower().startswith("abstract"):
                    abstract = ""  # 将在后续行中填充
            elif stripped.lower().startswith("abstract") and not abstract:
                current_title = "Abstract"
            else:
                current_section_lines.append(stripped)
                if current_title == "Abstract" and not abstract:
                    abstract += stripped + " "

        # 添加最后一个 section
        if current_section_lines:
            sections.append(DocumentSection(
                title=current_title,
                content="\n".join(current_section_lines),
                level=2,
            ))

    raw_text = "\n\n".join(all_text_parts)
    abstract = abstract.strip()

    # 从元数据提取信息
    metadata_dict: dict[str, str] = {}
    pdf_metadata = doc.metadata
    if pdf_metadata:
        if pdf_metadata.get("title"):
            title = title or pdf_metadata["title"]
            metadata_dict["pdf_title"] = pdf_metadata["title"]
        if pdf_metadata.get("author"):
            authors = [a.strip() for a in pdf_metadata["author"].split(",")]
            metadata_dict["pdf_author"] = pdf_metadata["author"]

    doc.close()

    logger.info(f"PDF parsed: {len(sections)} sections, {len(raw_text)} chars")

    return ParsedDocument(
        file_path=file_path,
        file_type=FileType.PDF,
        title=title,
        authors=authors,
        abstract=abstract,
        sections=sections,
        raw_text=raw_text,
        metadata=metadata_dict,
    )
