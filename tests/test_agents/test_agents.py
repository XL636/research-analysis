"""Agent 单元测试."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.agents.analyzer import AnalyzerAgent
from src.agents.generator import GeneratorAgent
from src.agents.reviewer import ReviewerAgent
from src.agents.synthesizer import SynthesizerAgent
from src.core.llm_client import LLMClient
from src.core.models import (
    AnalysisResult,
    ParsedDocument,
    Report,
    ReviewFeedback,
    SynthesisResult,
    FileType,
    DocumentSection,
    KeyFinding,
    MethodologyAssessment,
)


@pytest.fixture
def mock_llm():
    mock = MagicMock(spec=LLMClient)
    return mock


@pytest.fixture
def tmp_config_path(tmp_path):
    """Create minimal config for agent tests."""
    import yaml
    config = {
        "models": {
            "test-model": {
                "provider": "test",
                "base_url": "http://localhost",
                "model": "test-v1",
                "api_key_env": "TEST_KEY",
            }
        },
        "agent_models": {
            "analyzer": "test-model",
            "generator": "test-model",
            "reviewer": "test-model",
            "synthesizer": "test-model",
        },
    }
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(yaml.dump(config), encoding="utf-8")
    return str(config_path)


# ========== AnalyzerAgent Tests ==========

class TestAnalyzerAgent:
    def test_process_returns_analysis_result(self, mock_llm, tmp_config_path):
        mock_llm.chat_json.return_value = {
            "summary": "A study on deep learning methods.",
            "key_findings": [
                {"finding": "Transformers outperform RNNs", "evidence": "Table 2", "significance": "Major"}
            ],
            "methodology": {"approach": "Experimental", "strengths": ["Large dataset"], "limitations": ["Single domain"]},
            "contributions": ["New architecture proposed"],
            "limitations": ["Limited to English"],
            "future_work": ["Multilingual extension"],
            "tags": ["deep-learning", "nlp"],
            "relevance_score": 8.5,
        }

        agent = AnalyzerAgent(mock_llm, tmp_config_path)
        doc = ParsedDocument(
            file_path="/tmp/test.pdf",
            file_type=FileType.PDF,
            title="Test Paper",
            sections=[DocumentSection(title="Intro", content="Some content")],
            raw_text="Full text",
        )
        result = agent.process(doc)

        assert isinstance(result, AnalysisResult)
        assert result.document_title == "Test Paper"
        assert result.summary == "A study on deep learning methods."
        assert len(result.key_findings) == 1
        assert result.key_findings[0].finding == "Transformers outperform RNNs"
        assert result.relevance_score == 8.5
        assert "deep-learning" in result.tags

    def test_process_with_minimal_response(self, mock_llm, tmp_config_path):
        mock_llm.chat_json.return_value = {"summary": "Brief summary"}
        agent = AnalyzerAgent(mock_llm, tmp_config_path)
        doc = ParsedDocument(
            file_path="/tmp/test.pdf", file_type=FileType.PDF, title="Test", raw_text="text"
        )
        result = agent.process(doc)
        assert result.summary == "Brief summary"
        assert result.key_findings == []

    def test_process_uses_file_path_when_no_title(self, mock_llm, tmp_config_path):
        mock_llm.chat_json.return_value = {"summary": "Summary"}
        agent = AnalyzerAgent(mock_llm, tmp_config_path)
        doc = ParsedDocument(
            file_path="/tmp/test.pdf", file_type=FileType.PDF, title="", raw_text="text"
        )
        result = agent.process(doc)
        assert result.document_title == "/tmp/test.pdf"


# ========== GeneratorAgent Tests ==========

class TestGeneratorAgent:
    def test_process_with_analysis_list(self, mock_llm, tmp_config_path):
        mock_llm.chat.return_value = "# Generated Report\n\nThis is the report content."

        agent = GeneratorAgent(mock_llm, tmp_config_path)
        analysis = AnalysisResult(
            document_title="Paper A",
            summary="Summary of Paper A",
            tags=["ml"],
            relevance_score=7.0,
        )
        result = agent.process([analysis])

        assert isinstance(result, Report)
        assert result.content == "# Generated Report\n\nThis is the report content."
        assert result.title == "Paper A"  # single analysis → use its title

    def test_process_with_multiple_analyses(self, mock_llm, tmp_config_path):
        mock_llm.chat.return_value = "# Multi Report\n\nContent"

        agent = GeneratorAgent(mock_llm, tmp_config_path)
        analyses = [
            AnalysisResult(document_title="A", summary="Summary A", relevance_score=7.0),
            AnalysisResult(document_title="B", summary="Summary B", relevance_score=8.0),
        ]
        result = agent.process(analyses)
        assert result.title == "多文档分析报告"

    def test_process_with_synthesis_result(self, mock_llm, tmp_config_path):
        mock_llm.chat.return_value = "# Synthesis Report\n\nContent"

        agent = GeneratorAgent(mock_llm, tmp_config_path)
        synthesis = SynthesisResult(
            overall_summary="Overall summary",
            common_themes=["AI"],
            source_analyses=[
                AnalysisResult(document_title="X", summary="S", relevance_score=6.0)
            ],
        )
        result = agent.process(synthesis)
        assert result.title == "综合分析报告"
        assert isinstance(result, Report)

    def test_process_with_feedback(self, mock_llm, tmp_config_path):
        mock_llm.chat.return_value = "# Improved Report"

        agent = GeneratorAgent(mock_llm, tmp_config_path)
        analysis = AnalysisResult(document_title="A", summary="S", relevance_score=7.0)
        feedback = ReviewFeedback(
            approved=False, overall_score=5.0,
            issues=["Too short"], suggestions=["Add details"],
        )
        result = agent.process([analysis], feedback=feedback)
        assert result.content == "# Improved Report"
        # Verify LLM was called with feedback info
        call_args = mock_llm.chat.call_args
        user_msg = call_args[0][1][1]["content"]  # messages[1] is user message
        assert "评审反馈" in user_msg


# ========== ReviewerAgent Tests ==========

class TestReviewerAgent:
    def test_process_approved(self, mock_llm, tmp_config_path):
        mock_llm.chat_json.return_value = {
            "approved": True,
            "overall_score": 8.5,
            "issues": [],
            "suggestions": ["Could add more examples"],
            "details": "Good quality report.",
        }

        agent = ReviewerAgent(mock_llm, tmp_config_path)
        report = Report(title="Test Report", content="# Report\nContent here", source_files=["a.pdf"])
        result = agent.process(report)

        assert isinstance(result, ReviewFeedback)
        assert result.approved is True
        assert result.overall_score == 8.5

    def test_process_rejected(self, mock_llm, tmp_config_path):
        mock_llm.chat_json.return_value = {
            "approved": False,
            "overall_score": 4.0,
            "issues": ["Missing methodology section", "Factual errors"],
            "suggestions": ["Rewrite the methods section"],
            "details": "Needs significant improvements.",
        }

        agent = ReviewerAgent(mock_llm, tmp_config_path)
        report = Report(title="Test Report", content="# Report\nBrief content", source_files=["a.pdf"])
        result = agent.process(report)

        assert result.approved is False
        assert result.overall_score == 4.0
        assert len(result.issues) == 2


# ========== SynthesizerAgent Tests ==========

class TestSynthesizerAgent:
    def _make_analysis(self, title: str, summary: str) -> AnalysisResult:
        return AnalysisResult(
            document_title=title,
            summary=summary,
            key_findings=[KeyFinding(finding="Finding", evidence="Evidence", significance="High")],
            methodology=MethodologyAssessment(approach="Method"),
            tags=["test"],
            relevance_score=7.0,
        )

    def test_process_returns_synthesis_result(self, mock_llm, tmp_config_path):
        mock_llm.chat_json.return_value = {
            "overall_summary": "Both papers address ML challenges.",
            "common_themes": ["Machine learning", "Optimization"],
            "key_differences": ["Different datasets used"],
            "theme_comparisons": [
                {"theme": "Optimization", "perspectives": {"Paper A": "SGD", "Paper B": "Adam"}}
            ],
            "research_gaps": ["No real-world deployment"],
            "recommendations": ["Test in production"],
        }

        agent = SynthesizerAgent(mock_llm, tmp_config_path)
        analyses = [
            self._make_analysis("Paper A", "Summary A"),
            self._make_analysis("Paper B", "Summary B"),
        ]
        result = agent.process(analyses)

        assert isinstance(result, SynthesisResult)
        assert result.overall_summary == "Both papers address ML challenges."
        assert len(result.common_themes) == 2
        assert len(result.theme_comparisons) == 1
        assert result.source_analyses == analyses

    def test_process_raises_if_less_than_2_docs(self, mock_llm, tmp_config_path):
        agent = SynthesizerAgent(mock_llm, tmp_config_path)
        analysis = self._make_analysis("Paper A", "Summary A")
        with pytest.raises(ValueError, match="至少需要 2 篇"):
            agent.process([analysis])

    def test_process_with_empty_response_fields(self, mock_llm, tmp_config_path):
        mock_llm.chat_json.return_value = {
            "overall_summary": "Brief",
        }
        agent = SynthesizerAgent(mock_llm, tmp_config_path)
        analyses = [
            self._make_analysis("A", "S1"),
            self._make_analysis("B", "S2"),
        ]
        result = agent.process(analyses)
        assert result.overall_summary == "Brief"
        assert result.common_themes == []
        assert result.theme_comparisons == []
