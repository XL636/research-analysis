"""笔记解析器测试（Markdown + TXT）."""
from __future__ import annotations

from pathlib import Path

import pytest

from src.core.models import FileType
from src.parsers.note_parser import parse_note


FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestMarkdownParser:
    def test_parse_md_returns_markdown_type(self):
        result = parse_note(str(FIXTURES_DIR / "sample.md"))
        assert result.file_type == FileType.MARKDOWN

    def test_parse_md_extracts_title(self):
        result = parse_note(str(FIXTURES_DIR / "sample.md"))
        assert result.title == "Research on Machine Learning"

    def test_parse_md_extracts_sections(self):
        result = parse_note(str(FIXTURES_DIR / "sample.md"))
        section_titles = [s.title for s in result.sections]
        assert "Introduction" in section_titles
        assert "Methods" in section_titles
        assert "Results" in section_titles

    def test_parse_md_raw_text_not_empty(self):
        result = parse_note(str(FIXTURES_DIR / "sample.md"))
        assert len(result.raw_text) > 0

    def test_parse_md_section_content(self):
        result = parse_note(str(FIXTURES_DIR / "sample.md"))
        # Find Introduction section
        intro = next((s for s in result.sections if s.title == "Introduction"), None)
        assert intro is not None
        assert "artificial intelligence" in intro.content.lower()


class TestTxtParser:
    def test_parse_txt_returns_txt_type(self):
        result = parse_note(str(FIXTURES_DIR / "sample.txt"))
        assert result.file_type == FileType.TXT

    def test_parse_txt_splits_paragraphs(self):
        result = parse_note(str(FIXTURES_DIR / "sample.txt"))
        # sample.txt has 3 paragraphs separated by blank lines
        assert len(result.sections) == 3

    def test_parse_txt_title_is_filename(self):
        result = parse_note(str(FIXTURES_DIR / "sample.txt"))
        assert result.title == "sample"

    def test_parse_txt_raw_text_not_empty(self):
        result = parse_note(str(FIXTURES_DIR / "sample.txt"))
        assert "deep learning" in result.raw_text.lower()


def test_parse_note_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_note("/nonexistent/file.md")
