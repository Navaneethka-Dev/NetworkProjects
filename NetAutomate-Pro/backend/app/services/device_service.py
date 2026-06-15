"""Device service — CRUD, ping, status update."""
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.device import Device, DeviceGroup, DeviceStatusEnum
from app.network.connector import DeviceConnector
from app.schemas.device import DeviceCreate, DeviceUpdate


async def list_devices(
    db: AsyncSession,
    status: DeviceStatusEnum | None = None,
    vendor: str | None = None,
    group_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Device]:
    q = select(Device).options(selectinload(Device.group))
    if status:
        q = q.where(Device.status == status)
    if vendor:
        q = q.where(Device.vendor == vendor)
    if group_id:
        q = q.where(Device.group_id == group_id)
    q = q.offset(skip).limit(limit).order_by(Device.hostname)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_device_or_404(db: AsyncSession, device_id: uuid.UUID) -> Device:
    result = await db.execute(
        select(Device).options(selectinload(Device.group)).where(Device.id == device_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")
    return device


async def create_device(db: AsyncSession, data: DeviceCreate, created_by: uuid.UUID) -> Device:
    if data.group_id:
        grp = await db.execute(select(DeviceGroup).where(DeviceGroup.id == data.group_id))
        if not grp.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Device group not found")

    device = Device(
        hostname=data.hostname,
        ip_address=data.ip_address,
        device_type=data.device_type,
        vendor=data.vendor,
        model=data.model,
        ssh_port=data.ssh_port,
        username=data.username,
        password=data.password,
        secret=data.secret,
        group_id=data.group_id,
        created_by=created_by,
        status=DeviceStatusEnum.unknown,
    )
    db.add(device)
    await db.flush()
    return device


async def update_device(db: AsyncSession, device_id: uuid.UUID, data: DeviceUpdate) -> Device:
    device = await get_device_or_404(db, device_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    await db.flush()
    return device


async def delete_device(db: AsyncSession, device_id: uuid.UUID) -> None:
    device = await get_device_or_404(db, device_id)
    await db.delete(device)
    await db.flush()


async def ping_device(db: AsyncSession, device_id: uuid.UUID) -> dict:
    device = await get_device_or_404(db, device_id)
    conn = DeviceConnector({
        "hostname": device.hostname,
        "ip_address": device.ip_address,
        "device_type": device.device_type,
        "vendor": device.vendor,
        "ssh_port": device.ssh_port,
        "username": device.username,
        "password": device.password,
        "secret": device.secret,
    })
    reachable, latency = conn.ping()
    device.status = DeviceStatusEnum.online if reachable else DeviceStatusEnum.unreachable
    device.last_checked = datetime.now(timezone.utc)
    await db.flush()
    return {
        "device_id": device.id,
        "hostname": device.hostname,
        "reachable": reachable,
        "latency_ms": latency,
        "message": "Device is reachable" if reachable else "Device is unreachable",
    }


# ── DeviceGroup ────────────────────────────────────────────────────────────────

async def list_groups(db: AsyncSession) -> list[DeviceGroup]:
    result = await db.execute(select(DeviceGroup).order_by(DeviceGroup.name))
    return list(result.scalars().all())


async def create_group(db: AsyncSession, name: str, description: str | None, created_by: uuid.UUID) -> DeviceGroup:
    existing = await db.execute(select(DeviceGroup).where(DeviceGroup.name == name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Group name already exists")
    group = DeviceGroup(name=name, description=description, created_by=created_by)
    db.add(group)
    await db.flush()
    return group


async def delete_group(db: AsyncSession, group_id: uuid.UUID) -> None:
    result = await db.execute(select(DeviceGroup).where(DeviceGroup.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    await db.delete(group)
    await db.flush()
