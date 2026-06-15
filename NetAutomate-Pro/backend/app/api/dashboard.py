"""Dashboard API — /api/dashboard/*"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.rbac import require_viewer
from app.models.backup import Backup
from app.models.deployment import Deployment, DeploymentStatusEnum
from app.models.device import Device, DeviceStatusEnum

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db), _=Depends(require_viewer)):
    total_devices = (await db.execute(select(func.count(Device.id)))).scalar() or 0
    online_devices = (await db.execute(
        select(func.count(Device.id)).where(Device.status == DeviceStatusEnum.online)
    )).scalar() or 0
    total_deployments = (await db.execute(select(func.count(Deployment.id)))).scalar() or 0
    successful_deployments = (await db.execute(
        select(func.count(Deployment.id)).where(Deployment.status == DeploymentStatusEnum.completed)
    )).scalar() or 0
    total_backups = (await db.execute(select(func.count(Backup.id)))).scalar() or 0

    return {
        "total_devices": total_devices,
        "online_devices": online_devices,
        "offline_devices": total_devices - online_devices,
        "total_deployments": total_deployments,
        "successful_deployments": successful_deployments,
        "failed_deployments": total_deployments - successful_deployments,
        "total_backups": total_backups,
        "deployment_success_rate": round(
            successful_deployments / total_deployments * 100, 1
        ) if total_deployments > 0 else 0.0,
    }


@router.get("/device-health")
async def device_health(db: AsyncSession = Depends(get_db), _=Depends(require_viewer)):
    result = await db.execute(
        select(Device.status, func.count(Device.id)).group_by(Device.status)
    )
    counts = {row[0].value: row[1] for row in result.all()}
    return {
        "online": counts.get("online", 0),
        "offline": counts.get("offline", 0),
        "unreachable": counts.get("unreachable", 0),
        "maintenance": counts.get("maintenance", 0),
        "unknown": counts.get("unknown", 0),
    }


@router.get("/recent-deployments")
async def recent_deployments(db: AsyncSession = Depends(get_db), _=Depends(require_viewer)):
    result = await db.execute(
        select(Deployment).order_by(Deployment.created_at.desc()).limit(10)
    )
    deps = result.scalars().all()
    return [
        {
            "id": str(d.id),
            "status": d.status.value,
            "deployment_type": d.deployment_type.value,
            "device_count": len(d.target_devices),
            "created_at": d.created_at.isoformat(),
        }
        for d in deps
    ]


@router.get("/activity")
async def recent_activity(db: AsyncSession = Depends(get_db), _=Depends(require_viewer)):
    from app.models.audit_log import AuditLog
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.created_at.desc()).limit(20)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "action": l.action,
            "resource_type": l.resource_type,
            "resource_id": str(l.resource_id) if l.resource_id else None,
            "user_id": str(l.user_id) if l.user_id else None,
            "ip_address": l.ip_address,
            "created_at": l.created_at.isoformat(),
        }
        for l in logs
    ]
