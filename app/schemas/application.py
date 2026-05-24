"""Schemas for application generation requests and responses."""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class ApplicationType(str, Enum):
    """Supported application types."""
    COVER_LETTER = "cover_letter"
    RESUME_TAILORING = "resume_tailoring"
    INTERVIEW_PREP = "interview_prep"


class ApplicationGenerationRequest(BaseModel):
    """Request schema for application generation."""
    user_id: str = Field(..., description="User ID")
    job_description: str = Field(..., description="Job description")
    job_title: str = Field(..., description="Job title")
    application_type: ApplicationType = Field(
        default=ApplicationType.COVER_LETTER,
        description="Type of application to generate"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "job_description": "Senior Python Developer role...",
                "job_title": "Senior Python Developer",
                "application_type": "cover_letter"
            }
        }


class ApplicationGenerationResponse(BaseModel):
    """Response schema for application generation."""
    user_id: str = Field(..., description="User ID")
    job_title: str = Field(..., description="Job title")
    application_type: ApplicationType = Field(..., description="Type of application")
    content: str = Field(..., description="Generated content")
    generated_at: str = Field(..., description="Timestamp of generation")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "job_title": "Senior Python Developer",
                "application_type": "cover_letter",
                "content": "Dear Hiring Manager...",
                "generated_at": "2026-05-24T10:30:00Z"
            }
        }


class WorkflowRequest(BaseModel):
    """Request schema for full application workflow."""
    user_id: str = Field(..., description="User ID")
    job_description: str = Field(..., description="Job description")
    job_title: str = Field(..., description="Job title")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "job_description": "Senior Python Developer role...",
                "job_title": "Senior Python Developer"
            }
        }
