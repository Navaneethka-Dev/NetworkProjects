"""Pydantic schemas for Deployment and DeploymentLog."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.deployment import DeploymentStatusEnum, DeploymentTypeEnum, DeploymentLogStatusEnum


class DeploymentCreate(BaseModel):
    template_id: uuid.UUID
    device_ids: list[uuid.UUID] = Field(..., min_length=1)
    variables: dict = Field(default_factory=dict)
    deployment_type: DeploymentTypeEnum = DeploymentTypeEnum.single
    dry_run: bool = False


class DeploymentLogResponse(BaseModel):
    id: uuid.UUID
    deployment_id: uuid.UUID
    device_id: uuid.UUID
    device_hostname: str | None = None
    status: DeploymentLogStatusEnum
    output: str | None
    error_message: str | None
    duration_seconds: float | None
    created_at: datetime
    model_config = {"from_attributes": True}


class DeploymentResponse(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID | None
    template_name: str | None = None
    deployment_type: DeploymentTypeEnum
    target_devices: list
    rendered_config: str | None
    variables_used: dict
    status: DeploymentStatusEnum
    deployed_by: uuid.UUID | None
    celery_task_id: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    logs: list[DeploymentLogResponse] = []
    model_config = {"from_attributes": True}


class DeploymentSummary(BaseModel):
    id: uuid.UUID
    template_id: uuid.UUID | None
    template_name: str | None = None
    deployment_type: DeploymentTypeEnum
    status: DeploymentStatusEnum
    device_count: int = 0
    deployed_by: uuid.UUID | None
    created_at: datetime
    model_config = {"from_attributes": True}
