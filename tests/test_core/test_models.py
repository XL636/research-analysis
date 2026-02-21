"""Tests for src/core/models.py — Pydantic data models."""
from __future__ import annotations

from datetime import datetime

from src.core.models import (
    FileType,
    DocumentSection,
    ParsedDocument,
    KeyFinding,
    MethodologyAssessment,
    AnalysisResult,
    ThemeComparison,
    SynthesisResult,
    Report,
    ReviewFeedback,
    PipelineContext,
)


# ---------------------------------------------------------------------------
# FileType
# ---------------------------------------------------------------------------

class TestFileType:
    def test_enum_values(self) -> None:
        assert FileType.PDF == "pdf"
        assert FileType.PPTX == "pptx"
        assert FileType.MARKDOWN == "markdown"
        assert FileType.TXT == "txt"
        assert FileType.DOCX == "docx"
        assert FileType.AUDIO == "audio"

    def test_is_str_subclass(self) -> None:
        assert isinstance(FileType.PDF, str)

    def test_all_members(self) -> None:
        members = {m.value for m in FileType}
        assert members == {"pdf", "pptx", "markdown", "txt", "docx", "audio"}


# ---------------------------------------------------------------------------
# DocumentSection
# ---------------------------------------------------------------------------

class TestDocumentSection:
    def test_defaults(self) -> None:
        section = DocumentSection()
        assert section.title == ""
        assert section.content == ""
        assert section.level == 1

    def test_custom_values(self) -> None:
        section = DocumentSection(title="Methods", content="We used XYZ.", level=3)
        assert section.title == "Methods"
        assert section.content == "We used XYZ."
        assert section.level == 3

    def test_level_two(self, sample_section: DocumentSection) -> None:
        assert sample_section.level == 2
        assert sample_section.title == "Introduction"


# ---------------------------------------------------------------------------
# ParsedDocument
# ---------------------------------------------------------------------------

class TestParsedDocument:
    def test_required_fields(self) -> None:
        doc = ParsedDocument(file_path="/tmp/doc.pdf", file_type=FileType.PDF)
        assert doc.file_path == "/tmp/doc.pdf"
        assert doc.file_type == FileType.PDF

    def test_defaults(self) -> None:
        doc = ParsedDocument(file_path="/tmp/doc.pdf", file_type=FileType.PDF)
        assert doc.title == ""
        assert doc.authors == []
        assert doc.abstract == ""
        assert doc.sections == []
        assert doc.raw_text == ""
        assert doc.metadata == {}
        assert isinstance(doc.parsed_at, datetime)

    def test_full_instantiation(self, sample_parsed_doc: ParsedDocument) -> None:
        assert sample_parsed_doc.title == "Test Paper"
        assert sample_parsed_doc.authors == ["Author A"]
        assert sample_parsed_doc.abstract == "This is an abstract."
        assert len(sample_parsed_doc.sections) == 1

    def test_full_text_with_sections(self, sample_parsed_doc: ParsedDocument) -> None:
        text = sample_parsed_doc.full_text
        # Title should appear as a heading
        assert "# Test Paper" in text
        # Abstract section header should be present
        assert "## Abstract" in text
        assert "This is an abstract." in text
        # Section title at level 2 → prefix "###"
        assert "### Introduction" in text
        assert "This is the introduction." in text

    def test_full_text_section_level_prefix(self) -> None:
        """Section at level 1 gets prefix '##' (level + 1)."""
        section = DocumentSection(title="Background", content="Some background.", level=1)
        doc = ParsedDocument(
            file_path="/tmp/doc.pdf",
            file_type=FileType.PDF,
            title="A Paper",
            sections=[section],
        )
        text = doc.full_text
        assert "## Background" in text

    def test_full_text_without_sections_returns_raw_text(self) -> None:
        doc = ParsedDocument(
            file_path="/tmp/doc.txt",
            file_type=FileType.TXT,
            raw_text="Just raw text content.",
        )
        assert doc.full_text == "Just raw text content."

    def test_full_text_no_title_no_abstract(self) -> None:
        section = DocumentSection(title="Only Section", content="Content here.", level=1)
        doc = ParsedDocument(
            file_path="/tmp/doc.md",
            file_type=FileType.MARKDOWN,
            sections=[section],
        )
        text = doc.full_text
        # No title block
        assert "# " not in text.split("\n")[0] or "# " not in text
        assert "Only Section" in text

    def test_full_text_with_title_but_no_abstract(self) -> None:
        section = DocumentSection(title="Sec", content="Body.", level=1)
        doc = ParsedDocument(
            file_path="/tmp/doc.pdf",
            file_type=FileType.PDF,
            title="My Paper",
            sections=[section],
        )
        text = doc.full_text
        assert "# My Paper" in text
        assert "Abstract" not in text

    def test_metadata_is_dict(self) -> None:
        doc = ParsedDocument(
            file_path="/tmp/doc.pdf",
            file_type=FileType.PDF,
            metadata={"pages": "10", "language": "en"},
        )
        assert doc.metadata["pages"] == "10"
        assert doc.metadata["language"] == "en"


