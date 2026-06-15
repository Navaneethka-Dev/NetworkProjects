"""Backup model — portable across SQLite and PostgreSQL."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BackupTypeEnum(str, enum.Enum):
    manual = "manual"
    scheduled = "scheduled"
    pre_deployment = "pre_deployment"


class Backup(Base):
    __tablename__ = "backups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    config_content: Mapped[str] = mapped_column(Text, nullable=False)
    backup_type: Mapped[BackupTypeEnum] = mapped_column(
        Enum(BackupTypeEnum, name="backuptypeenum"), nullable=False, default=BackupTypeEnum.manual
    )
    version_tag: Mapped[str] = mapped_column(String(50), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    device: Mapped["Device"] = relationship(back_populates="backups")  # type: ignore[name-defined]

    def __repr__(self) -> str:
        return f"<Backup {self.version_tag} device={self.device_id}>"
