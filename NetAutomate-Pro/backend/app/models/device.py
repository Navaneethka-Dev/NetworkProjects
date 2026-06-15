"""Device and DeviceGroup models — portable across SQLite and PostgreSQL."""
import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DeviceStatusEnum(str, enum.Enum):
    online = "online"
    offline = "offline"
    unreachable = "unreachable"
    maintenance = "maintenance"
    unknown = "unknown"


class DeviceGroup(Base):
    __tablename__ = "device_groups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    devices: Mapped[list["Device"]] = relationship(back_populates="group")

    def __repr__(self) -> str:
        return f"<DeviceGroup {self.name}>"


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    hostname: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    device_type: Mapped[str] = mapped_column(String(50), nullable=False)
    vendor: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    ssh_port: Mapped[int] = mapped_column(Integer, nullable=False, default=22)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DeviceStatusEnum] = mapped_column(
        Enum(DeviceStatusEnum, name="devicestatusenum"),
        nullable=False, default=DeviceStatusEnum.unknown
    )
    group_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("device_groups.id", ondelete="SET NULL"), nullable=True
    )
    last_checked: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    group: Mapped[DeviceGroup | None] = relationship(back_populates="devices")
    created_by_user: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        back_populates="devices", foreign_keys=[created_by]
    )
    backups: Mapped[list["Backup"]] = relationship(  # type: ignore[name-defined]
        back_populates="device", cascade="all, delete-orphan"
    )
    deployment_logs: Mapped[list["DeploymentLog"]] = relationship(  # type: ignore[name-defined]
        back_populates="device"
    )

    def __repr__(self) -> str:
        return f"<Device {self.hostname} ({self.ip_address})>"
