"""Backups API — /api/backups/*"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.rbac import require_admin, require_operator, require_viewer
from app.models.backup import BackupTypeEnum
from app.models.device import Device
from app.schemas.backup import (
    BackupCreate, BackupDetailResponse, BackupDiffResponse,
    BackupResponse, BackupRestoreRequest,
)
from app.services.backup_service import (
    create_backup, diff_backups, get_backup_or_404, list_backups, restore_backup,
)

router = APIRouter(prefix="/api/backups", tags=["Backups"])


async def _hostname_map(db: AsyncSession, device_ids: list[uuid.UUID]) -> dict[uuid.UUID, str]:
    """Return {device_id: hostname} for a list of device IDs."""
    if not device_ids:
        return {}
    result = await db.execute(select(Device).where(Device.id.in_(device_ids)))
    return {d.id: d.hostname for d in result.scalars().all()}


@router.get("", response_model=list[BackupResponse])
async def get_backups(
    device_id: uuid.UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    backups = await list_backups(db, device_id=device_id, skip=skip, limit=limit)
    hostnames = await _hostname_map(db, [b.device_id for b in backups])
    result = []
    for b in backups:
        result.append(BackupResponse(
            id=b.id,
            device_id=b.device_id,
            device_hostname=hostnames.get(b.device_id),
            backup_type=b.backup_type,
            version_tag=b.version_tag,
            checksum=b.checksum,
            config_size=len(b.config_content),
            created_by=b.created_by,
            created_at=b.created_at,
        ))
    return result


@router.post("", response_model=BackupResponse, status_code=201)
async def add_backup(
    data: BackupCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_operator),
):
    b = await create_backup(db, data.device_id, data.backup_type, current_user.id)
    hostnames = await _hostname_map(db, [b.device_id])
    return BackupResponse(
        id=b.id, device_id=b.device_id, device_hostname=hostnames.get(b.device_id),
        backup_type=b.backup_type, version_tag=b.version_tag, checksum=b.checksum,
        config_size=len(b.config_content), created_by=b.created_by, created_at=b.created_at,
    )


# NOTE: /diff must be registered BEFORE /{backup_id} to avoid path conflict
@router.get("/diff", response_model=BackupDiffResponse)
async def diff_query(
    backup_a_id: uuid.UUID = Query(...),
    backup_b_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    """Diff two backups using query parameters (used by frontend)."""
    return await diff_backups(db, backup_a_id, backup_b_id)


@router.post("/trigger/{device_id}", response_model=BackupResponse, status_code=201)
async def trigger_backup(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_operator),
):
    """Trigger an immediate manual backup for a specific device."""
    b = await create_backup(db, device_id, BackupTypeEnum.manual, current_user.id)
    hostnames = await _hostname_map(db, [b.device_id])
    return BackupResponse(
        id=b.id, device_id=b.device_id, device_hostname=hostnames.get(b.device_id),
        backup_type=b.backup_type, version_tag=b.version_tag, checksum=b.checksum,
        config_size=len(b.config_content), created_by=b.created_by, created_at=b.created_at,
    )


@router.get("/{backup_id}", response_model=BackupDetailResponse)
async def get_backup(
    backup_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    b = await get_backup_or_404(db, backup_id)
    hostnames = await _hostname_map(db, [b.device_id])
    return BackupDetailResponse(
        id=b.id, device_id=b.device_id, device_hostname=hostnames.get(b.device_id),
        backup_type=b.backup_type, version_tag=b.version_tag, checksum=b.checksum,
        config_size=len(b.config_content), created_by=b.created_by,
        created_at=b.created_at, config_content=b.config_content,
    )


@router.post("/{backup_id}/restore")
async def restore(
    backup_id: uuid.UUID,
    data: BackupRestoreRequest,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    return await restore_backup(db, backup_id, data.dry_run)