# ---------------------------------------------------------------------------
# KeyFinding
# ---------------------------------------------------------------------------

class TestKeyFinding:
    def test_required_finding(self) -> None:
        kf = KeyFinding(finding="Something was discovered.")
        assert kf.finding == "Something was discovered."
        assert kf.evidence == ""
        assert kf.significance == ""

    def test_full_fields(self, sample_key_finding: KeyFinding) -> None:
        assert sample_key_finding.finding == "Key discovery"
        assert sample_key_finding.evidence == "Table 1"
        assert sample_key_finding.significance == "High impact"


# ---------------------------------------------------------------------------
# MethodologyAssessment
# ---------------------------------------------------------------------------

class TestMethodologyAssessment:
    def test_defaults(self) -> None:
        m = MethodologyAssessment()
        assert m.approach == ""
        assert m.strengths == []
        assert m.limitations == []

    def test_full_fields(self) -> None:
        m = MethodologyAssessment(
            approach="RCT",
            strengths=["Blinded", "Large N"],
            limitations=["Short follow-up"],
        )
        assert m.approach == "RCT"
        assert "Blinded" in m.strengths
        assert "Short follow-up" in m.limitations


# ---------------------------------------------------------------------------
# AnalysisResult
# ---------------------------------------------------------------------------

class TestAnalysisResult:
    def test_required_field(self) -> None:
        ar = AnalysisResult(document_title="Doc")
        assert ar.document_title == "Doc"

    def test_defaults(self) -> None:
        ar = AnalysisResult(document_title="Doc")
        assert ar.summary == ""
        assert ar.key_findings == []
        assert isinstance(ar.methodology, MethodologyAssessment)
        assert ar.contributions == []
        assert ar.limitations == []
        assert ar.future_work == []
        assert ar.tags == []
        assert ar.relevance_score == 0.0

    def test_full_instantiation(self, sample_analysis_result: AnalysisResult) -> None:
        assert sample_analysis_result.document_title == "Test Paper"
        assert sample_analysis_result.summary == "Paper summary here."
        assert len(sample_analysis_result.key_findings) == 1
        assert sample_analysis_result.relevance_score == 8.5
        assert "ml" in sample_analysis_result.tags

    def test_methodology_embedded(self, sample_analysis_result: AnalysisResult) -> None:
        m = sample_analysis_result.methodology
        assert m.approach == "Experimental"
        assert "Robust" in m.strengths
        assert "Small sample" in m.limitations


# ---------------------------------------------------------------------------
# ThemeComparison
# ---------------------------------------------------------------------------

class TestThemeComparison:
    def test_required_theme(self) -> None:
        tc = ThemeComparison(theme="Scalability")
        assert tc.theme == "Scalability"
        assert tc.perspectives == {}

    def test_with_perspectives(self) -> None:
        tc = ThemeComparison(
            theme="Efficiency",
            perspectives={"Paper A": "High efficiency", "Paper B": "Moderate efficiency"},
        )
        assert tc.perspectives["Paper A"] == "High efficiency"
        assert tc.perspectives["Paper B"] == "Moderate efficiency"


