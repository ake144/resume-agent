"""Schemas for application generation requests and responses."""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from enum import Enum


class ApplicationType(str, Enum):
    """Supported application types."""
    COVER_LETTER = "cover_letter"
    RESUME_TAILORING = "resume_tailoring"
    INTERVIEW_PREP = "interview_prep"
    LINKEDIN_MESSAGE = "linkedin_message"
    UPWORK_PROPOSAL = "upwork_proposal"
    COLD_PITCH = "cold_pitch"


class ApplicationStatus(str, Enum):
    """Lifecycle status of a tracked Application row."""
    DRAFT = "draft"
    GENERATED = "generated"
    SUBMITTED = "submitted"
    INTERVIEWING = "interviewing"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApplicationGenerationRequest(BaseModel):
    """Request schema for application generation."""
    job_description: str = Field(..., description="Job description")
    job_title: str = Field(..., description="Job title")
    application_type: ApplicationType = Field(
        default=ApplicationType.COVER_LETTER,
        description="Type of application to generate"
    )
    job_posting_id: Optional[UUID] = Field(
        default=None, description="Optional JobPosting to link this application to"
    )

    class Config:
        json_schema_extra = {
            "example": {
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
    match_score: int = Field(..., description="Overall match score (0-100) used to ground generation")
    sources_used: int = Field(..., description="Number of retrieved source chunks used to ground generation")
    generated_at: str = Field(..., description="Timestamp of generation")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "job_title": "Senior Python Developer",
                "application_type": "cover_letter",
                "content": "Dear Hiring Manager...",
                "match_score": 85,
                "sources_used": 4,
                "generated_at": "2026-05-24T10:30:00Z"
            }
        }


class WorkflowRequest(BaseModel):
    """Request schema for full application workflow."""
    job_description: str = Field(..., description="Job description")
    job_title: str = Field(..., description="Job title")
    job_posting_id: Optional[UUID] = Field(
        default=None, description="Optional JobPosting to link this application to"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "job_description": "Senior Python Developer role...",
                "job_title": "Senior Python Developer"
            }
        }


class ApplicationSummaryResponse(BaseModel):
    """Summary schema for a single item in the applications list."""
    id: UUID
    job_title: str
    company: Optional[str] = None
    application_type: ApplicationType
    status: ApplicationStatus
    match_score: Optional[int] = None
    job_posting_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationDetailResponse(ApplicationSummaryResponse):
    """Full detail schema for a single application."""
    generated_content: str
    sources_used: Optional[int] = None
    match_analysis: Optional[dict] = None
    submitted_at: Optional[datetime] = None


class ApplicationListResponse(BaseModel):
    """Paginated list of applications, mirroring the shape the frontend
    already expects (content/totalItems/totalPages) to minimize its
    rewrite surface when swapping off the old backend."""
    content: list[ApplicationSummaryResponse]
    totalItems: int
    totalPages: int
