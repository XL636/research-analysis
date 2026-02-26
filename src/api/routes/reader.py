"""Reader API routes - document upload, page reading, AI chat, sessions, suggestions."""

from __future__ import annotations

import asyncio
from pathlib import Path

import yaml
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from loguru import logger

from src.api.schemas import (
    CreateSessionRequest,
    DeleteResponse,
    ReaderChatHistoryResponse,
    ReaderChatMessage,
    ReaderChatRequest,
    ReaderChatResponse,
    ReaderDocumentListResponse,
    ReaderDocumentResponse,
    ReaderPageResponse,
    ReaderProgressRequest,
    ReaderSessionListResponse,
    ReaderSessionResponse,
    SuggestedQuestionsResponse,
)
from src.api.services.reader_service import (
    ALLOWED_EXTENSIONS,
    delete_reader_files,
    detect_file_type,
    extract_pages,
    save_reader_file,
)
from src.store.reader_store import ReaderStore

router = APIRouter()

_store: ReaderStore | None = None


def _get_store() -> ReaderStore:
    global _store
    if _store is None:
        _store = ReaderStore()
    return _store


def _load_config() -> dict:
    config_path = Path("config/settings.yaml")
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def _get_or_create_latest_session(store: ReaderStore, doc_id: int) -> dict:
    """Get the most recent session for a document, or create one."""
    sessions = store.list_sessions(doc_id)
    if sessions:
        return sessions[0]  # Already sorted by updated_at DESC
    return store.create_session(doc_id, "默认对话")


# --- Document endpoints ---


@router.post("/upload", response_model=ReaderDocumentResponse)
async def upload_document(
    file: UploadFile = File(..., description="上传文件（PDF/PPTX/DOCX/MD/TXT）"),
):
    """Upload a file, parse into pages, return document info."""
    raw_name = file.filename or "upload"
    filename = Path(raw_name).name
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}",
        )

    contents = await file.read()
    if len(contents) > 100 * 1024 * 1024:  # 100MB
        raise HTTPException(status_code=400, detail="File too large (max 100MB)")

    # Save file
    doc_id_hex, file_path = save_reader_file(filename, contents)

    # Detect type and extract pages
    file_type = detect_file_type(filename)
    try:
        pages = extract_pages(file_path, file_type)
    except Exception as e:
        delete_reader_files(file_path)
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    if not pages:
        pages = [""]

    # Title: use filename without extension
    title = Path(filename).stem

    # Store in DB
    store = _get_store()
    doc = store.create_document(
        title=title,
        file_name=filename,
        file_type=file_type,
        file_path=file_path,
        total_pages=len(pages),
    )
    store.insert_pages(doc["id"], pages)

    # Auto-create first session
    store.create_session(doc["id"], "默认对话")

    return ReaderDocumentResponse(**doc)


@router.get("/documents", response_model=ReaderDocumentListResponse)
async def list_documents():
    """List all reader documents."""
    store = _get_store()
    docs = store.list_documents()
    return ReaderDocumentListResponse(
        documents=[ReaderDocumentResponse(**d) for d in docs]
    )


@router.get("/{doc_id}", response_model=ReaderDocumentResponse)
async def get_document(doc_id: int):
    """Get document details."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return ReaderDocumentResponse(**doc)


@router.delete("/{doc_id}", response_model=DeleteResponse)
async def delete_document(doc_id: int):
    """Delete document, pages, chats, and sessions."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete files
    delete_reader_files(doc["file_path"])
    # Delete from DB (CASCADE handles pages, chats, sessions, suggestions)
    store.delete_document(doc_id)
    return DeleteResponse(success=True, message="Document deleted")


@router.get("/{doc_id}/page/{page_num}", response_model=ReaderPageResponse)
async def get_page(doc_id: int, page_num: int):
    """Get a specific page's text content."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if page_num < 1 or page_num > doc["total_pages"]:
        raise HTTPException(status_code=400, detail=f"Page {page_num} out of range (1-{doc['total_pages']})")

    content = store.get_page_content(doc_id, page_num)
    return ReaderPageResponse(page_num=page_num, content=content or "")


@router.get("/{doc_id}/file")
async def get_file(doc_id: int):
    """Return the original file (for PDF rendering in browser)."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(doc["file_path"])
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    media_types = {
        "pdf": "application/pdf",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "md": "text/markdown",
        "txt": "text/plain",
    }
    media_type = media_types.get(doc["file_type"], "application/octet-stream")
    return FileResponse(
        str(file_path),
        media_type=media_type,
        filename=doc["file_name"],
    )


