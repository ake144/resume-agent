"""Schemas for job-related requests and responses."""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class JobIngestionRequest(BaseModel):
    """Request schema for job ingestion."""
    job_text: str = Field(..., description="Job description text")
    title: str = Field(..., description="Job title")
    company: Optional[str] = Field(None, description="Company name, if known")
    location: Optional[str] = Field(None, description="Job location, if known")
    source_url: Optional[HttpUrl] = Field(None, description="Source URL of the job posting")
    source_type: str = Field("manual_paste", description="Permitted provider or manual source")
    source_id: Optional[UUID] = Field(None, description="Configured source record")

    class Config:
        json_schema_extra = {
            "example": {
                "job_text": "We are looking for a senior Python developer...",
                "title": "Senior Python Developer",
                "company": "Example Corp",
                "location": "Remote",
                "source_url": "https://example.com/jobs/123"
            }
        }


class JobMatchRequest(BaseModel):
    """Request schema for job matching."""
    job_text: str = Field(..., description="Job description text")
    job_title: str = Field(..., description="Job title")
    job_posting_id: Optional[UUID] = Field(None, description="Owned posting to attach the match to")

    class Config:
        json_schema_extra = {
            "example": {
                "job_text": "We are looking for a senior Python developer...",
                "job_title": "Senior Python Developer"
            }
        }


class JobMatchResponse(BaseModel):
    """Response schema for job matching."""
    match_score: int = Field(..., ge=0, le=100, description="Overall match score (0-100)")
    strong_matches: List[str] = Field(..., description="List of strong matches with citations")
    skill_gaps: List[str] = Field(default_factory=list, description="Potential skill gaps")
    tailoring_recommendations: List[str] = Field(..., description="Tailoring recommendations")
    overall_verdict: str = Field(..., description="Overall verdict on fit")
    confidence_level: str = Field(..., description="Confidence level (High/Medium/Low)")
    preference_alignment: str = Field(default="Unknown")
    hard_constraints: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "match_score": 85,
                "strong_matches": ["5+ years Python experience", "FastAPI expertise"],
                "skill_gaps": ["Kubernetes experience"],
                "tailoring_recommendations": ["Emphasize cloud deployment experience"],
                "overall_verdict": "Strong candidate",
                "confidence_level": "High"
            }
            }


class MatchResultSummaryResponse(BaseModel):
    id: UUID
    job_posting_id: UUID
    matcher_version: str
    match_score: int
    confidence_level: str
    preference_alignment: str
    skill_gaps: List[str]
    hard_constraints: List[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MatchResultDetailResponse(MatchResultSummaryResponse):
    strong_matches: List[str]
    tailoring_recommendations: List[str]
    sources: List[dict]


class JobPostingResponse(BaseModel):
    id: UUID
    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: str
    source_url: Optional[str] = None
    source_type: str
    source_id: Optional[UUID] = None
    discovery_status: str
    discovered_at: datetime
    expires_at: Optional[datetime] = None
    is_expired: bool
    latest_match_score: Optional[int] = None


class JobSourceCreate(BaseModel):
    provider: str
    source_key: str
    enabled: bool = True
    config: Optional[dict] = None


class JobSourceResponse(JobSourceCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DiscoveryResponse(BaseModel):
    source_id: UUID
    provider: str
    jobs_seen: int
    created: int
    updated: int


class LocalSourcePresetResponse(BaseModel):
    provider: str
    label: str
    region: str
    homepage: str
    mode: str
    notes: str
