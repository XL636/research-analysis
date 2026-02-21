"""知识库单元测试."""
from __future__ import annotations

import pytest

from src.core.models import AnalysisResult, KeyFinding, MethodologyAssessment
from src.store.knowledge_base import KnowledgeBase


@pytest.fixture
def kb(tmp_path):
    """Create a KnowledgeBase with temporary SQLite db."""
    db_path = str(tmp_path / "test.db")
    return KnowledgeBase(db_path=db_path)


@pytest.fixture
def sample_analysis():
    return AnalysisResult(
        document_title="ML Paper",
        summary="A paper about machine learning optimization.",
        key_findings=[
            KeyFinding(finding="New optimizer found", evidence="Table 3", significance="High"),
        ],
        methodology=MethodologyAssessment(
            approach="Experimental", strengths=["Large scale"], limitations=["Single domain"]
        ),
        contributions=["Novel optimizer algorithm"],
        limitations=["Limited to computer vision"],
        future_work=["Apply to NLP tasks"],
        tags=["ml", "optimization"],
        relevance_score=8.0,
    )


class TestKnowledgeBase:
    def test_store_analysis_returns_doc_id(self, kb, sample_analysis):
        doc_id = kb.store_analysis(sample_analysis, file_path="/tmp/paper.pdf", file_type="pdf")
        assert doc_id > 0

    def test_store_and_retrieve_analysis(self, kb, sample_analysis):
        doc_id = kb.store_analysis(sample_analysis)
        retrieved = kb.get_analysis(doc_id)
        assert retrieved is not None
        assert retrieved.document_title == "ML Paper"
        assert retrieved.summary == sample_analysis.summary
        assert len(retrieved.key_findings) == 1
        assert retrieved.relevance_score == 8.0

    def test_search_finds_stored_document(self, kb, sample_analysis):
        kb.store_analysis(sample_analysis)
        results = kb.search("machine learning")
        assert len(results) > 0
        assert results[0]["title"] == "ML Paper"

    def test_search_returns_empty_for_no_match(self, kb, sample_analysis):
        kb.store_analysis(sample_analysis)
        results = kb.search("quantum computing")
        assert len(results) == 0

    def test_list_documents(self, kb, sample_analysis):
        kb.store_analysis(sample_analysis)
        docs = kb.list_documents()
        assert len(docs) == 1
        assert docs[0]["title"] == "ML Paper"

    def test_list_documents_by_tag(self, kb, sample_analysis):
        kb.store_analysis(sample_analysis)
        # sample_analysis has tags ["ml", "optimization"]
        ml_docs = kb.list_documents(tag="ml")
        assert len(ml_docs) == 1

        other_docs = kb.list_documents(tag="nonexistent")
        assert len(other_docs) == 0

    def test_get_analysis_nonexistent(self, kb):
        result = kb.get_analysis(9999)
        assert result is None

    def test_store_multiple_documents(self, kb):
        a1 = AnalysisResult(
            document_title="Paper 1", summary="About NLP", tags=["nlp"], relevance_score=7.0
        )
        a2 = AnalysisResult(
            document_title="Paper 2", summary="About CV", tags=["cv"], relevance_score=6.0
        )
        id1 = kb.store_analysis(a1)
        id2 = kb.store_analysis(a2)
        assert id1 != id2

        docs = kb.list_documents()
        assert len(docs) == 2

    def test_search_with_tags_in_result(self, kb, sample_analysis):
        kb.store_analysis(sample_analysis)
        results = kb.search("machine learning")
        assert len(results) > 0
        # tags field should contain the stored tags
        assert "ml" in results[0]["tags"]
