"""Pydantic schemas for Backup."""
import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.backup import BackupTypeEnum


class BackupCreate(BaseModel):
    device_id: uuid.UUID
    backup_type: BackupTypeEnum = BackupTypeEnum.manual


class BackupResponse(BaseModel):
    id: uuid.UUID
    device_id: uuid.UUID
    device_hostname: str | None = None
    backup_type: BackupTypeEnum
    version_tag: str
    checksum: str
    config_size: int = 0
    created_by: uuid.UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}


class BackupDetailResponse(BackupResponse):
    config_content: str


class BackupDiffResponse(BaseModel):
    backup_a_id: uuid.UUID
    backup_b_id: uuid.UUID
    backup_a_tag: str
    backup_b_tag: str
    unified_diff: str
    lines_added: int
    lines_removed: int
    lines_unchanged: int


class BackupRestoreRequest(BaseModel):
    backup_id: uuid.UUID
    dry_run: bool = True