@router.patch("/{doc_id}/progress", response_model=ReaderDocumentResponse)
async def update_progress(doc_id: int, body: ReaderProgressRequest):
    """Update reading progress (current page)."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    updated = store.update_progress(doc_id, body.current_page)
    return ReaderDocumentResponse(**updated)


# --- Session endpoints ---


@router.post("/{doc_id}/sessions", response_model=ReaderSessionResponse)
async def create_session(doc_id: int, body: CreateSessionRequest | None = None):
    """Create a new chat session for a document."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    title = body.title if body else "新对话"
    session = store.create_session(doc_id, title)
    return ReaderSessionResponse(**session)


@router.get("/{doc_id}/sessions", response_model=ReaderSessionListResponse)
async def list_sessions(doc_id: int):
    """List all chat sessions for a document (with message_count)."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    sessions = store.list_sessions(doc_id)
    return ReaderSessionListResponse(
        sessions=[ReaderSessionResponse(**s) for s in sessions]
    )


@router.delete("/{doc_id}/sessions/{session_id}", response_model=DeleteResponse)
async def delete_session(doc_id: int, session_id: int):
    """Delete a chat session and all its messages."""
    store = _get_store()
    session = store.get_session(session_id)
    if not session or session["document_id"] != doc_id:
        raise HTTPException(status_code=404, detail="Session not found")

    store.delete_session(session_id)
    return DeleteResponse(success=True, message="Session deleted")


# --- Session chat endpoints ---


@router.get("/{doc_id}/sessions/{session_id}/history", response_model=ReaderChatHistoryResponse)
async def get_session_chat_history(doc_id: int, session_id: int):
    """Get chat history for a specific session."""
    store = _get_store()
    session = store.get_session(session_id)
    if not session or session["document_id"] != doc_id:
        raise HTTPException(status_code=404, detail="Session not found")

    history = store.get_chat_history(doc_id, session_id=session_id)
    return ReaderChatHistoryResponse(
        messages=[ReaderChatMessage(**m) for m in history]
    )


@router.post("/{doc_id}/sessions/{session_id}/chat", response_model=ReaderChatResponse)
async def session_chat(doc_id: int, session_id: int, body: ReaderChatRequest):
    """AI chat within a session - answer questions based on current page context."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    session = store.get_session(session_id)
    if not session or session["document_id"] != doc_id:
        raise HTTPException(status_code=404, detail="Session not found")

    config = _load_config()
    reader_conf = config.get("reader", {})
    context_pages = reader_conf.get("context_pages", 1)
    max_history = reader_conf.get("max_chat_history", 20)

    # Build page context
    start_page = max(1, body.page_num - context_pages)
    end_page = min(doc["total_pages"], body.page_num + context_pages)
    page_rows = store.get_page_range(doc_id, start_page, end_page)

    context_parts = []
    for pr in page_rows:
        marker = " (当前页)" if pr["page_num"] == body.page_num else ""
        context_parts.append(f"[第 {pr['page_num']} 页{marker}]\n{pr['content']}")
    page_context = "\n\n---\n\n".join(context_parts)

    # Load prompt template
    prompt_template_path = reader_conf.get(
        "prompt_template", "config/prompts/reader_assistant.txt"
    )
    prompt_path = Path(prompt_template_path)
    if prompt_path.exists():
        system_prompt = prompt_path.read_text(encoding="utf-8")
    else:
        system_prompt = (
            "你是一个阅读辅助助手。基于以下页面内容回答用户问题。\n\n{page_context}"
        )

    system_prompt = system_prompt.replace("{document_title}", doc["title"])
    system_prompt = system_prompt.replace("{page_context}", page_context)

    # Build messages: system + recent session history + current question
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

    chat_history = store.get_chat_history(doc_id, limit=max_history, session_id=session_id)
    for ch in chat_history[-10:]:
        messages.append({"role": ch["role"], "content": ch["content"]})

    messages.append({"role": "user", "content": body.message})

    # Save user message
    store.add_chat(doc_id, "user", body.message, body.page_num, session_id=session_id)

    # Auto-generate session title from first message
    if session["message_count"] == 0:
        auto_title = body.message[:30].strip()
        if auto_title:
            store.update_session_title(session_id, auto_title)

    # Call LLM (in thread to avoid blocking event loop)
    from src.core.llm_client import LLMClient

    model_name = config.get("agent_models", {}).get("reader", "glm-4.5-plus")
    llm = LLMClient()
    try:
        reply = await asyncio.to_thread(
            llm.chat, model_name, messages, temperature=0.7, max_tokens=4096
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI chat failed: {e}")

    # Save assistant message
    assistant_msg = store.add_chat(doc_id, "assistant", reply, body.page_num, session_id=session_id)

    # Touch session updated_at
    store.touch_session(session_id)

    return ReaderChatResponse(
        reply=reply,
        message=ReaderChatMessage(**assistant_msg),
    )


@router.delete("/{doc_id}/sessions/{session_id}/history", response_model=DeleteResponse)
async def clear_session_chat_history(doc_id: int, session_id: int):
    """Clear chat history for a specific session."""
    store = _get_store()
    session = store.get_session(session_id)
    if not session or session["document_id"] != doc_id:
        raise HTTPException(status_code=404, detail="Session not found")

    store.clear_chat(doc_id, session_id=session_id)
    return DeleteResponse(success=True, message="Session chat history cleared")


# --- Suggested questions ---


@router.get("/{doc_id}/suggestions", response_model=SuggestedQuestionsResponse)
async def get_suggestions(doc_id: int, page_num: int = 1):
    """Get AI-generated suggested questions for a page."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if page_num < 1 or page_num > doc["total_pages"]:
        raise HTTPException(status_code=400, detail=f"Page {page_num} out of range")

    config = _load_config()
    reader_conf = config.get("reader", {})
    min_content = reader_conf.get("suggestions_min_content", 50)
    suggestions_count = reader_conf.get("suggestions_count", 3)

    # Check cache
    cached = store.get_suggestions(doc_id, page_num)
    if cached is not None:
        return SuggestedQuestionsResponse(questions=cached, page_num=page_num, cached=True)

    # Get page content
    content = store.get_page_content(doc_id, page_num)
    if not content or len(content.strip()) < min_content:
        return SuggestedQuestionsResponse(questions=[], page_num=page_num, cached=False)

    # Load prompt
    prompt_path_str = reader_conf.get(
        "suggestions_prompt", "config/prompts/reader_suggestions.txt"
    )
    prompt_path = Path(prompt_path_str)
    if prompt_path.exists():
        prompt_template = prompt_path.read_text(encoding="utf-8")
    else:
        prompt_template = (
            "基于以下内容生成{count}个问题，JSON格式返回 {{\"questions\": [...]}}。\n\n{page_content}"
        )

    prompt = prompt_template.replace("{document_title}", doc["title"])
    prompt = prompt.replace("{page_num}", str(page_num))
    prompt = prompt.replace("{count}", str(suggestions_count))
    prompt = prompt.replace("{page_content}", content[:3000])  # Limit content size

    # Call LLM (in thread to avoid blocking event loop)
    from src.core.llm_client import LLMClient

    model_name = reader_conf.get("suggestions_model", "glm-4-flash")
    llm = LLMClient()
    try:
        result = await asyncio.to_thread(
            llm.chat_json,
            model_name,
            [{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=512,
        )
        questions = result.get("questions", [])[:suggestions_count]
    except Exception as e:
        logger.warning(f"Failed to generate suggestions for doc_id={doc_id}, page={page_num}: {e}")
        return SuggestedQuestionsResponse(questions=[], page_num=page_num, cached=False)

    # Save to cache
    if questions:
        store.save_suggestions(doc_id, page_num, questions)

    return SuggestedQuestionsResponse(questions=questions, page_num=page_num, cached=False)


# --- Legacy endpoints (backward compatible) ---


@router.post("/{doc_id}/chat", response_model=ReaderChatResponse)
async def chat(doc_id: int, body: ReaderChatRequest):
    """AI chat - answer questions based on current page context (legacy, uses latest session)."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    session = _get_or_create_latest_session(store, doc_id)
    return await session_chat(doc_id, session["id"], body)


@router.get("/{doc_id}/chat/history", response_model=ReaderChatHistoryResponse)
async def get_chat_history(doc_id: int):
    """Get chat history for a document (legacy, uses latest session)."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    session = _get_or_create_latest_session(store, doc_id)
    history = store.get_chat_history(doc_id, session_id=session["id"])
    return ReaderChatHistoryResponse(
        messages=[ReaderChatMessage(**m) for m in history]
    )


@router.delete("/{doc_id}/chat/history", response_model=DeleteResponse)
async def clear_chat_history(doc_id: int):
    """Clear chat history for a document (legacy, uses latest session)."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    session = _get_or_create_latest_session(store, doc_id)
    store.clear_chat(doc_id, session_id=session["id"])
    return DeleteResponse(success=True, message="Chat history cleared")
