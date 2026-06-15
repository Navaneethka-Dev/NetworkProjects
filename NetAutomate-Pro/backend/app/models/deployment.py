"""Deployment and DeploymentLog models — portable across SQLite and PostgreSQL."""
import enum
import json
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DeploymentStatusEnum(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    rolled_back = "rolled_back"


class DeploymentTypeEnum(str, enum.Enum):
    single = "single"
    bulk = "bulk"
    scheduled = "scheduled"


class DeploymentLogStatusEnum(str, enum.Enum):
    success = "success"
    failed = "failed"
    skipped = "skipped"


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("config_templates.id", ondelete="SET NULL"), nullable=True
    )
    deployment_type: Mapped[DeploymentTypeEnum] = mapped_column(
        Enum(DeploymentTypeEnum, name="deploymenttypeenum"), nullable=False, default=DeploymentTypeEnum.single
    )
    # Store JSON as text for SQLite compatibility
    _target_devices: Mapped[str] = mapped_column("target_devices", Text, nullable=False, default="[]")
    rendered_config: Mapped[str | None] = mapped_column(Text, nullable=True)
    _variables_used: Mapped[str] = mapped_column("variables_used", Text, nullable=False, default="{}")
    status: Mapped[DeploymentStatusEnum] = mapped_column(
        Enum(DeploymentStatusEnum, name="deploymentstatusenum"),
        nullable=False, default=DeploymentStatusEnum.pending
    )
    deployed_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    celery_task_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    template: Mapped["ConfigTemplate | None"] = relationship(back_populates="deployments")  # type: ignore[name-defined]
    deployed_by_user: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        back_populates="deployments", foreign_keys=[deployed_by]
    )
    logs: Mapped[list["DeploymentLog"]] = relationship(
        back_populates="deployment", cascade="all, delete-orphan"
    )

    @property
    def target_devices(self) -> list:
        try:
            return json.loads(self._target_devices)
        except Exception:
            return []

    @target_devices.setter
    def target_devices(self, value: list) -> None:
        self._target_devices = json.dumps(value)

    @property
    def variables_used(self) -> dict:
        try:
            return json.loads(self._variables_used)
        except Exception:
            return {}

    @variables_used.setter
    def variables_used(self, value: dict) -> None:
        self._variables_used = json.dumps(value)

    def __repr__(self) -> str:
        return f"<Deployment {self.id} ({self.status})>"


class DeploymentLog(Base):
    __tablename__ = "deployment_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    deployment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("deployments.id", ondelete="CASCADE"), nullable=False
    )
    device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False
    )
    device_hostname: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[DeploymentLogStatusEnum] = mapped_column(
        Enum(DeploymentLogStatusEnum, name="deploymentlogstatusenum"), nullable=False
    )
    output: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    deployment: Mapped[Deployment] = relationship(back_populates="logs")
    device: Mapped["Device"] = relationship(back_populates="deployment_logs")  # type: ignore[name-defined]
