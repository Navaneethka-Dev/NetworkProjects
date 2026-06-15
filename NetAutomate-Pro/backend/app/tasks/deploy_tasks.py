"""Celery tasks — deployment execution (per device, parallel)."""
import time
import uuid
from datetime import datetime, timezone

from app.tasks.celery_app import celery_app


@celery_app.task(bind=True, name="app.tasks.deploy_tasks.execute_deployment", max_retries=2)
def execute_deployment(self, deployment_id: str):
    """Execute a deployment against all target devices."""
    import asyncio
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.database import AsyncSessionLocal
    from app.models.deployment import Deployment, DeploymentLog, DeploymentStatusEnum, DeploymentLogStatusEnum
    from app.models.device import Device
    from app.network.connector import DeviceConnector

    async def _run():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload

            result = await db.execute(
                select(Deployment).options(selectinload(Deployment.template))
                .where(Deployment.id == deployment_id)
            )
            deployment = result.scalar_one_or_none()
            if not deployment:
                return

            deployment.status = DeploymentStatusEnum.running
            deployment.started_at = datetime.now(timezone.utc)
            await db.commit()

            all_success = True
            for device_id_str in deployment.target_devices:
                dev_result = await db.execute(
                    select(Device).where(Device.id == device_id_str)
                )
                device = dev_result.scalar_one_or_none()
                if not device:
                    continue

                start = time.perf_counter()
                try:
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
                    config_lines = [
                        l.strip() for l in (deployment.rendered_config or "").splitlines()
                        if l.strip() and not l.startswith("!")
                    ]
                    output = conn.send_config(config_lines[:100])
                    duration = time.perf_counter() - start

                    log = DeploymentLog(
                        deployment_id=deployment.id,
                        device_id=device.id,
                        device_hostname=device.hostname,
                        status=DeploymentLogStatusEnum.success,
                        output=output,
                        duration_seconds=round(duration, 3),
                    )
                except Exception as exc:
                    all_success = False
                    log = DeploymentLog(
                        deployment_id=deployment.id,
                        device_id=device.id,
                        device_hostname=device.hostname,
                        status=DeploymentLogStatusEnum.failed,
                        error_message=str(exc),
                        duration_seconds=round(time.perf_counter() - start, 3),
                    )

                db.add(log)

            deployment.status = (
                DeploymentStatusEnum.completed if all_success else DeploymentStatusEnum.failed
            )
            deployment.completed_at = datetime.now(timezone.utc)
            await db.commit()

    asyncio.run(_run())
    return {"deployment_id": deployment_id, "status": "done"}
