"""Deployment service — create, run (sync fallback if no Celery/Redis), rollback."""
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.deployment import Deployment, DeploymentStatusEnum, DeploymentTypeEnum
from app.models.device import Device
from app.schemas.deployment import DeploymentCreate
from app.services.template_service import _render, get_template_or_404


async def list_deployments(db: AsyncSession, skip: int = 0, limit: int = 50) -> list[Deployment]:
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.logs), selectinload(Deployment.template))
        .order_by(Deployment.created_at.desc())
        .offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_deployment_or_404(db: AsyncSession, deployment_id: str) -> Deployment:
    result = await db.execute(
        select(Deployment)
        .options(selectinload(Deployment.logs), selectinload(Deployment.template))
        .where(Deployment.id == str(deployment_id))
    )
    dep = result.scalar_one_or_none()
    if not dep:
        raise HTTPException(status_code=404, detail=f"Deployment {deployment_id} not found")
    return dep


async def create_deployment(
    db: AsyncSession, data: DeploymentCreate, deployed_by: str
) -> Deployment:
    # Validate template exists
    tmpl = await get_template_or_404(db, data.template_id)

    # Validate devices exist
    for did in data.device_ids:
        result = await db.execute(select(Device).where(Device.id == str(did)))
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail=f"Device {did} not found")

    # Build a context for rendering
    ctx = {"device": {"hostname": "bulk"}, **data.variables}
    rendered = _render(tmpl.template_content, ctx)

    deployment = Deployment(
        template_id=str(data.template_id),
        deployment_type=data.deployment_type if len(data.device_ids) > 1 else DeploymentTypeEnum.single,
        rendered_config=rendered,
        variables_used=data.variables,
        status=DeploymentStatusEnum.pending,
        deployed_by=str(deployed_by),
    )
    deployment.target_devices = [str(d) for d in data.device_ids]
    db.add(deployment)
    await db.flush()

    if not data.dry_run:
        # Try to enqueue via Celery; fall back to direct async execution if Celery/Redis unavailable
        try:
            from app.tasks.deploy_tasks import execute_deployment  # type: ignore
            task = execute_deployment.delay(str(deployment.id))
            deployment.celery_task_id = task.id
            await db.flush()
        except Exception:
            # No Redis — run the deployment synchronously in-process
            await _run_deployment_sync(db, deployment, tmpl, data)

    return deployment


async def _run_deployment_sync(db: AsyncSession, deployment: Deployment, tmpl, data: DeploymentCreate) -> None:
    """Synchronous deployment fallback when Celery/Redis is not available (local dev)."""
    import time
    from app.models.deployment import DeploymentLog, DeploymentLogStatusEnum
    from app.network.connector import DeviceConnector

    deployment.status = DeploymentStatusEnum.running
    deployment.started_at = datetime.now(timezone.utc)
    await db.flush()

    all_success = True
    for did in data.device_ids:
        result = await db.execute(select(Device).where(Device.id == str(did)))
        device = result.scalar_one_or_none()
        if not device:
            continue
        start = time.perf_counter()
        try:
            conn = DeviceConnector({
                "hostname": device.hostname, "ip_address": device.ip_address,
                "device_type": device.device_type, "vendor": device.vendor,
                "ssh_port": device.ssh_port, "username": device.username,
                "password": device.password, "secret": device.secret,
            })
            ctx = {"device": {"hostname": device.hostname, "ip_address": device.ip_address}, **data.variables}
            rendered = _render(tmpl.template_content, ctx)
            lines = [ln.strip() for ln in rendered.splitlines() if ln.strip() and not ln.startswith("!")]
            output = conn.send_config(lines)
            duration = time.perf_counter() - start
            log = DeploymentLog(
                deployment_id=deployment.id, device_id=device.id,
                device_hostname=device.hostname,
                status=DeploymentLogStatusEnum.success, output=output,
                duration_seconds=round(duration, 3),
            )
        except Exception as exc:
            all_success = False
            log = DeploymentLog(
                deployment_id=deployment.id, device_id=device.id,
                device_hostname=device.hostname,
                status=DeploymentLogStatusEnum.failed, error_message=str(exc),
                duration_seconds=round(time.perf_counter() - start, 3),
            )
        db.add(log)

    deployment.status = DeploymentStatusEnum.completed if all_success else DeploymentStatusEnum.failed
    deployment.completed_at = datetime.now(timezone.utc)
    await db.flush()


async def rollback_deployment(db: AsyncSession, deployment_id: str) -> Deployment:
    dep = await get_deployment_or_404(db, deployment_id)
    if dep.status not in (DeploymentStatusEnum.completed, DeploymentStatusEnum.failed):
        raise HTTPException(status_code=400, detail="Can only rollback completed or failed deployments")
    dep.status = DeploymentStatusEnum.rolled_back
    await db.flush()
    return dep
