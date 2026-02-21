"""PDF 解析器测试."""
from __future__ import annotations

import pytest
import pymupdf

from src.core.models import FileType
from src.parsers.pdf_parser import parse_pdf


@pytest.fixture
def sample_pdf(tmp_path):
    """Generate a sample PDF using PyMuPDF."""
    pdf_path = tmp_path / "sample.pdf"
    doc = pymupdf.open()  # new empty document

    # Page 1 - title and introduction
    page = doc.new_page()
    # Insert title with large font
    page.insert_text((72, 72), "Sample Research Paper", fontsize=24)
    page.insert_text((72, 120), "Introduction", fontsize=16)
    page.insert_text((72, 150), "This paper discusses important research findings.", fontsize=12)
    page.insert_text((72, 170), "The methodology involves extensive experiments.", fontsize=12)

    # Page 2 - results
    page2 = doc.new_page()
    page2.insert_text((72, 72), "Results", fontsize=16)
    page2.insert_text((72, 100), "We found significant improvements in all metrics.", fontsize=12)
    page2.insert_text((72, 120), "The accuracy reached 95 percent.", fontsize=12)

    doc.save(str(pdf_path))
    doc.close()
    return str(pdf_path)


def test_parse_pdf_returns_parsed_document(sample_pdf):
    result = parse_pdf(sample_pdf)
    assert result.file_type == FileType.PDF
    assert result.file_path == sample_pdf


def test_parse_pdf_extracts_title(sample_pdf):
    result = parse_pdf(sample_pdf)
    # Title should be extracted (largest font text on page 1)
    assert result.title != ""


def test_parse_pdf_extracts_raw_text(sample_pdf):
    result = parse_pdf(sample_pdf)
    assert "research" in result.raw_text.lower() or "findings" in result.raw_text.lower()


def test_parse_pdf_extracts_sections(sample_pdf):
    result = parse_pdf(sample_pdf)
    assert len(result.sections) > 0


def test_parse_pdf_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_pdf("/nonexistent/file.pdf")
