"""AuditLog model — portable across SQLite and PostgreSQL."""
import json
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    _details: Mapped[str] = mapped_column("details", Text, nullable=False, default="{}")
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped["User | None"] = relationship(back_populates="audit_logs")  # type: ignore[name-defined]

    @property
    def details(self) -> dict:
        try:
            return json.loads(self._details)
        except Exception:
            return {}

    @details.setter
    def details(self, value: dict) -> None:
        self._details = json.dumps(value)

    def __repr__(self) -> str:
        return f"<AuditLog {self.action} by user={self.user_id}>"
