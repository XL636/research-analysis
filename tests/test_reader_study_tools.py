"""Tests for reader study tools — study guide & FAQ generation fixes.

Covers:
- Fix 1: save_as_note removed from API, no note auto-creation
- Fix 2: focus mode differentiation (STUDY_GUIDE_FOCUS_MODES content differences)
- Fix 2: prompt template has {focus_mode} at the end (highest weight)
- API endpoint integration tests with mocked LLM
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import httpx

from src.api.routes.reader import STUDY_GUIDE_FOCUS_MODES


# ── Unit tests: Focus mode content differentiation ──────────────────


class TestFocusModes:
    """Fix 2: Verify three focus modes produce structurally different prompts."""

    def test_all_three_modes_exist(self):
        assert set(STUDY_GUIDE_FOCUS_MODES.keys()) == {"conceptual", "practical", "review"}

    def test_conceptual_forbids_steps(self):
        text = STUDY_GUIDE_FOCUS_MODES["conceptual"]
        assert "禁止" in text and "操作步骤" in text
        assert "概念" in text or "原理" in text or "定义" in text

    def test_practical_requires_steps(self):
        text = STUDY_GUIDE_FOCUS_MODES["practical"]
        assert "操作步骤" in text
        assert "案例" in text or "示例" in text
        # Should not focus on pure theory
        assert "禁止" in text and "理论" in text

    def test_review_requires_comparison_table(self):
        text = STUDY_GUIDE_FOCUS_MODES["review"]
        assert "对比表" in text or "对比" in text
        assert "记忆口诀" in text or "助记" in text
        assert "自测题" in text or "判断题" in text or "选择题" in text

    def test_modes_are_structurally_different(self):
        """Each mode must have unique keywords not shared by the other two."""
        conceptual = STUDY_GUIDE_FOCUS_MODES["conceptual"]
        practical = STUDY_GUIDE_FOCUS_MODES["practical"]
        review = STUDY_GUIDE_FOCUS_MODES["review"]

        # conceptual unique: "类比", "来源/背景/演进"
        assert "类比" in conceptual
        assert "类比" not in practical
        assert "类比" not in review

        # practical unique: "排错" or "排查"
        assert any(kw in practical for kw in ["排错", "排查"])

        # review unique: "考点清单" or "必考"
        assert any(kw in review for kw in ["考点清单", "必考", "高频必考"])

    def test_all_modes_are_override_instructions(self):
        """Each mode should clearly state it overrides general requirements."""
        for mode, text in STUDY_GUIDE_FOCUS_MODES.items():
            assert "覆盖" in text, f"Mode '{mode}' should contain override instruction"


# ── Unit tests: Prompt template structure ────────────────────────────


class TestPromptTemplate:
    """Fix 2: Verify {focus_mode} is at the end of the prompt template."""

    def test_focus_mode_is_last_placeholder(self):
        prompt_path = Path("config/prompts/reader_study_guide.txt")
        assert prompt_path.exists(), "Study guide prompt template should exist"
        content = prompt_path.read_text(encoding="utf-8")

        # {focus_mode} should appear after all other placeholders
        focus_pos = content.rfind("{focus_mode}")
        assert focus_pos > 0, "{focus_mode} should be in the template"

        # Nothing substantive after {focus_mode} (only whitespace)
        after_focus = content[focus_pos + len("{focus_mode}"):].strip()
        assert after_focus == "", (
            f"{'{focus_mode}'} should be the last content in the template, "
            f"but found: '{after_focus[:50]}...'"
        )

    def test_template_has_all_required_placeholders(self):
        prompt_path = Path("config/prompts/reader_study_guide.txt")
        content = prompt_path.read_text(encoding="utf-8")

        for placeholder in ["{document_title}", "{sampled_content}", "{focus_mode}"]:
            assert placeholder in content, f"Missing placeholder: {placeholder}"


# ── Integration tests: API endpoints ─────────────────────────────────


pytestmark = pytest.mark.anyio


@pytest.fixture
def temp_reader_store(tmp_path):
    """Create a temporary ReaderStore with a test document."""
    from src.store.reader_store import ReaderStore

    db_path = str(tmp_path / "test_reader.db")
    store = ReaderStore(db_path=db_path)

    # Create a test document with some pages
    doc = store.create_document(
        title="Test Document",
        file_name="test.pdf",
        file_type="pdf",
        file_path=str(tmp_path / "test.pdf"),
        total_pages=3,
    )
    store.insert_pages(doc["id"], [
        "Page 1: Introduction to machine learning concepts.",
        "Page 2: Supervised vs unsupervised learning methods.",
        "Page 3: Neural network architectures and training.",
    ])
    return store, doc


@pytest.fixture
async def reader_client(tmp_path, temp_reader_store):
    """Create an httpx test client with mocked reader store."""
    store, _doc = temp_reader_store

    from src.api.app import create_app
    app = create_app()

    # Patch the reader module's _get_store to use our test store
    with patch("src.api.routes.reader._get_store", return_value=store):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as c:
            yield c


class TestStudyGuideEndpoint:
    """Test /reader/{doc_id}/generate/study-guide endpoint."""

    async def test_generate_study_guide_no_save_as_note_param(
        self, reader_client, temp_reader_store
    ):
        """Fix 1: save_as_note param removed, API should not accept it."""
        _store, doc = temp_reader_store

        mock_llm = MagicMock()
        mock_llm.chat_json.return_value = {
            "sections": [
                {"title": "Intro", "content": "Introduction content"},
                {"title": "Methods", "content": "Methods content"},
            ]
        }

        with patch("src.core.llm_client.LLMClient", return_value=mock_llm), \
             patch("src.api.routes.reader._load_config", return_value={"agent_models": {}}):
            # Without save_as_note (default behavior)
            resp = await reader_client.post(
                f"/api/reader/{doc['id']}/generate/study-guide",
                params={"focus": "conceptual"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["sections"]) == 2
            assert data["saved_note_id"] is None

    async def test_generate_study_guide_does_not_create_note(
        self, reader_client, temp_reader_store
    ):
        """Fix 1: Even if old save_as_note=true is passed, no note is created."""
        store, doc = temp_reader_store

        mock_llm = MagicMock()
        mock_llm.chat_json.return_value = {
            "sections": [{"title": "T1", "content": "C1"}]
        }

        with patch("src.core.llm_client.LLMClient", return_value=mock_llm), \
             patch("src.api.routes.reader._load_config", return_value={"agent_models": {}}):
            # Even passing save_as_note=true should be ignored (param removed)
            resp = await reader_client.post(
                f"/api/reader/{doc['id']}/generate/study-guide",
                params={"focus": "conceptual", "save_as_note": "true"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["saved_note_id"] is None

            # Verify no notes were created in the store
            notes = store.list_notes(doc["id"])
            assert len(notes) == 0

    async def test_generate_study_guide_invalid_focus(
        self, reader_client, temp_reader_store
    ):
        """Invalid focus mode returns 400."""
        _store, doc = temp_reader_store

        with patch("src.api.routes.reader._load_config", return_value={"agent_models": {}}):
            resp = await reader_client.post(
                f"/api/reader/{doc['id']}/generate/study-guide",
                params={"focus": "invalid_mode"},
            )
            assert resp.status_code == 400

    async def test_focus_mode_injected_into_prompt(
        self, reader_client, temp_reader_store
    ):
        """Fix 2: Focus mode text is passed to LLM in the prompt."""
        _store, doc = temp_reader_store

        mock_llm = MagicMock()
        mock_llm.chat_json.return_value = {"sections": []}

        for focus in ["conceptual", "practical", "review"]:
            with patch("src.core.llm_client.LLMClient", return_value=mock_llm), \
                 patch("src.api.routes.reader._load_config", return_value={"agent_models": {}}):
                resp = await reader_client.post(
                    f"/api/reader/{doc['id']}/generate/study-guide",
                    params={"focus": focus},
                )
                assert resp.status_code == 200

                # Check the prompt sent to LLM contains focus mode text
                call_args = mock_llm.chat_json.call_args
                prompt = call_args[0][1][0]["content"]  # messages[0]["content"]
                assert STUDY_GUIDE_FOCUS_MODES[focus][:20] in prompt

    async def test_temperature_is_0_5(
        self, reader_client, temp_reader_store
    ):
        """Fix 2: Temperature should be 0.5 (not 0.3)."""
        _store, doc = temp_reader_store

        mock_llm = MagicMock()
        mock_llm.chat_json.return_value = {"sections": []}

        with patch("src.core.llm_client.LLMClient", return_value=mock_llm), \
             patch("src.api.routes.reader._load_config", return_value={"agent_models": {}}):
            await reader_client.post(
                f"/api/reader/{doc['id']}/generate/study-guide",
                params={"focus": "conceptual"},
            )
            call_kwargs = mock_llm.chat_json.call_args
            assert call_kwargs.kwargs.get("temperature") == 0.5 or \
                   (len(call_kwargs.args) > 2 and call_kwargs.args[2] == 0.5) or \
                   call_kwargs[1].get("temperature") == 0.5


class TestFaqEndpoint:
    """Test /reader/{doc_id}/generate/faq endpoint."""

    async def test_generate_faq_no_save_as_note(
        self, reader_client, temp_reader_store
    ):
        """Fix 1: FAQ endpoint no longer has save_as_note."""
        store, doc = temp_reader_store

        mock_llm = MagicMock()
        mock_llm.chat_json.return_value = {
            "questions": [
                {"question": "What is ML?", "answer": "Machine learning is..."},
            ]
        }

        with patch("src.core.llm_client.LLMClient", return_value=mock_llm), \
             patch("src.api.routes.reader._load_config", return_value={"agent_models": {}}):
            resp = await reader_client.post(
                f"/api/reader/{doc['id']}/generate/faq",
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["questions"]) == 1
            assert data["saved_note_id"] is None

            # No notes created
            notes = store.list_notes(doc["id"])
            assert len(notes) == 0

    async def test_generate_faq_ignores_save_as_note_param(
        self, reader_client, temp_reader_store
    ):
        """Fix 1: Even if save_as_note is passed, it's ignored."""
        store, doc = temp_reader_store

        mock_llm = MagicMock()
        mock_llm.chat_json.return_value = {
            "questions": [{"question": "Q1?", "answer": "A1"}]
        }

        with patch("src.core.llm_client.LLMClient", return_value=mock_llm), \
             patch("src.api.routes.reader._load_config", return_value={"agent_models": {}}):
            resp = await reader_client.post(
                f"/api/reader/{doc['id']}/generate/faq",
                params={"save_as_note": "true"},
            )
            assert resp.status_code == 200
            assert resp.json()["saved_note_id"] is None
            assert len(store.list_notes(doc["id"])) == 0

    async def test_faq_doc_not_found(self, reader_client):
        """Non-existent doc returns 404."""
        with patch("src.api.routes.reader._load_config", return_value={"agent_models": {}}):
            resp = await reader_client.post("/api/reader/99999/generate/faq")
            assert resp.status_code == 404