# ---------------------------------------------------------------------------
# SynthesisResult
# ---------------------------------------------------------------------------

class TestSynthesisResult:
    def test_defaults(self) -> None:
        sr = SynthesisResult()
        assert sr.overall_summary == ""
        assert sr.common_themes == []
        assert sr.key_differences == []
        assert sr.theme_comparisons == []
        assert sr.research_gaps == []
        assert sr.recommendations == []
        assert sr.source_analyses == []

    def test_with_data(self, sample_analysis_result: AnalysisResult) -> None:
        tc = ThemeComparison(theme="Deep Learning", perspectives={"Test Paper": "Core topic"})
        sr = SynthesisResult(
            overall_summary="Two papers reviewed.",
            common_themes=["Neural networks"],
            key_differences=["Scale of experiments"],
            theme_comparisons=[tc],
            research_gaps=["Interpretability"],
            recommendations=["Focus on robustness"],
            source_analyses=[sample_analysis_result],
        )
        assert sr.overall_summary == "Two papers reviewed."
        assert len(sr.source_analyses) == 1
        assert len(sr.theme_comparisons) == 1
        assert sr.theme_comparisons[0].theme == "Deep Learning"


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

class TestReport:
    def test_required_fields(self) -> None:
        report = Report(title="My Report", content="# My Report\n\nContent.")
        assert report.title == "My Report"
        assert report.content == "# My Report\n\nContent."

    def test_defaults(self) -> None:
        report = Report(title="R", content="C")
        assert report.format == "markdown"
        assert isinstance(report.generated_at, datetime)
        assert report.source_files == []

    def test_full_instantiation(self, sample_report: Report) -> None:
        assert sample_report.title == "Test Report"
        assert "Report content here." in sample_report.content
        assert "test.pdf" in sample_report.source_files

    def test_custom_format(self) -> None:
        report = Report(title="R", content="C", format="docx")
        assert report.format == "docx"


# ---------------------------------------------------------------------------
# ReviewFeedback
# ---------------------------------------------------------------------------

class TestReviewFeedback:
    def test_defaults(self) -> None:
        rf = ReviewFeedback()
        assert rf.approved is False
        assert rf.overall_score == 0.0
        assert rf.issues == []
        assert rf.suggestions == []
        assert rf.details == ""

    def test_approved_feedback(self, sample_review_approved: ReviewFeedback) -> None:
        assert sample_review_approved.approved is True
        assert sample_review_approved.overall_score == 8.0
        assert sample_review_approved.issues == []
        assert "Minor tweak" in sample_review_approved.suggestions

    def test_rejected_feedback(self, sample_review_rejected: ReviewFeedback) -> None:
        assert sample_review_rejected.approved is False
        assert sample_review_rejected.overall_score == 5.0
        assert "Missing details" in sample_review_rejected.issues
        assert "Add more evidence" in sample_review_rejected.suggestions

    def test_with_details(self) -> None:
        rf = ReviewFeedback(approved=True, overall_score=9.0, details="Excellent work.")
        assert rf.details == "Excellent work."


# ---------------------------------------------------------------------------
# PipelineContext
# ---------------------------------------------------------------------------

