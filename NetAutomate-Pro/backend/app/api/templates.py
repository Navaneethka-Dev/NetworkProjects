"""Templates API — /api/templates/*"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.rbac import require_admin, require_operator, require_viewer
from app.schemas.template import (
    TemplateCreate, TemplatePreviewRequest, TemplatePreviewResponse,
    TemplateResponse, TemplateSummary, TemplateUpdate,
)
from app.services.template_service import (
    create_template, delete_template, get_template_or_404,
    list_templates, preview_template, update_template,
)

router = APIRouter(prefix="/api/templates", tags=["Templates"])


@router.get("", response_model=list[TemplateSummary])
async def get_templates(
    vendor: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    return await list_templates(db, vendor=vendor)


@router.post("", response_model=TemplateResponse, status_code=201)
async def add_template(
    data: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_operator),
):
    return await create_template(db, data, current_user.id)


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    return await get_template_or_404(db, template_id)


@router.put("/{template_id}", response_model=TemplateResponse)
async def edit_template(
    template_id: uuid.UUID,
    data: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_operator),
):
    return await update_template(db, template_id, data)


@router.delete("/{template_id}", status_code=204)
async def remove_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    await delete_template(db, template_id)


@router.post("/{template_id}/preview", response_model=TemplatePreviewResponse)
async def preview(
    template_id: uuid.UUID,
    data: TemplatePreviewRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_operator),
):
    return await preview_template(db, template_id, data.variables, data.device_hostname)
