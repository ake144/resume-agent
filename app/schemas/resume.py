"""Schemas for job-related requests and responses."""
from fastapi import UploadFile
from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List


class ResumeIngestionRequest(BaseModel):
    """Request schema for resume ingestion."""
    file: Optional[UploadFile] = Field(None, description="Resume file upload")
    title: str = Field(..., description="My Resume")
    text: Optional[str] = Field(None, description="Resume text input (alternative to file upload)")

    class Config:
        json_schema_extra = {
            "example": {
                "file": "resume.pdf",
                "title": "Senior Python Developer",
                "text": "I am a senior Python developer with 5 years of experience..."
            }
        }