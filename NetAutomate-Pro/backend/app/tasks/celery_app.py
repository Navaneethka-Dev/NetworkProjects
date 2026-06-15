"""Celery application configuration."""
from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "netautomate",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.deploy_tasks",
        "app.tasks.backup_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,  # 24 hours
)

# ── Beat schedule (periodic tasks) ────────────────────────────────────────────
celery_app.conf.beat_schedule = {
    "scheduled-backup-all-devices": {
        "task": "app.tasks.backup_tasks.scheduled_backup_all",
        "schedule": crontab(
            minute=0,
            hour=f"*/{settings.SCHEDULED_BACKUP_INTERVAL_HOURS}",
        ),
        "options": {"queue": "backups"},
    },
    "device-health-check": {
        "task": "app.tasks.backup_tasks.check_all_device_health",
        "schedule": crontab(minute="*/15"),   # Every 15 minutes
        "options": {"queue": "health"},
    },
}

celery_app.conf.task_routes = {
    "app.tasks.deploy_tasks.*": {"queue": "deployments"},
    "app.tasks.backup_tasks.scheduled_backup_all": {"queue": "backups"},
    "app.tasks.backup_tasks.create_device_backup": {"queue": "backups"},
    "app.tasks.backup_tasks.check_all_device_health": {"queue": "health"},
}
