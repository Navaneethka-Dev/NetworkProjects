"""Audit Log API — /api/audit-logs/*

Exposes the audit trail of user actions for the activity feed page.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db
from app.core.rbac import require_admin, require_viewer
from app.models.audit_log import AuditLog
from app.models.user import User

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


@router.get("")
async def list_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: str | None = Query(None, description="Filter by action keyword"),
    resource_type: str | None = Query(None),
    user_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    """Return paginated audit log entries, newest first."""
    query = select(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
    if action:
        query = query.where(AuditLog.action.ilike(f"%{action}%"))
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)

    result = await db.execute(query)
    logs = result.scalars().all()

    # Enrich with username
    user_ids = {log.user_id for log in logs if log.user_id}
    usernames: dict[uuid.UUID, str] = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        for u in users_result.scalars().all():
            usernames[u.id] = u.username

    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "username": usernames.get(log.user_id) if log.user_id else None,
            "action": log.action,
            "resource_type": log.resource_type,
            "resource_id": str(log.resource_id) if log.resource_id else None,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": log.created_at.isoformat(),
        }
        for log in logs
    ]


@router.get("/summary")
async def audit_summary(
    db: AsyncSession = Depends(get_db),
    _=Depends(require_viewer),
):
    """Quick stats for the activity page header."""
    from sqlalchemy import func
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    total_result = await db.execute(select(func.count(AuditLog.id)))
    total = total_result.scalar() or 0

    day_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.created_at >= day_ago)
    )
    today_count = day_result.scalar() or 0

    week_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.created_at >= week_ago)
    )
    week_count = week_result.scalar() or 0

    # Unique users in last 7 days
    users_result = await db.execute(
        select(func.count(func.distinct(AuditLog.user_id))).where(AuditLog.created_at >= week_ago)
    )
    active_users = users_result.scalar() or 0

    return {
        "total_events": total,
        "events_today": today_count,
        "events_this_week": week_count,
        "active_users_this_week": active_users,
    }


@router.delete("/{log_id}", status_code=204)
async def delete_log(
    log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin),
):
    """Delete a single audit log entry (admin only)."""
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()
    if log:
        await db.delete(log)
        await db.flush()
