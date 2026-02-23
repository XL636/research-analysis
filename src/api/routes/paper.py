"""Paper writing API routes."""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.api.schemas import (
    CitationRefResponse,
    CreatePaperRequest,
    DeleteResponse,
    OutlineReviseRequest,
    PaperExportRequest,
    PaperOutlineResponse,
    PaperProjectResponse,
    PaperProjectSummary,
    PaperSectionResponse,
    PolishRequest,
    SectionReviseRequest,
    SectionWriteRequest,
)

router = APIRouter()


def _get_pipeline():
    """Lazy import WriterPipeline."""
    from src.core.writer_engine import WriterPipeline

    return WriterPipeline()


def _project_to_response(project) -> PaperProjectResponse:
    """Convert PaperProject to API response."""
    outline_resp = None
    if project.outline:
        outline_resp = PaperOutlineResponse(
            abstract_draft=project.outline.abstract_draft,
            sections=[
                PaperSectionResponse(
                    id=s.id, title=s.title, level=s.level,
                    outline_points=s.outline_points, content=s.content,
                    word_count=s.word_count, status=s.status.value,
                    citations=s.citations,
                )
                for s in project.outline.sections
            ],
            estimated_word_count=project.outline.estimated_word_count,
        )

    draft_sections = []
    draft_title = ""
    draft_abstract = ""
    draft_word_count = 0
    if project.draft:
        draft_title = project.draft.title
        draft_abstract = project.draft.abstract
        draft_word_count = project.draft.total_word_count
        draft_sections = [
            PaperSectionResponse(
                id=s.id, title=s.title, level=s.level,
                outline_points=s.outline_points, content=s.content,
                word_count=s.word_count, status=s.status.value,
                citations=s.citations,
            )
            for s in project.draft.sections
        ]

    citations = [
        CitationRefResponse(
            key=c.key, title=c.title, authors=c.authors,
            year=c.year, venue=c.venue, source=c.source,
        )
        for c in project.citations
    ]

    return PaperProjectResponse(
        id=project.id,
        name=project.name,
        status=project.status.value,
        language=project.language.value,
        venue=project.venue.value,
        topic=project.topic,
        research_question=project.research_question,
        key_contributions=project.key_contributions,
        target_word_count=project.target_word_count,
        outline=outline_resp,
        draft_title=draft_title,
        draft_abstract=draft_abstract,
        draft_sections=draft_sections,
        draft_total_word_count=draft_word_count,
        citations=citations,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@router.post("/projects", response_model=PaperProjectResponse)
async def create_project(body: CreatePaperRequest):
    """创建论文项目并生成大纲."""
    from src.core.paper_models import PaperLanguage, PaperVenue

    wp = _get_pipeline()

    project = await asyncio.to_thread(
        wp.create_project,
        name=body.name,
        topic=body.topic,
        language=PaperLanguage(body.language),
        venue=PaperVenue(body.venue),
        research_question=body.research_question,
        key_contributions=body.key_contributions,
        target_word_count=body.target_word_count,
        reference_doc_ids=body.reference_doc_ids,
        additional_context=body.additional_context,
    )

    # 自动生成大纲
    project = await asyncio.to_thread(wp.generate_outline, project)

    return _project_to_response(project)


@router.get("/projects", response_model=list[PaperProjectSummary])
async def list_projects(
    limit: int = Query(20, ge=1, le=200),
):
    """列出论文项目."""
    from src.store.paper_store import PaperStore

    store = PaperStore()
    projects = store.list_projects(limit=limit)
    return [PaperProjectSummary(**p) for p in projects]


@router.get("/projects/{project_id}", response_model=PaperProjectResponse)
async def get_project(project_id: str):
    """获取论文项目详情."""
    from src.store.paper_store import PaperStore

    store = PaperStore()
    project = store.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _project_to_response(project)


@router.delete("/projects/{project_id}", response_model=DeleteResponse)
async def delete_project(project_id: str):
    """删除论文项目."""
    from src.store.paper_store import PaperStore

    store = PaperStore()
    if not store.delete(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
    return DeleteResponse(success=True, message="Project deleted")


@router.post("/projects/{project_id}/outline/revise", response_model=PaperProjectResponse)
async def revise_outline(project_id: str, body: OutlineReviseRequest):
    """修改论文大纲."""
    wp = _get_pipeline()
    project = wp.store.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project = await asyncio.to_thread(wp.revise_outline, project, body.feedback)
    return _project_to_response(project)


@router.post("/projects/{project_id}/outline/confirm", response_model=PaperProjectResponse)
async def confirm_outline(project_id: str):
    """确认论文大纲."""
    wp = _get_pipeline()
    project = wp.store.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        project = wp.confirm_outline(project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _project_to_response(project)


@router.post("/projects/{project_id}/write", response_model=PaperProjectResponse)
async def write_sections(project_id: str, body: SectionWriteRequest | None = None):
    """写作论文章节."""
    wp = _get_pipeline()
    project = wp.store.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        if body and body.section_id:
            project = await asyncio.to_thread(wp.write_section, project, body.section_id)
        else:
            project = await asyncio.to_thread(wp.write_all_sections, project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _project_to_response(project)


@router.get("/projects/{project_id}/sections/{section_id}", response_model=PaperSectionResponse)
async def get_section(project_id: str, section_id: str):
    """获取章节详情."""
    from src.store.paper_store import PaperStore

    store = PaperStore()
    project = store.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if not project.draft:
        raise HTTPException(status_code=400, detail="No draft available")

    for s in project.draft.sections:
        if s.id == section_id:
            return PaperSectionResponse(
                id=s.id, title=s.title, level=s.level,
                outline_points=s.outline_points, content=s.content,
                word_count=s.word_count, status=s.status.value,
                citations=s.citations,
            )
    raise HTTPException(status_code=404, detail="Section not found")


@router.post("/projects/{project_id}/sections/{section_id}/revise", response_model=PaperProjectResponse)
async def revise_section(project_id: str, section_id: str, body: SectionReviseRequest):
    """修改章节."""
    wp = _get_pipeline()
    project = wp.store.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        project = await asyncio.to_thread(wp.revise_section, project, section_id, body.feedback)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _project_to_response(project)


@router.post("/projects/{project_id}/polish", response_model=PaperProjectResponse)
async def polish_paper(project_id: str, body: PolishRequest | None = None):
    """全文润色."""
    wp = _get_pipeline()
    project = wp.store.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    instructions = body.instructions if body else ""
    try:
        project = await asyncio.to_thread(wp.polish, project, instructions)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return _project_to_response(project)


@router.get("/projects/{project_id}/export")
async def export_paper(
    project_id: str,
    format: str = Query("markdown", description="输出格式: markdown/docx/pdf/latex"),
):
    """导出论文."""
    wp = _get_pipeline()
    project = wp.store.load(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        output_path = await asyncio.to_thread(wp.export, project, format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"success": True, "output_path": output_path, "format": format}
