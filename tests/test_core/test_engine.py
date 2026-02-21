"""Tests for src/core/engine.py — Pipeline with all agents mocked."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.core.models import (
    AnalysisResult,
    ParsedDocument,
    PipelineContext,
    Report,
    ReviewFeedback,
    SynthesisResult,
)

# Patch target for the ReviewerAgent that the engine imports dynamically.
# engine.py does: from src.agents.reviewer import ReviewerAgent
# Patching the class in its own module replaces it for the dynamic import too.
_REVIEWER_PATCH = "src.agents.reviewer.ReviewerAgent"
_SYNTHESIZER_PATCH = "src.agents.synthesizer.SynthesizerAgent"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _approved_review() -> ReviewFeedback:
    return ReviewFeedback(approved=True, overall_score=9.0, issues=[], suggestions=[])


def _rejected_review() -> ReviewFeedback:
    return ReviewFeedback(
        approved=False, overall_score=4.0, issues=["Incomplete"], suggestions=["Add detail"]
    )


def _wire_standard_mocks(
    MockLLM,
    MockParser,
    MockAnalyzer,
    MockGenerator,
    mock_write,
    *,
    parsed_docs: list,
    analysis_result: AnalysisResult,
    report: Report,
    write_return: str = "/tmp/output.md",
) -> None:
    """Configure the common mock chain used by most pipeline tests."""
    MockLLM.return_value = MagicMock()
    MockParser.return_value.process.return_value = parsed_docs
    MockAnalyzer.return_value.process.return_value = analysis_result
    MockGenerator.return_value.process.return_value = report
    mock_write.return_value = write_return


# ---------------------------------------------------------------------------
# Pipeline.__init__
# ---------------------------------------------------------------------------

class TestPipelineInit:
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_init_creates_llm_and_agents(
        self, MockLLM, MockParser, MockAnalyzer, MockGenerator, tmp_config: str
    ) -> None:
        from src.core.engine import Pipeline

        Pipeline(config_path=tmp_config)

        MockLLM.assert_called_once_with(tmp_config)
        MockParser.assert_called_once()
        MockAnalyzer.assert_called_once()
        MockGenerator.assert_called_once()

    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_init_loads_pipeline_config(
        self, MockLLM, MockParser, MockAnalyzer, MockGenerator, tmp_config: str
    ) -> None:
        from src.core.engine import Pipeline

        pipeline = Pipeline(config_path=tmp_config)

        # tmp_config sets max_review_retries: 1
        assert pipeline.max_review_retries == 1
        assert pipeline.output_dir != ""

    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_init_stores_config_path(
        self, MockLLM, MockParser, MockAnalyzer, MockGenerator, tmp_config: str
    ) -> None:
        from src.core.engine import Pipeline

        pipeline = Pipeline(config_path=tmp_config)
        assert pipeline.config_path == tmp_config


# ---------------------------------------------------------------------------
# Single-file pipeline
# ---------------------------------------------------------------------------

class TestSingleFilePipeline:
    @patch(_REVIEWER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_single_file_returns_populated_context(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        from src.core.engine import Pipeline

        _wire_standard_mocks(
            MockLLM, MockParser, MockAnalyzer, MockGenerator, mock_write,
            parsed_docs=[sample_parsed_doc],
            analysis_result=sample_analysis_result,
            report=sample_report,
        )
        MockReviewer.return_value.process.return_value = _approved_review()

        pipeline = Pipeline(config_path=tmp_config)
        ctx = pipeline.run(input_files=["/tmp/test.pdf"])

        assert isinstance(ctx, PipelineContext)
        assert len(ctx.parsed_documents) == 1
        assert len(ctx.analyses) == 1
        assert ctx.report is not None
        assert ctx.report.title == sample_report.title

    @patch(_REVIEWER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_single_file_output_path_set(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        from src.core.engine import Pipeline

        _wire_standard_mocks(
            MockLLM, MockParser, MockAnalyzer, MockGenerator, mock_write,
            parsed_docs=[sample_parsed_doc],
            analysis_result=sample_analysis_result,
            report=sample_report,
            write_return="/tmp/out/test_report.md",
        )
        MockReviewer.return_value.process.return_value = _approved_review()

        pipeline = Pipeline(config_path=tmp_config)
        ctx = pipeline.run(input_files=["/tmp/test.pdf"])

        assert ctx.output_path == "/tmp/out/test_report.md"

    @patch(_REVIEWER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_single_file_no_synthesis(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        from src.core.engine import Pipeline

        _wire_standard_mocks(
            MockLLM, MockParser, MockAnalyzer, MockGenerator, mock_write,
            parsed_docs=[sample_parsed_doc],
            analysis_result=sample_analysis_result,
            report=sample_report,
        )
        MockReviewer.return_value.process.return_value = _approved_review()

        pipeline = Pipeline(config_path=tmp_config)
        ctx = pipeline.run(input_files=["/tmp/test.pdf"], synthesize=False)

        # Only 1 document → no synthesis path triggered
        assert ctx.synthesis is None

    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_no_parsed_docs_returns_early(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        tmp_config: str,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        from src.core.engine import Pipeline

        MockLLM.return_value = MagicMock()
        MockParser.return_value.process.return_value = []
        MockAnalyzer.return_value.process.return_value = sample_analysis_result
        MockGenerator.return_value.process.return_value = sample_report
        mock_write.return_value = "/tmp/output.md"

        pipeline = Pipeline(config_path=tmp_config)
        ctx = pipeline.run(input_files=["/tmp/nonexistent.pdf"])

        assert ctx.parsed_documents == []
        assert ctx.analyses == []
        assert ctx.report is None

    @patch(_REVIEWER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_input_files_stored_in_context(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        from src.core.engine import Pipeline

        _wire_standard_mocks(
            MockLLM, MockParser, MockAnalyzer, MockGenerator, mock_write,
            parsed_docs=[sample_parsed_doc],
            analysis_result=sample_analysis_result,
            report=sample_report,
        )
        MockReviewer.return_value.process.return_value = _approved_review()

        pipeline = Pipeline(config_path=tmp_config)
        ctx = pipeline.run(input_files=["/tmp/test.pdf"])

        assert ctx.input_files == ["/tmp/test.pdf"]


# ---------------------------------------------------------------------------
# Multi-file pipeline — auto synthesize
# ---------------------------------------------------------------------------

class TestMultiFilePipeline:
    @patch(_REVIEWER_PATCH)
    @patch(_SYNTHESIZER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_multi_file_auto_enables_synthesize(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockSynth,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        from src.core.engine import Pipeline

        second_doc = ParsedDocument(
            file_path="/tmp/test2.pdf",
            file_type=sample_parsed_doc.file_type,
            title="Paper Two",
        )
        second_analysis = AnalysisResult(
            document_title="Paper Two", summary="Second paper summary."
        )
        sample_synthesis = SynthesisResult(
            overall_summary="Combined summary.",
            source_analyses=[sample_analysis_result, second_analysis],
        )

        MockLLM.return_value = MagicMock()
        MockParser.return_value.process.return_value = [sample_parsed_doc, second_doc]
        MockAnalyzer.return_value.process.side_effect = [sample_analysis_result, second_analysis]
        MockSynth.return_value.process.return_value = sample_synthesis
        MockGenerator.return_value.process.return_value = sample_report
        mock_write.return_value = "/tmp/output.md"
        MockReviewer.return_value.process.return_value = _approved_review()

        pipeline = Pipeline(config_path=tmp_config)
        ctx = pipeline.run(
            input_files=["/tmp/test.pdf", "/tmp/test2.pdf"],
            synthesize=False,  # Should be auto-overridden to True
        )

        assert len(ctx.parsed_documents) == 2
        assert len(ctx.analyses) == 2

    @patch(_REVIEWER_PATCH)
    @patch(_SYNTHESIZER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_multi_file_analyzer_called_per_doc(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockSynth,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        from src.core.engine import Pipeline

        second_doc = ParsedDocument(
            file_path="/tmp/test2.pdf",
            file_type=sample_parsed_doc.file_type,
            title="Paper Two",
        )
        second_analysis = AnalysisResult(document_title="Paper Two")
        sample_synthesis = SynthesisResult(
            overall_summary="Combined.",
            source_analyses=[sample_analysis_result, second_analysis],
        )

        MockLLM.return_value = MagicMock()
        MockParser.return_value.process.return_value = [sample_parsed_doc, second_doc]
        MockAnalyzer.return_value.process.side_effect = [sample_analysis_result, second_analysis]
        MockSynth.return_value.process.return_value = sample_synthesis
        MockGenerator.return_value.process.return_value = sample_report
        mock_write.return_value = "/tmp/output.md"
        MockReviewer.return_value.process.return_value = _approved_review()

        pipeline = Pipeline(config_path=tmp_config)
        pipeline.run(input_files=["/tmp/test.pdf", "/tmp/test2.pdf"])

        # AnalyzerAgent.process must be called once per document
        assert MockAnalyzer.return_value.process.call_count == 2


# ---------------------------------------------------------------------------
# Reviewer feedback loop
# ---------------------------------------------------------------------------

class TestReviewerFeedbackLoop:
    @patch(_REVIEWER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_review_approved_on_first_attempt(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
        sample_review_approved: ReviewFeedback,
    ) -> None:
        from src.core.engine import Pipeline

        _wire_standard_mocks(
            MockLLM, MockParser, MockAnalyzer, MockGenerator, mock_write,
            parsed_docs=[sample_parsed_doc],
            analysis_result=sample_analysis_result,
            report=sample_report,
        )
        MockReviewer.return_value.process.return_value = sample_review_approved

        pipeline = Pipeline(config_path=tmp_config)
        ctx = pipeline.run(input_files=["/tmp/test.pdf"])

        assert ctx.review is not None
        assert ctx.review.approved is True
        # Generator called exactly once when review passes immediately
        assert MockGenerator.return_value.process.call_count == 1

    @patch(_REVIEWER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_review_retry_on_rejection(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
        sample_review_rejected: ReviewFeedback,
        sample_review_approved: ReviewFeedback,
    ) -> None:
        """First review rejected → pipeline regenerates → second review approves."""
        from src.core.engine import Pipeline

        revised_report = Report(
            title="Revised Report",
            content="# Revised\n\nImproved content.",
            source_files=["test.pdf"],
        )
        MockLLM.return_value = MagicMock()
        MockParser.return_value.process.return_value = [sample_parsed_doc]
        MockAnalyzer.return_value.process.return_value = sample_analysis_result
        # First generate call → original; second → revised
        MockGenerator.return_value.process.side_effect = [sample_report, revised_report]
        mock_write.return_value = "/tmp/output.md"
        # First review rejects, second approves
        MockReviewer.return_value.process.side_effect = [
            sample_review_rejected,
            sample_review_approved,
        ]

        pipeline = Pipeline(config_path=tmp_config)
        pipeline.run(input_files=["/tmp/test.pdf"])

        # Generator should have been called twice (original + one regeneration)
        assert MockGenerator.return_value.process.call_count == 2

    @patch(_REVIEWER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_review_stops_after_max_retries(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
        sample_review_rejected: ReviewFeedback,
    ) -> None:
        """With max_review_retries=1, pipeline runs at most 2 total generate calls."""
        from src.core.engine import Pipeline

        revised_report = Report(
            title="Revised", content="# R\nContent.", source_files=[]
        )
        MockLLM.return_value = MagicMock()
        MockParser.return_value.process.return_value = [sample_parsed_doc]
        MockAnalyzer.return_value.process.return_value = sample_analysis_result
        MockGenerator.return_value.process.side_effect = [sample_report, revised_report]
        mock_write.return_value = "/tmp/output.md"
        # Always reject
        MockReviewer.return_value.process.return_value = sample_review_rejected

        pipeline = Pipeline(config_path=tmp_config)
        # tmp_config: max_review_retries=1 → loop iterates at most 2 times
        ctx = pipeline.run(input_files=["/tmp/test.pdf"])

        # Generator: 1 initial + at most max_review_retries re-generations
        assert MockGenerator.return_value.process.call_count <= 2
        assert ctx.report is not None


# ---------------------------------------------------------------------------
# _write_output
# ---------------------------------------------------------------------------

class TestWriteOutput:
    @patch(_REVIEWER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_write_output_markdown_calls_write_markdown(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        from src.core.engine import Pipeline

        _wire_standard_mocks(
            MockLLM, MockParser, MockAnalyzer, MockGenerator, mock_write,
            parsed_docs=[sample_parsed_doc],
            analysis_result=sample_analysis_result,
            report=sample_report,
            write_return="/tmp/output/test_report.md",
        )
        MockReviewer.return_value.process.return_value = _approved_review()

        pipeline = Pipeline(config_path=tmp_config)
        ctx = pipeline.run(input_files=["/tmp/test.pdf"], output_format="markdown")

        mock_write.assert_called_once()
        assert ctx.output_path == "/tmp/output/test_report.md"

    @patch(_REVIEWER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_write_output_explicit_path_used(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        from src.core.engine import Pipeline

        explicit = "/custom/path/report.md"
        _wire_standard_mocks(
            MockLLM, MockParser, MockAnalyzer, MockGenerator, mock_write,
            parsed_docs=[sample_parsed_doc],
            analysis_result=sample_analysis_result,
            report=sample_report,
            write_return=explicit,
        )
        MockReviewer.return_value.process.return_value = _approved_review()

        pipeline = Pipeline(config_path=tmp_config)
        pipeline.run(
            input_files=["/tmp/test.pdf"],
            output_format="markdown",
            output_path=explicit,
        )

        # write_markdown must be called with the explicit output path
        call_args = mock_write.call_args
        passed_path = call_args[0][1] if call_args[0] else call_args[1].get("output_path", "")
        assert passed_path == explicit

    @patch(_REVIEWER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_write_output_auto_generates_md_path(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        from src.core.engine import Pipeline

        _wire_standard_mocks(
            MockLLM, MockParser, MockAnalyzer, MockGenerator, mock_write,
            parsed_docs=[sample_parsed_doc],
            analysis_result=sample_analysis_result,
            report=sample_report,
        )
        # Return the path that write_markdown was called with, so we can inspect it
        mock_write.side_effect = lambda report, path: path
        MockReviewer.return_value.process.return_value = _approved_review()

        pipeline = Pipeline(config_path=tmp_config)
        ctx = pipeline.run(input_files=["/tmp/myfile.pdf"], output_format="markdown")

        # Auto-generated path should end with .md and include the input stem
        assert ctx.output_path.endswith(".md")
        assert "myfile" in ctx.output_path

    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_write_output_no_report_returns_empty(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        tmp_config: str,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        from src.core.engine import Pipeline

        MockLLM.return_value = MagicMock()
        MockParser.return_value.process.return_value = []  # Nothing parsed
        MockAnalyzer.return_value.process.return_value = sample_analysis_result
        MockGenerator.return_value.process.return_value = sample_report
        mock_write.return_value = "/tmp/output.md"

        pipeline = Pipeline(config_path=tmp_config)
        ctx = pipeline.run(input_files=["/tmp/ghost.pdf"])

        assert ctx.output_path == ""
        mock_write.assert_not_called()

    @patch(_REVIEWER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_write_output_docx_fallback_to_markdown(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        """When the docx writer is unavailable (ImportError), falls back to write_markdown."""
        from src.core.engine import Pipeline

        _wire_standard_mocks(
            MockLLM, MockParser, MockAnalyzer, MockGenerator, mock_write,
            parsed_docs=[sample_parsed_doc],
            analysis_result=sample_analysis_result,
            report=sample_report,
            write_return="/tmp/output.md",
        )
        MockReviewer.return_value.process.return_value = _approved_review()

        # Make the docx writer import fail by pointing to a non-existent module
        import sys
        original = sys.modules.get("src.outputs.docx_writer")
        sys.modules["src.outputs.docx_writer"] = None  # type: ignore[assignment]
        try:
            pipeline = Pipeline(config_path=tmp_config)
            pipeline.run(
                input_files=["/tmp/test.pdf"],
                output_format="docx",
                output_path="/tmp/report.docx",
            )
        finally:
            if original is None:
                sys.modules.pop("src.outputs.docx_writer", None)
            else:
                sys.modules["src.outputs.docx_writer"] = original

        # Fallback write_markdown should have been called
        mock_write.assert_called_once()

    @patch(_REVIEWER_PATCH)
    @patch("src.core.engine.write_markdown")
    @patch("src.core.engine.GeneratorAgent")
    @patch("src.core.engine.AnalyzerAgent")
    @patch("src.core.engine.ParserAgent")
    @patch("src.core.engine.LLMClient")
    def test_output_format_stored_in_context(
        self,
        MockLLM,
        MockParser,
        MockAnalyzer,
        MockGenerator,
        mock_write,
        MockReviewer,
        tmp_config: str,
        sample_parsed_doc: ParsedDocument,
        sample_analysis_result: AnalysisResult,
        sample_report: Report,
    ) -> None:
        from src.core.engine import Pipeline

        _wire_standard_mocks(
            MockLLM, MockParser, MockAnalyzer, MockGenerator, mock_write,
            parsed_docs=[sample_parsed_doc],
            analysis_result=sample_analysis_result,
            report=sample_report,
        )
        MockReviewer.return_value.process.return_value = _approved_review()

        pipeline = Pipeline(config_path=tmp_config)
        ctx = pipeline.run(input_files=["/tmp/test.pdf"], output_format="markdown")

        assert ctx.output_format == "markdown"
