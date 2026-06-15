"""Celery tasks — automated backups and device health checks."""
from app.tasks.celery_app import celery_app


@celery_app.task(name="app.tasks.backup_tasks.create_device_backup")
def create_device_backup(device_id: str, created_by: str | None = None):
    """Create a backup for a single device."""
    import asyncio
    from app.database import AsyncSessionLocal
    from app.models.backup import BackupTypeEnum
    from app.services.backup_service import create_backup
    import uuid

    async def _run():
        async with AsyncSessionLocal() as db:
            try:
                bak = await create_backup(
                    db,
                    uuid.UUID(device_id),
                    BackupTypeEnum.scheduled,
                    uuid.UUID(created_by) if created_by else None,
                )
                return {"backup_id": str(bak.id), "version_tag": bak.version_tag}
            except Exception as exc:
                return {"error": str(exc)}

    return asyncio.run(_run())


@celery_app.task(name="app.tasks.backup_tasks.scheduled_backup_all")
def scheduled_backup_all():
    """Triggered by Celery Beat — backs up every active device."""
    import asyncio
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.device import Device

    async def _get_device_ids():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Device.id))
            return [str(row[0]) for row in result.all()]

    device_ids = asyncio.run(_get_device_ids())
    results = []
    for did in device_ids:
        task = create_device_backup.delay(did)
        results.append({"device_id": did, "task_id": task.id})
    return {"queued": len(results), "tasks": results}


@celery_app.task(name="app.tasks.backup_tasks.check_all_device_health")
def check_all_device_health():
    """Triggered by Beat every 15 minutes — pings all devices and updates status."""
    import asyncio
    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.database import AsyncSessionLocal
    from app.models.device import Device, DeviceStatusEnum
    from app.network.connector import DeviceConnector

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Device))
            devices = result.scalars().all()
            updated = 0
            for device in devices:
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
                reachable, _ = conn.ping()
                device.status = DeviceStatusEnum.online if reachable else DeviceStatusEnum.unreachable
                device.last_checked = datetime.now(timezone.utc)
                updated += 1
            await db.commit()
            return {"devices_checked": updated}

    return asyncio.run(_run())
