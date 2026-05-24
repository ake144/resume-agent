"""Schemas for job-related requests and responses."""
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List


class JobIngestionRequest(BaseModel):
    """Request schema for job ingestion."""
    user_id: str = Field(..., description="User ID")
    job_text: str = Field(..., description="Job description text")
    title: str = Field(..., description="Job title")
    source_url: Optional[HttpUrl] = Field(None, description="Source URL of the job posting")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "job_text": "We are looking for a senior Python developer...",
                "title": "Senior Python Developer",
                "source_url": "https://example.com/jobs/123"
            }
        }


class JobMatchRequest(BaseModel):
    """Request schema for job matching."""
    user_id: str = Field(..., description="User ID")
    job_text: str = Field(..., description="Job description text")
    job_title: str = Field(..., description="Job title")

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
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
