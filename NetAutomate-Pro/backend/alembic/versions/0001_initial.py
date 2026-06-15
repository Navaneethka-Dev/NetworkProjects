"""Initial schema — all tables.

Revision ID: 0001
Revises:
Create Date: 2026-06-15
"""
from __future__ import annotations

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("username", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            sa.Enum("admin", "operator", "viewer", name="roleenum"),
            nullable=False,
            server_default="viewer",
        ),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── device_groups ──────────────────────────────────────────────────────────
    op.create_table(
        "device_groups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── devices ────────────────────────────────────────────────────────────────
    op.create_table(
        "devices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("hostname", sa.String(255), nullable=False, index=True),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("device_type", sa.String(50), nullable=False),
        sa.Column("vendor", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("ssh_port", sa.Integer, nullable=False, server_default="22"),
        sa.Column("username", sa.String(100), nullable=False),
        sa.Column("password", sa.Text, nullable=False),
        sa.Column("secret", sa.Text, nullable=True),
        sa.Column(
            "status",
            sa.Enum("online", "offline", "unreachable", "maintenance", "unknown", name="devicestatusenum"),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column(
            "group_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("device_groups.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("last_checked", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── config_templates ───────────────────────────────────────────────────────
    op.create_table(
        "config_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("name", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("vendor", sa.String(50), nullable=False, server_default="cisco"),
        sa.Column("template_content", sa.Text, nullable=False),
        sa.Column("variables_schema", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── deployments ────────────────────────────────────────────────────────────
    op.create_table(
        "deployments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "template_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("config_templates.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "deployment_type",
            sa.Enum("single", "bulk", "scheduled", name="deploymenttypeenum"),
            nullable=False,
            server_default="single",
        ),
        sa.Column("target_devices", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("rendered_config", sa.Text, nullable=True),
        sa.Column("variables_used", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column(
            "status",
            sa.Enum("pending", "running", "completed", "failed", "rolled_back", name="deploymentstatusenum"),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "deployed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── deployment_logs ────────────────────────────────────────────────────────
    op.create_table(
        "deployment_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "deployment_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("deployments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "device_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("devices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("device_hostname", sa.String(255), nullable=True),
        sa.Column(
            "status",
            sa.Enum("success", "failed", "skipped", name="deploymentlogstatusenum"),
            nullable=False,
        ),
        sa.Column("output", sa.Text, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("duration_seconds", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── backups ────────────────────────────────────────────────────────────────
    op.create_table(
        "backups",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "device_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("devices.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("config_content", sa.Text, nullable=False),
        sa.Column(
            "backup_type",
            sa.Enum("manual", "scheduled", "pre_deployment", name="backuptypeenum"),
            nullable=False,
            server_default="manual",
        ),
        sa.Column("version_tag", sa.String(50), nullable=False),
        sa.Column("checksum", sa.String(64), nullable=False),
        sa.Column(
            "created_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── audit_logs ─────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(255), nullable=False, index=True),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("details", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("backups")
    op.drop_table("deployment_logs")
    op.drop_table("deployments")
    op.drop_table("config_templates")
    op.drop_table("devices")
    op.drop_table("device_groups")
    op.drop_table("users")

    # Drop custom enum types
    for enum_name in [
        "roleenum", "devicestatusenum", "deploymenttypeenum",
        "deploymentstatusenum", "deploymentlogstatusenum", "backuptypeenum",
    ]:
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