class TestNoteCreationSeparation:
    """Fix 1: Verify that note creation is fully decoupled from generation."""

    async def test_notes_endpoint_still_works(
        self, reader_client, temp_reader_store
    ):
        """Notes can still be created independently via the notes endpoint."""
        _store, doc = temp_reader_store

        resp = await reader_client.post(
            f"/api/reader/{doc['id']}/notes",
            json={
                "content": "# Study Guide\n\nManually saved content",
                "source": "study_guide",
            },
        )
        assert resp.status_code == 200
        note = resp.json()
        assert note["source"] == "study_guide"
        assert "Study Guide" in note["content"]

    async def test_generate_then_save_separately(
        self, reader_client, temp_reader_store
    ):
        """Simulate the fixed flow: generate → display → save as separate action."""
        store, doc = temp_reader_store

        mock_llm = MagicMock()
        mock_llm.chat_json.return_value = {
            "sections": [
                {"title": "Basics", "content": "ML basics content"},
                {"title": "Advanced", "content": "Advanced topics"},
            ]
        }

        # Step 1: Generate study guide (no note created)
        with patch("src.core.llm_client.LLMClient", return_value=mock_llm), \
             patch("src.api.routes.reader._load_config", return_value={"agent_models": {}}):
            gen_resp = await reader_client.post(
                f"/api/reader/{doc['id']}/generate/study-guide",
                params={"focus": "conceptual"},
            )
            assert gen_resp.status_code == 200
            sections = gen_resp.json()["sections"]
            assert len(store.list_notes(doc["id"])) == 0

        # Step 2: Frontend formats and saves as note (separate call)
        formatted = "# 学习指南 — Test Document\n\n"
        for s in sections:
            formatted += f"## {s['title']}\n{s['content']}\n\n"

        save_resp = await reader_client.post(
            f"/api/reader/{doc['id']}/notes",
            json={"content": formatted, "source": "study_guide"},
        )
        assert save_resp.status_code == 200
        assert len(store.list_notes(doc["id"])) == 1

        # Step 3: Saving again creates a second note (frontend prevents this,
        # but backend has no dedup — that's fine, frontend controls it)
        save_resp2 = await reader_client.post(
            f"/api/reader/{doc['id']}/notes",
            json={"content": formatted, "source": "study_guide"},
        )
        assert save_resp2.status_code == 200
        assert len(store.list_notes(doc["id"])) == 2
