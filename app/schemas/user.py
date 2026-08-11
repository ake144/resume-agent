"""Schemas for user registration and identity."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserRegistrationRequest(BaseModel):
    """Request schema for account registration."""
    email: EmailStr = Field(..., description="Account email address")
    full_name: str | None = Field(None, description="Seeds the auto-created profile's full_name")


class UserRegistrationResponse(BaseModel):
    """Response schema for account registration.

    api_key is the raw key, returned exactly once - it cannot be recovered
    after this response since only its hash is stored.
    """
    id: UUID
    email: EmailStr
    api_key: str
    created_at: datetime


class UserResponse(BaseModel):
    """Response schema for the authenticated user's own identity."""
    id: UUID
    email: EmailStr
    created_at: datetime
