"""Reader API routes - document upload, page reading, AI chat, sessions, suggestions."""

from __future__ import annotations

import asyncio
import json
import queue
import threading
from pathlib import Path

import yaml
from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from loguru import logger

from src.api.schemas import (
    CreateNoteRequest,
    CreateSessionRequest,
    DeleteResponse,
    DocumentOverviewResponse,
    FaqResponse,
    NoteListResponse,
    NoteResponse,
    OutlineItem,
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
    StudyGuideResponse,
    SuggestedQuestionsResponse,
    UpdateNoteRequest,
)
from src.api.services.reader_service import (
    ALLOWED_EXTENSIONS,
    delete_reader_files,
    detect_file_type,
    extract_pages,
    sample_document_content,
    save_reader_file,
)
from src.store.reader_store import ReaderStore

router = APIRouter()

# --- Agent mode tool definitions (OpenAI Function Calling format) ---

AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_pages",
            "description": "在当前文档中全文搜索页面内容，返回最相关的页面列表",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_page",
            "description": "获取文档中指定页码的完整内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_num": {"type": "integer", "description": "页码（从1开始）"},
                },
                "required": ["page_num"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "在知识库中搜索已分析过的文档，可以找到相关研究和分析结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_document_info",
            "description": "获取当前文档的元信息（标题、总页数、文件类型等）",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

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


def _select_context_pages_fixed(
    store: ReaderStore, doc: dict, current_page: int, reader_conf: dict,
) -> list[int]:
    """Fixed strategy: ±N pages around current page."""
    context_pages = reader_conf.get("context_pages", 1)
    start = max(1, current_page - context_pages)
    end = min(doc["total_pages"], current_page + context_pages)
    return list(range(start, end + 1))


def _select_context_pages_keyword(
    store: ReaderStore, doc_id: int, question: str, current_page: int, reader_conf: dict,
) -> list[int]:
    """Keyword (FTS) strategy: search most relevant pages, always include current page."""
    limit = reader_conf.get("context_search_limit", 5)
    try:
        results = store.search_pages(doc_id, question, limit=limit)
        page_nums = {r["page_num"] for r in results}
    except Exception:
        page_nums = set()
    page_nums.add(current_page)
    return sorted(page_nums)


def _select_context_pages_smart(
    store: ReaderStore, doc_id: int, question: str, current_page: int,
    reader_conf: dict, llm, config: dict,
) -> list[int]:
    """Smart strategy: FTS coarse filter + LLM rerank."""
    candidates = store.search_pages(doc_id, question, limit=8)
    if not candidates:
        return [current_page]

    summaries = [f"第{c['page_num']}页: {c['content'][:200]}" for c in candidates]
    model = reader_conf.get("suggestions_model", "glm-4-flash")
    prompt = (
        f"用户在第{current_page}页问：{question}\n\n候选页面：\n"
        + "\n".join(summaries)
        + '\n\n请返回最相关的页码（JSON数组），最多5个。格式：{"pages": [2, 5, 8]}'
    )

    try:
        result = llm.chat_json(
            model,
            [
                {"role": "system", "content": "你是页面相关性评估助手。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=128,
        )
        pages = set(result.get("pages", []))
    except Exception:
        pages = {c["page_num"] for c in candidates[:3]}

    pages.add(current_page)
    return sorted(pages)


def _build_page_context(
    store: ReaderStore, doc: dict, question: str, current_page: int,
    reader_conf: dict, config: dict, llm=None,
) -> str:
    """Build page context string based on configured strategy."""
    strategy = reader_conf.get("context_strategy", "fixed")
    doc_id = doc["id"]

    if strategy == "keyword":
        page_nums = _select_context_pages_keyword(store, doc_id, question, current_page, reader_conf)
    elif strategy == "smart":
        page_nums = _select_context_pages_smart(store, doc_id, question, current_page, reader_conf, llm, config)
    else:  # "fixed"
        page_nums = _select_context_pages_fixed(store, doc, current_page, reader_conf)

    page_rows = store.get_pages_by_nums(doc_id, page_nums)

    context_parts = []
    for pr in page_rows:
        marker = " (当前页)" if pr["page_num"] == current_page else ""
        context_parts.append(f"[第 {pr['page_num']} 页{marker}]\n{pr['content']}")
    return "\n\n---\n\n".join(context_parts)


def _execute_agent_tool(tool_name: str, args: dict, doc_id: int, store: ReaderStore, kb) -> str:
    """Execute an Agent tool call, return result string."""
    if tool_name == "search_pages":
        results = store.search_pages(doc_id, args["query"], limit=5)
        if not results:
            return "未找到相关页面。"
        lines = [
            f"第{r['page_num']}页（相关度 rank={r['rank']:.2f}）:\n{r['content'][:300]}"
            for r in results
        ]
        return "\n\n---\n".join(lines)

    elif tool_name == "get_page":
        content = store.get_page_content(doc_id, args["page_num"])
        if not content:
            return f"第{args['page_num']}页不存在或无内容。"
        return f"[第{args['page_num']}页内容]\n{content}"

    elif tool_name == "search_knowledge_base":
        results = kb.search(args["query"], limit=5)
        if not results:
            return "知识库中未找到相关文档。"
        lines = [f"《{r['title']}》: {r.get('summary', '')[:200]}" for r in results]
        return "\n\n".join(lines)

    elif tool_name == "get_document_info":
        doc = store.get_document(doc_id)
        return json.dumps(
            {
                "title": doc["title"],
                "total_pages": doc["total_pages"],
                "file_type": doc["file_type"],
            },
            ensure_ascii=False,
        )

    return "未知工具。"


def _run_agent_stream(
    llm, model_name: str, messages: list[dict], tools: list[dict],
    doc_id: int, store: ReaderStore, kb, q: queue.Queue, max_iter: int = 5,
) -> None:
    """Agent tool loop + final streaming output. Runs in a background thread."""
    for _i in range(max_iter):
        # Non-streaming call for tool decision phase
        client, model_id = llm._get_client(model_name)
        response = client.chat.completions.create(
            model=model_id,
            messages=messages,
            tools=tools,
            temperature=0.7,
            max_tokens=4096,
        )
        msg = response.choices[0].message

        if msg.tool_calls:
            # Append assistant message with tool calls
            messages.append(msg.model_dump())
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                q.put(("tool_use", tc.function.name, args))
                result = _execute_agent_tool(tc.function.name, args, doc_id, store, kb)
                summary = result[:100] + "..." if len(result) > 100 else result
                q.put(("tool_result", tc.function.name, summary))
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })
        else:
            # No tool calls → final reply, stream it
            for chunk in llm.stream_chat(model_name, messages, temperature=0.7, max_tokens=4096):
                q.put(("delta", chunk))
            break
    else:
        # Max iterations reached, force final reply without tools
        for chunk in llm.stream_chat(model_name, messages, temperature=0.7, max_tokens=4096):
            q.put(("delta", chunk))
    q.put(None)  # End signal


async def _prepare_chat_context(
    doc_id: int, session_id: int, body: ReaderChatRequest,
) -> tuple[dict, list[dict[str, str]], str]:
    """Validate, build context, save user message. Returns (doc, messages, model_name)."""
    from src.core.llm_client import LLMClient

    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    session = store.get_session(session_id)
    if not session or session["document_id"] != doc_id:
        raise HTTPException(status_code=404, detail="Session not found")

    config = _load_config()
    reader_conf = config.get("reader", {})
    max_history = reader_conf.get("max_chat_history", 20)

    llm = LLMClient()
    agent_models = config.get("agent_models", {})
    if body.agent_mode:
        model_name = agent_models.get("reader_agent", agent_models.get("reader", "glm-4-plus"))
    else:
        model_name = agent_models.get("reader", "glm-4-plus")

    # Build page context using strategy
    page_context = _build_page_context(
        store, doc, body.message, body.page_num, reader_conf, config, llm=llm,
    )

    # Load prompt template (agent mode uses a different prompt)
    if body.agent_mode:
        prompt_template_path = "config/prompts/reader_agent.txt"
    else:
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

    # Build overview context if available (T-93b)
    overview_context = ""
    try:
        overview = store.get_overview(doc["id"])
        if overview:
            overview_context = f"[文档概览]\n{overview['summary']}"
            if overview.get("key_topics"):
                import json as _json
                topics = _json.loads(overview["key_topics"]) if isinstance(overview["key_topics"], str) else overview["key_topics"]
                if topics:
                    overview_context += f"\n关键主题：{', '.join(topics)}"
    except Exception:
        pass

    system_prompt = system_prompt.replace("{document_title}", doc["title"])
    system_prompt = system_prompt.replace("{current_page}", str(body.page_num))
    system_prompt = system_prompt.replace("{page_context}", page_context)
    system_prompt = system_prompt.replace("{overview_context}", overview_context)

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

    return doc, messages, model_name


@router.post("/{doc_id}/sessions/{session_id}/chat", response_model=ReaderChatResponse)
async def session_chat(doc_id: int, session_id: int, body: ReaderChatRequest):
    """AI chat within a session - answer questions based on current page context."""
    from src.core.llm_client import LLMClient

    doc, messages, model_name = await _prepare_chat_context(doc_id, session_id, body)

    llm = LLMClient()
    try:
        reply = await asyncio.to_thread(
            llm.chat, model_name, messages, temperature=0.7, max_tokens=4096
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI chat failed: {e}")

    store = _get_store()
    assistant_msg = store.add_chat(doc_id, "assistant", reply, body.page_num, session_id=session_id)
    store.touch_session(session_id)

    return ReaderChatResponse(
        reply=reply,
        message=ReaderChatMessage(**assistant_msg),
    )


@router.post("/{doc_id}/sessions/{session_id}/stream-chat")
async def session_stream_chat(doc_id: int, session_id: int, body: ReaderChatRequest):
    """SSE streaming AI chat within a session."""
    from src.core.llm_client import LLMClient

    doc, messages, model_name = await _prepare_chat_context(doc_id, session_id, body)

    async def event_generator():
        full_reply = ""
        try:
            q: queue.Queue = queue.Queue()

            if body.agent_mode:
                # Agent mode: use agent_model, with tool calling loop
                config = _load_config()
                reader_conf = config.get("reader", {})
                agent_model = reader_conf.get("agent_model", model_name)
                max_iter = reader_conf.get("agent_max_iterations", 5)

                def _run():
                    try:
                        llm = LLMClient()
                        store = _get_store()
                        from src.store.knowledge_base import KnowledgeBase
                        kb = KnowledgeBase()
                        _run_agent_stream(
                            llm, agent_model, messages, AGENT_TOOLS,
                            doc_id, store, kb, q, max_iter=max_iter,
                        )
                    except Exception as e:
                        q.put(("error", str(e)))
                        q.put(None)

                threading.Thread(target=_run, daemon=True).start()

                while True:
                    item = await asyncio.to_thread(q.get)
                    if item is None:
                        break
                    if item[0] == "tool_use":
                        yield f"data: {json.dumps({'type': 'tool_use', 'tool': item[1], 'args': item[2]}, ensure_ascii=False)}\n\n"
                    elif item[0] == "tool_result":
                        yield f"data: {json.dumps({'type': 'tool_result', 'tool': item[1], 'summary': item[2]}, ensure_ascii=False)}\n\n"
                    elif item[0] == "delta":
                        full_reply += item[1]
                        yield f"data: {json.dumps({'type': 'delta', 'content': item[1]}, ensure_ascii=False)}\n\n"
                    elif item[0] == "error":
                        yield f"data: {json.dumps({'type': 'error', 'message': item[1]}, ensure_ascii=False)}\n\n"
                        return
            else:
                # Normal mode: direct streaming
                def _run():
                    try:
                        llm = LLMClient()
                        for chunk in llm.stream_chat(
                            model_name, messages, temperature=0.7, max_tokens=4096
                        ):
                            q.put(chunk)
                    finally:
                        q.put(None)

                threading.Thread(target=_run, daemon=True).start()

                while True:
                    chunk = await asyncio.to_thread(q.get)
                    if chunk is None:
                        break
                    full_reply += chunk
                    yield f"data: {json.dumps({'type': 'delta', 'content': chunk}, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error(f"Stream chat error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
            return

        # Save complete reply
        store = _get_store()
        msg = store.add_chat(doc_id, "assistant", full_reply, body.page_num, session_id=session_id)
        store.touch_session(session_id)
        yield f"data: {json.dumps({'type': 'done', 'message': msg}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
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

    agent_models = config.get("agent_models", {})
    model_name = agent_models.get("reader_suggestions", reader_conf.get("suggestions_model", "glm-4-flash"))
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


# --- Document Overview ---


@router.get("/{doc_id}/overview", response_model=DocumentOverviewResponse)
async def get_overview(doc_id: int):
    """Get document overview (summary, topics, outline)."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    overview = store.get_overview(doc_id)
    if not overview:
        raise HTTPException(status_code=404, detail="Overview not generated yet")

    # Parse JSON fields
    key_topics = json.loads(overview["key_topics"]) if isinstance(overview["key_topics"], str) else overview["key_topics"]
    outline_raw = json.loads(overview["outline"]) if isinstance(overview["outline"], str) else overview["outline"]
    outline = [OutlineItem(**item) if isinstance(item, dict) else item for item in outline_raw]

    return DocumentOverviewResponse(
        id=overview["id"],
        document_id=doc_id,
        summary=overview["summary"],
        key_topics=key_topics,
        outline=outline,
        created_at=overview.get("created_at", ""),
        updated_at=overview.get("updated_at", ""),
    )


@router.post("/{doc_id}/overview/regenerate", response_model=DocumentOverviewResponse)
async def regenerate_overview(doc_id: int):
    """Generate or regenerate document overview using LLM."""
    from src.core.llm_client import LLMClient

    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    config = _load_config()
    agent_models = config.get("agent_models", {})
    model_name = agent_models.get("reader", "glm-4-plus")

    # Sample document content
    sampled = sample_document_content(store, doc_id)
    if not sampled.strip():
        raise HTTPException(status_code=400, detail="Document has no content")

    # Load prompt
    prompt_path = Path("config/prompts/reader_overview.txt")
    if prompt_path.exists():
        prompt_template = prompt_path.read_text(encoding="utf-8")
    else:
        prompt_template = "为文档《{document_title}》生成概览JSON：{{\"summary\":\"...\",\"key_topics\":[...],\"outline\":[...]}}\n\n{sampled_content}"

    prompt = prompt_template.replace("{document_title}", doc["title"])
    prompt = prompt.replace("{sampled_content}", sampled)

    llm = LLMClient()
    try:
        result = await asyncio.to_thread(
            llm.chat_json,
            model_name,
            [{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=4096,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Overview generation failed: {e}")

    summary = result.get("summary", "")
    key_topics = result.get("key_topics", [])
    outline = result.get("outline", [])

    overview = store.save_overview(doc_id, summary, key_topics, outline)

    # Parse for response
    outline_items = [OutlineItem(**item) if isinstance(item, dict) else item for item in outline]

    return DocumentOverviewResponse(
        id=overview["id"],
        document_id=doc_id,
        summary=summary,
        key_topics=key_topics,
        outline=outline_items,
        created_at=overview.get("created_at", ""),
        updated_at=overview.get("updated_at", ""),
    )


# --- Notes ---


@router.post("/{doc_id}/notes", response_model=NoteResponse)
async def create_note(doc_id: int, body: CreateNoteRequest):
    """Create a new note."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    note = store.create_note(
        doc_id, body.content, body.page_num, body.source, body.source_message_id,
    )
    return NoteResponse(**note)


@router.get("/{doc_id}/notes", response_model=NoteListResponse)
async def list_notes(doc_id: int, page_num: int | None = None):
    """List notes for a document, optionally filtered by page."""
    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    notes = store.list_notes(doc_id, page_num)
    return NoteListResponse(notes=[NoteResponse(**n) for n in notes])


@router.get("/{doc_id}/notes/{note_id}", response_model=NoteResponse)
async def get_note(doc_id: int, note_id: int):
    """Get a specific note."""
    store = _get_store()
    note = store.get_note(note_id)
    if not note or note["document_id"] != doc_id:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteResponse(**note)


@router.put("/{doc_id}/notes/{note_id}", response_model=NoteResponse)
async def update_note(doc_id: int, note_id: int, body: UpdateNoteRequest):
    """Update a note."""
    store = _get_store()
    note = store.get_note(note_id)
    if not note or note["document_id"] != doc_id:
        raise HTTPException(status_code=404, detail="Note not found")

    updated = store.update_note(note_id, body.content, body.page_num)
    return NoteResponse(**updated)


@router.delete("/{doc_id}/notes/{note_id}", response_model=DeleteResponse)
async def delete_note(doc_id: int, note_id: int):
    """Delete a note."""
    store = _get_store()
    note = store.get_note(note_id)
    if not note or note["document_id"] != doc_id:
        raise HTTPException(status_code=404, detail="Note not found")

    store.delete_note(note_id)
    return DeleteResponse(success=True, message="Note deleted")


# --- Study Tools ---


@router.post("/{doc_id}/generate/study-guide", response_model=StudyGuideResponse)
async def generate_study_guide(doc_id: int, save_as_note: bool = False):
    """Generate a study guide from the document."""
    from src.core.llm_client import LLMClient

    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    config = _load_config()
    agent_models = config.get("agent_models", {})
    model_name = agent_models.get("reader", "glm-4-plus")

    sampled = sample_document_content(store, doc_id)
    if not sampled.strip():
        raise HTTPException(status_code=400, detail="Document has no content")

    prompt_path = Path("config/prompts/reader_study_guide.txt")
    if prompt_path.exists():
        prompt = prompt_path.read_text(encoding="utf-8")
    else:
        prompt = "基于以下文档内容生成学习指南。返回JSON：{{\"sections\":[{{\"title\":\"...\",\"content\":\"...\"}}]}}\n\n{sampled_content}"

    prompt = prompt.replace("{document_title}", doc["title"])
    prompt = prompt.replace("{sampled_content}", sampled)

    llm = LLMClient()
    try:
        result = await asyncio.to_thread(
            llm.chat_json, model_name,
            [{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=4096,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Study guide generation failed: {e}")

    sections = result.get("sections", [])
    saved_note_id = None

    if save_as_note and sections:
        # Format as markdown note
        lines = [f"# 学习指南 — {doc['title']}\n"]
        for s in sections:
            lines.append(f"## {s.get('title', '')}\n{s.get('content', '')}\n")
        note = store.create_note(doc_id, "\n".join(lines), source="study_guide")
        saved_note_id = note["id"]

    return StudyGuideResponse(sections=sections, saved_note_id=saved_note_id)


@router.post("/{doc_id}/generate/faq", response_model=FaqResponse)
async def generate_faq(doc_id: int, save_as_note: bool = False):
    """Generate FAQ from the document."""
    from src.core.llm_client import LLMClient

    store = _get_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    config = _load_config()
    agent_models = config.get("agent_models", {})
    model_name = agent_models.get("reader", "glm-4-plus")

    sampled = sample_document_content(store, doc_id)
    if not sampled.strip():
        raise HTTPException(status_code=400, detail="Document has no content")

    prompt_path = Path("config/prompts/reader_faq.txt")
    if prompt_path.exists():
        prompt = prompt_path.read_text(encoding="utf-8")
    else:
        prompt = "基于以下文档内容生成FAQ。返回JSON：{{\"questions\":[{{\"question\":\"...\",\"answer\":\"...\"}}]}}\n\n{sampled_content}"

    prompt = prompt.replace("{document_title}", doc["title"])
    prompt = prompt.replace("{sampled_content}", sampled)

    llm = LLMClient()
    try:
        result = await asyncio.to_thread(
            llm.chat_json, model_name,
            [{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=4096,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"FAQ generation failed: {e}")

    questions = result.get("questions", [])
    saved_note_id = None

    if save_as_note and questions:
        lines = [f"# FAQ — {doc['title']}\n"]
        for q in questions:
            lines.append(f"**Q: {q.get('question', '')}**\n\nA: {q.get('answer', '')}\n")
        note = store.create_note(doc_id, "\n".join(lines), source="faq")
        saved_note_id = note["id"]

    return FaqResponse(questions=questions, saved_note_id=saved_note_id)


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
