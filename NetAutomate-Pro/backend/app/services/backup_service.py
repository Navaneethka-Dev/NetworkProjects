"""Backup service — create, diff, restore. Uses str IDs (SQLite/PostgreSQL portable)."""
import hashlib
from datetime import datetime, timezone
from difflib import unified_diff

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backup import Backup, BackupTypeEnum
from app.models.device import Device
from app.network.connector import DeviceConnector


def _sha256(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def _version_tag() -> str:
    return f"v{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"


async def list_backups(
    db: AsyncSession, device_id: str | None = None, skip: int = 0, limit: int = 100
) -> list[Backup]:
    q = select(Backup).order_by(Backup.created_at.desc()).offset(skip).limit(limit)
    if device_id:
        q = q.where(Backup.device_id == str(device_id))
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_backup_or_404(db: AsyncSession, backup_id: str) -> Backup:
    result = await db.execute(select(Backup).where(Backup.id == str(backup_id)))
    bak = result.scalar_one_or_none()
    if not bak:
        raise HTTPException(status_code=404, detail=f"Backup {backup_id} not found")
    return bak


async def create_backup(
    db: AsyncSession,
    device_id: str,
    backup_type: BackupTypeEnum = BackupTypeEnum.manual,
    created_by: str | None = None,
) -> Backup:
    result = await db.execute(select(Device).where(Device.id == str(device_id)))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail=f"Device {device_id} not found")

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
    config = conn.get_running_config()

    backup = Backup(
        device_id=str(device_id),
        config_content=config,
        backup_type=backup_type,
        version_tag=_version_tag(),
        checksum=_sha256(config),
        created_by=str(created_by) if created_by else None,
    )
    db.add(backup)
    await db.flush()
    return backup


async def diff_backups(db: AsyncSession, backup_a_id: str, backup_b_id: str) -> dict:
    a = await get_backup_or_404(db, backup_a_id)
    b = await get_backup_or_404(db, backup_b_id)
    lines_a = a.config_content.splitlines(keepends=True)
    lines_b = b.config_content.splitlines(keepends=True)
    diff_lines = list(unified_diff(lines_a, lines_b, fromfile=a.version_tag, tofile=b.version_tag))
    added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
    removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
    return {
        "backup_a_id": str(a.id),
        "backup_b_id": str(b.id),
        "backup_a_tag": a.version_tag,
        "backup_b_tag": b.version_tag,
        "unified_diff": "".join(diff_lines),
        "lines_added": added,
        "lines_removed": removed,
        "lines_unchanged": len(lines_a) - removed,
    }


async def restore_backup(db: AsyncSession, backup_id: str, dry_run: bool = True) -> dict:
    bak = await get_backup_or_404(db, backup_id)
    result = await db.execute(select(Device).where(Device.id == bak.device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if dry_run:
        return {"status": "dry_run", "config_preview": bak.config_content[:500] + "..."}

    conn = DeviceConnector({
        "hostname": device.hostname, "ip_address": device.ip_address,
        "device_type": device.device_type, "vendor": device.vendor,
        "ssh_port": device.ssh_port, "username": device.username,
        "password": device.password, "secret": device.secret,
    })
    lines = [l.strip() for l in bak.config_content.splitlines() if l.strip() and not l.startswith("!")]
    output = conn.send_config(lines[:50])
    return {"status": "restored", "output": output}
