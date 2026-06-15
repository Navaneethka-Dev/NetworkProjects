"""Pydantic schemas for Device and DeviceGroup."""
import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator
import ipaddress

from app.models.device import DeviceStatusEnum


# ── DeviceGroup ───────────────────────────────────────────────────────────────

class DeviceGroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None


class DeviceGroupUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None


class DeviceGroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    model_config = {"from_attributes": True}


# ── Device ────────────────────────────────────────────────────────────────────

class DeviceCreate(BaseModel):
    hostname: str = Field(..., min_length=1, max_length=255)
    ip_address: str
    device_type: str = Field(..., description="cisco_ios | cisco_nxos | cisco_xe | juniper_junos | arista_eos")
    vendor: str = Field(..., description="cisco | juniper | arista")
    model: str | None = None
    ssh_port: int = Field(22, ge=1, le=65535)
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)
    secret: str | None = None
    group_id: uuid.UUID | None = None

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        try:
            ipaddress.ip_address(v)
        except ValueError:
            raise ValueError(f"Invalid IP address: {v}")
        return v


class DeviceUpdate(BaseModel):
    hostname: str | None = None
    ip_address: str | None = None
    device_type: str | None = None
    vendor: str | None = None
    model: str | None = None
    ssh_port: int | None = Field(None, ge=1, le=65535)
    username: str | None = None
    password: str | None = None
    secret: str | None = None
    status: DeviceStatusEnum | None = None
    group_id: uuid.UUID | None = None

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, v: str | None) -> str | None:
        if v is not None:
            try:
                ipaddress.ip_address(v)
            except ValueError:
                raise ValueError(f"Invalid IP address: {v}")
        return v


class DeviceResponse(BaseModel):
    id: uuid.UUID
    hostname: str
    ip_address: str
    device_type: str
    vendor: str
    model: str | None
    ssh_port: int
    username: str
    status: DeviceStatusEnum
    group_id: uuid.UUID | None
    last_checked: datetime | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class DevicePingResponse(BaseModel):
    device_id: uuid.UUID
    hostname: str
    reachable: bool
    message: str
    latency_ms: float | None = None
