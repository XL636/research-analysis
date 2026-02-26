"""Templates API routes - CRUD for report templates."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.api.schemas import (
    CreateTemplateRequest,
    TemplateListResponse,
    TemplateResponse,
    TemplateSectionSchema,
    UpdateTemplateRequest,
)
from src.core.models import TemplateSection
from src.store.template_store import TemplateStore

router = APIRouter()


def _template_to_response(t) -> TemplateResponse:
    return TemplateResponse(
        id=t.id,
        name=t.name,
        display_name=t.display_name,
        description=t.description,
        prompt_content=t.prompt_content,
        sections=[
            TemplateSectionSchema(title=s.title, description=s.description, required=s.required)
            for s in t.sections
        ],
        is_builtin=t.is_builtin,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.get("/", response_model=TemplateListResponse)
async def list_templates():
    """List all report templates."""
    store = TemplateStore()
    templates = store.list_templates()
    return TemplateListResponse(
        templates=[_template_to_response(t) for t in templates]
    )


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: int):
    """Get a template by ID."""
    store = TemplateStore()
    template = store.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return _template_to_response(template)


@router.post("/", response_model=TemplateResponse, status_code=201)
async def create_template(req: CreateTemplateRequest):
    """Create a custom template."""
    store = TemplateStore()

    # Check name uniqueness
    existing = store.get_template_by_name(req.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Template name '{req.name}' already exists")

    sections = [TemplateSection(title=s.title, description=s.description, required=s.required) for s in req.sections]

    template = store.create_template(
        name=req.name,
        display_name=req.display_name,
        description=req.description,
        prompt_content=req.prompt_content,
        sections=sections,
    )
    return _template_to_response(template)


@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: int, req: UpdateTemplateRequest):
    """Update a template."""
    store = TemplateStore()
    sections = None
    if req.sections is not None:
        sections = [TemplateSection(title=s.title, description=s.description, required=s.required) for s in req.sections]

    try:
        template = store.update_template(
            template_id,
            display_name=req.display_name,
            description=req.description,
            prompt_content=req.prompt_content,
            sections=sections,
        )
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return _template_to_response(template)


@router.delete("/{template_id}")
async def delete_template(template_id: int):
    """Delete a custom template (builtin cannot be deleted)."""
    store = TemplateStore()
    try:
        success = store.delete_template(template_id)
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))

    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"success": True, "message": "Template deleted"}
