"""LaTeX 输出适配器 - 生成 .tex + .bib 文件."""

from __future__ import annotations

import re
from pathlib import Path

from loguru import logger

from src.core.paper_models import CitationRef, PaperDraft, PaperLanguage, PaperVenue


def write_latex(
    draft: PaperDraft,
    output_dir: str,
    venue: PaperVenue = PaperVenue.GENERIC,
    language: PaperLanguage = PaperLanguage.ZH,
) -> str:
    """将论文草稿导出为 LaTeX 文件.

    Args:
        draft: 论文草稿
        output_dir: 输出目录
        venue: 目标会议
        language: 论文语言

    Returns:
        main.tex 文件路径
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    # 生成 main.tex
    tex_content = _build_tex(draft, venue, language)
    tex_path = out / "main.tex"
    tex_path.write_text(tex_content, encoding="utf-8")

    # 生成 refs.bib
    bib_content = _build_bib(draft.citations)
    bib_path = out / "refs.bib"
    bib_path.write_text(bib_content, encoding="utf-8")

    logger.info(f"LaTeX output written to: {out}")
    return str(tex_path)


def _build_tex(draft: PaperDraft, venue: PaperVenue, language: PaperLanguage) -> str:
    """构建 LaTeX 文档."""
    is_zh = language == PaperLanguage.ZH

    # 文档类和宏包
    if is_zh:
        preamble = _ZH_PREAMBLE
    else:
        preamble = _EN_PREAMBLE

    parts = [preamble]

    # 标题和作者
    parts.append(f"\\title{{{_escape_latex(draft.title)}}}")
    parts.append("\\author{}")
    parts.append("\\date{}")
    parts.append("")
    parts.append("\\begin{document}")
    parts.append("\\maketitle")

    # 摘要
    if draft.abstract:
        parts.append("")
        parts.append("\\begin{abstract}")
        parts.append(_md_to_latex(draft.abstract))
        parts.append("\\end{abstract}")

    # 章节
    for section in draft.sections:
        parts.append("")
        cmd = "\\section" if section.level == 1 else "\\subsection"
        parts.append(f"{cmd}{{{_escape_latex(section.title)}}}")
        if section.content:
            parts.append(_md_to_latex(section.content))

    # 致谢
    if draft.acknowledgments:
        parts.append("")
        parts.append("\\section*{Acknowledgments}" if not is_zh else "\\section*{致谢}")
        parts.append(_md_to_latex(draft.acknowledgments))

    # 参考文献
    parts.append("")
    parts.append("\\bibliographystyle{plain}")
    parts.append("\\bibliography{refs}")
    parts.append("")
    parts.append("\\end{document}")

    return "\n".join(parts)


def _build_bib(citations: list[CitationRef]) -> str:
    """生成 BibTeX 文件."""
    entries = []
    for ref in citations:
        key = ref.key or f"ref-{len(entries)}"
        entry = f"@article{{{key},\n"
        entry += f"  title = {{{_escape_latex(ref.title)}}},\n"
        if ref.authors:
            entry += f"  author = {{{_escape_latex(ref.authors)}}},\n"
        if ref.year:
            entry += f"  year = {{{ref.year}}},\n"
        if ref.venue:
            entry += f"  journal = {{{_escape_latex(ref.venue)}}},\n"
        if ref.doi:
            entry += f"  doi = {{{ref.doi}}},\n"
        if ref.url:
            entry += f"  url = {{{ref.url}}},\n"
        entry += "}"
        entries.append(entry)
    return "\n\n".join(entries)


def _escape_latex(text: str) -> str:
    """转义 LaTeX 特殊字符."""
    chars = {
        "&": "\\&",
        "%": "\\%",
        "$": "\\$",
        "#": "\\#",
        "_": "\\_",
        "{": "\\{",
        "}": "\\}",
        "~": "\\textasciitilde{}",
        "^": "\\textasciicircum{}",
    }
    for old, new in chars.items():
        text = text.replace(old, new)
    return text


def _md_to_latex(md: str) -> str:
    """简单的 Markdown → LaTeX 转换."""
    lines = md.split("\n")
    result = []

    in_itemize = False

    for line in lines:
        stripped = line.strip()

        # 子标题
        if stripped.startswith("####"):
            if in_itemize:
                result.append("\\end{itemize}")
                in_itemize = False
            result.append(f"\\paragraph{{{_escape_latex(stripped.lstrip('#').strip())}}}")
            continue
        if stripped.startswith("###"):
            if in_itemize:
                result.append("\\end{itemize}")
                in_itemize = False
            result.append(f"\\subsubsection{{{_escape_latex(stripped.lstrip('#').strip())}}}")
            continue

        # 列表项
        if stripped.startswith("- ") or stripped.startswith("* "):
            if not in_itemize:
                result.append("\\begin{itemize}")
                in_itemize = True
            result.append(f"  \\item {_escape_latex(stripped[2:])}")
            continue

        # 结束列表
        if in_itemize and not stripped:
            result.append("\\end{itemize}")
            in_itemize = False

        # 粗体和斜体
        processed = stripped
        processed = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", processed)
        processed = re.sub(r"\*(.+?)\*", r"\\textit{\1}", processed)

        # 引用标记 [ref-key] → \cite{ref-key}
        processed = re.sub(r"\[([a-zA-Z0-9_-]+)\]", r"\\cite{\1}", processed)

        result.append(processed)

    if in_itemize:
        result.append("\\end{itemize}")

    return "\n".join(result)


_ZH_PREAMBLE = r"""\documentclass[12pt,a4paper]{ctexart}
\usepackage[margin=2.5cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{natbib}
"""

_EN_PREAMBLE = r"""\documentclass[12pt,a4paper]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{natbib}
"""
