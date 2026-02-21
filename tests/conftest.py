"""共享 pytest fixtures."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from src.core.models import (
    ParsedDocument, DocumentSection, FileType,
    AnalysisResult, KeyFinding, MethodologyAssessment,
    Report, ReviewFeedback,
)


@pytest.fixture
def sample_section() -> DocumentSection:
    return DocumentSection(title="Introduction", content="This is the introduction.", level=2)


@pytest.fixture
def sample_parsed_doc(sample_section: DocumentSection) -> ParsedDocument:
    return ParsedDocument(
        file_path="/tmp/test.pdf",
        file_type=FileType.PDF,
        title="Test Paper",
        authors=["Author A"],
        abstract="This is an abstract.",
        sections=[sample_section],
        raw_text="Full raw text here.",
    )


@pytest.fixture
def sample_key_finding() -> KeyFinding:
    return KeyFinding(finding="Key discovery", evidence="Table 1", significance="High impact")


@pytest.fixture
def sample_analysis_result(sample_key_finding: KeyFinding) -> AnalysisResult:
    return AnalysisResult(
        document_title="Test Paper",
        summary="Paper summary here.",
        key_findings=[sample_key_finding],
        methodology=MethodologyAssessment(
            approach="Experimental", strengths=["Robust"], limitations=["Small sample"]
        ),
        contributions=["New method"],
        limitations=["Limited scope"],
        future_work=["More experiments"],
        tags=["ml", "nlp"],
        relevance_score=8.5,
    )


@pytest.fixture
def sample_report() -> Report:
    return Report(
        title="Test Report",
        content="# Test Report\n\nReport content here.",
        source_files=["test.pdf"],
    )


@pytest.fixture
def sample_review_approved() -> ReviewFeedback:
    return ReviewFeedback(approved=True, overall_score=8.0, issues=[], suggestions=["Minor tweak"])


@pytest.fixture
def sample_review_rejected() -> ReviewFeedback:
    return ReviewFeedback(
        approved=False, overall_score=5.0,
        issues=["Missing details"], suggestions=["Add more evidence"],
    )


@pytest.fixture
def mock_llm_client():
    """Mock LLMClient that returns configurable responses."""
    from src.core.llm_client import LLMClient
    mock = MagicMock(spec=LLMClient)
    mock.chat.return_value = "Mock LLM response"
    mock.chat_json.return_value = {}
    mock.available_models = ["deepseek-chat", "qwen-plus"]
    return mock


@pytest.fixture
def tmp_config(tmp_path) -> str:
    """Create a temporary settings.yaml for testing."""
    import yaml
    config = {
        "models": {
            "test-model": {
                "provider": "test",
                "base_url": "http://localhost:8000",
                "model": "test-v1",
                "api_key_env": "TEST_API_KEY",
            }
        },
        "agent_models": {
            "parser": "test-model",
            "analyzer": "test-model",
            "synthesizer": "test-model",
            "generator": "test-model",
            "reviewer": "test-model",
        },
        "pipeline": {
            "max_review_retries": 1,
            "output_dir": str(tmp_path / "output"),
        },
        "knowledge_base": {
            "db_path": str(tmp_path / "test.db"),
        },
    }
    config_path = tmp_path / "settings.yaml"
    config_path.write_text(yaml.dump(config), encoding="utf-8")
    return str(config_path)