class TestPipelineContext:
    def test_all_defaults(self) -> None:
        ctx = PipelineContext()
        assert ctx.input_files == []
        assert ctx.parsed_documents == []
        assert ctx.analyses == []
        assert ctx.synthesis is None
        assert ctx.report is None
        assert ctx.review is None
        assert ctx.output_path == ""
        assert ctx.output_format == "markdown"

    def test_with_input_files(self) -> None:
        ctx = PipelineContext(input_files=["/tmp/a.pdf", "/tmp/b.pdf"])
        assert len(ctx.input_files) == 2

    def test_with_optional_fields(
        self,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
        sample_review_approved: ReviewFeedback,
    ) -> None:
        sr = SynthesisResult(overall_summary="Synthesis done.")
        ctx = PipelineContext(
            input_files=["/tmp/test.pdf"],
            parsed_documents=[sample_parsed_doc],
            analyses=[sample_analysis_result],
            synthesis=sr,
            report=sample_report,
            review=sample_review_approved,
            output_path="/tmp/output.md",
            output_format="markdown",
        )
        assert len(ctx.parsed_documents) == 1
        assert len(ctx.analyses) == 1
        assert ctx.synthesis is not None
        assert ctx.report is not None
        assert ctx.review is not None
        assert ctx.output_path == "/tmp/output.md"

    def test_output_format_custom(self) -> None:
        ctx = PipelineContext(output_format="docx")
        assert ctx.output_format == "docx"


# ---------------------------------------------------------------------------
# Serialization round-trip
# ---------------------------------------------------------------------------

class TestSerializationRoundTrip:
    def test_parsed_document_roundtrip(self, sample_parsed_doc: ParsedDocument) -> None:
        json_str = sample_parsed_doc.model_dump_json()
        restored = ParsedDocument.model_validate_json(json_str)
        assert restored.file_path == sample_parsed_doc.file_path
        assert restored.file_type == sample_parsed_doc.file_type
        assert restored.title == sample_parsed_doc.title
        assert restored.authors == sample_parsed_doc.authors
        assert len(restored.sections) == len(sample_parsed_doc.sections)

    def test_analysis_result_roundtrip(self, sample_analysis_result: AnalysisResult) -> None:
        json_str = sample_analysis_result.model_dump_json()
        restored = AnalysisResult.model_validate_json(json_str)
        assert restored.document_title == sample_analysis_result.document_title
        assert restored.summary == sample_analysis_result.summary
        assert restored.relevance_score == sample_analysis_result.relevance_score
        assert len(restored.key_findings) == len(sample_analysis_result.key_findings)
        assert restored.key_findings[0].finding == sample_analysis_result.key_findings[0].finding

    def test_report_roundtrip(self, sample_report: Report) -> None:
        json_str = sample_report.model_dump_json()
        restored = Report.model_validate_json(json_str)
        assert restored.title == sample_report.title
        assert restored.content == sample_report.content
        assert restored.source_files == sample_report.source_files

    def test_review_feedback_roundtrip(self, sample_review_rejected: ReviewFeedback) -> None:
        json_str = sample_review_rejected.model_dump_json()
        restored = ReviewFeedback.model_validate_json(json_str)
        assert restored.approved == sample_review_rejected.approved
        assert restored.overall_score == sample_review_rejected.overall_score
        assert restored.issues == sample_review_rejected.issues

    def test_pipeline_context_roundtrip(
        self,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
    ) -> None:
        ctx = PipelineContext(
            input_files=["/tmp/test.pdf"],
            parsed_documents=[sample_parsed_doc],
            analyses=[sample_analysis_result],
            output_format="docx",
        )
        json_str = ctx.model_dump_json()
        restored = PipelineContext.model_validate_json(json_str)
        assert restored.input_files == ctx.input_files
        assert restored.output_format == ctx.output_format
        assert len(restored.parsed_documents) == 1
        assert len(restored.analyses) == 1
        assert restored.synthesis is None
        assert restored.report is None

    def test_synthesis_result_roundtrip(self, sample_analysis_result: AnalysisResult) -> None:
        tc = ThemeComparison(theme="Efficiency", perspectives={"Paper A": "Fast"})
        sr = SynthesisResult(
            overall_summary="Overview.",
            common_themes=["Speed"],
            theme_comparisons=[tc],
            source_analyses=[sample_analysis_result],
        )
        json_str = sr.model_dump_json()
        restored = SynthesisResult.model_validate_json(json_str)
        assert restored.overall_summary == sr.overall_summary
        assert restored.common_themes == sr.common_themes
        assert len(restored.theme_comparisons) == 1
        assert restored.theme_comparisons[0].theme == "Efficiency"
        assert len(restored.source_analyses) == 1
