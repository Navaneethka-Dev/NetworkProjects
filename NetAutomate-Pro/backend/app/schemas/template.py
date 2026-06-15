"""Pydantic schemas for ConfigTemplate."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    vendor: str = Field(..., description="cisco | juniper | arista | any")
    template_content: str = Field(..., min_length=1)
    variables_schema: dict = Field(default_factory=dict)


class TemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    vendor: str | None = None
    template_content: str | None = None
    variables_schema: dict | None = None


class TemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    vendor: str
    template_content: str
    variables_schema: dict
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class TemplateSummary(BaseModel):
    """Lightweight response without template_content (for list views)."""
    id: uuid.UUID
    name: str
    description: str | None
    vendor: str
    variables_schema: dict
    created_at: datetime
    model_config = {"from_attributes": True}


class TemplatePreviewRequest(BaseModel):
    variables: dict = Field(default_factory=dict)
    device_hostname: str | None = None


class TemplatePreviewResponse(BaseModel):
    rendered_config: str
    variables_used: dict
    template_name: str
