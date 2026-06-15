"""Pydantic schemas for User and Authentication."""
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import RoleEnum


# ── Request schemas ────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: RoleEnum = RoleEnum.viewer


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    role: RoleEnum | None = None
    is_active: bool | None = None
    password: str | None = Field(None, min_length=8)


# ── Response schemas ───────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    email: str
    role: RoleEnum
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(UserResponse):
    pass
