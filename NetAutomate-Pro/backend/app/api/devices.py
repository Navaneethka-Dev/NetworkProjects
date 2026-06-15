"""Device API — /api/devices/* and /api/device-groups/*"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.rbac import require_admin, require_operator, require_viewer
from app.models.device import DeviceStatusEnum
from app.schemas.device import (
    DeviceCreate, DeviceGroupCreate, DeviceGroupResponse,
    DevicePingResponse, DeviceResponse, DeviceUpdate,
)
from app.services.device_service import (
    create_device, create_group, delete_device, delete_group,
    get_device_or_404, list_devices, list_groups, ping_device, update_device,
)

router = APIRouter(tags=["Devices"])


# ── Device Groups (also aliased under /devices/groups for frontend compat) ─────

@router.get("/api/devices/groups", response_model=list[DeviceGroupResponse])
@router.get("/api/device-groups", response_model=list[DeviceGroupResponse])
async def get_groups(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    return await list_groups(db)


@router.post("/api/device-groups", response_model=DeviceGroupResponse, status_code=201)
async def add_group(
    data: DeviceGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_operator),
):
    return await create_group(db, data.name, data.description, current_user.id)


@router.delete("/api/device-groups/{group_id}", status_code=204)
async def remove_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    await delete_group(db, group_id)


# ── Devices ────────────────────────────────────────────────────────────────────

@router.get("/api/devices", response_model=list[DeviceResponse])
async def get_devices(
    status: DeviceStatusEnum | None = Query(None),
    vendor: str | None = Query(None),
    group_id: uuid.UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    return await list_devices(db, status=status, vendor=vendor, group_id=group_id, skip=skip, limit=limit)


@router.post("/api/devices", response_model=DeviceResponse, status_code=201)
async def add_device(
    data: DeviceCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_operator),
):
    return await create_device(db, data, current_user.id)


@router.get("/api/devices/{device_id}", response_model=DeviceResponse)
async def get_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    return await get_device_or_404(db, device_id)


@router.put("/api/devices/{device_id}", response_model=DeviceResponse)
async def edit_device(
    device_id: uuid.UUID,
    data: DeviceUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_operator),
):
    return await update_device(db, device_id, data)


@router.delete("/api/devices/{device_id}", status_code=204)
async def remove_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    await delete_device(db, device_id)


@router.post("/api/devices/{device_id}/ping", response_model=DevicePingResponse)
async def ping(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_operator),
):
    return await ping_device(db, device_id)
