"""Deployments API — /api/deployments/*"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.rbac import require_admin, require_operator, require_viewer
from app.schemas.deployment import DeploymentCreate, DeploymentResponse, DeploymentSummary
from app.services.deployment_service import (
    create_deployment, get_deployment_or_404, list_deployments, rollback_deployment,
)

router = APIRouter(prefix="/api/deployments", tags=["Deployments"])


@router.get("", response_model=list[DeploymentSummary])
async def get_deployments(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    deps = await list_deployments(db, skip=skip, limit=limit)
    result = []
    for d in deps:
        result.append(DeploymentSummary(
            id=d.id,
            template_id=d.template_id,
            template_name=d.template.name if d.template else None,
            deployment_type=d.deployment_type,
            status=d.status,
            device_count=len(d.target_devices),
            deployed_by=d.deployed_by,
            created_at=d.created_at,
        ))
    return result


@router.post("", response_model=DeploymentResponse, status_code=201)
async def add_deployment(
    data: DeploymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_operator),
):
    return await create_deployment(db, data, current_user.id)


@router.get("/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(
    deployment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    return await get_deployment_or_404(db, deployment_id)


@router.post("/{deployment_id}/rollback", response_model=DeploymentResponse)
async def rollback(
    deployment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    return await rollback_deployment(db, deployment_id)
