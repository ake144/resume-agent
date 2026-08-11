"""Schemas for the authenticated user's structured profile data:
contact info, work history, education, and skills.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    links: Optional[dict] = None
    summary: Optional[str] = None


class UserProfileResponse(BaseModel):
    user_id: UUID
    full_name: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    links: Optional[dict] = None
    summary: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkHistoryEntryCreate(BaseModel):
    company: str
    job_title: str
    location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None  # None = current/ongoing
    description: Optional[str] = None


class WorkHistoryEntryUpdate(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    description: Optional[str] = None


class WorkHistoryEntryResponse(BaseModel):
    id: UUID
    company: str
    job_title: str
    location: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class EducationEntryCreate(BaseModel):
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[str] = None
    description: Optional[str] = None


class EducationEntryUpdate(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[str] = None
    description: Optional[str] = None


class EducationEntryResponse(BaseModel):
    id: UUID
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SkillEntryCreate(BaseModel):
    name: str
    category: Optional[str] = None
    proficiency: Optional[str] = None


class SkillEntryUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    proficiency: Optional[str] = None


class SkillEntryResponse(BaseModel):
    id: UUID
    name: str
    category: Optional[str] = None
    proficiency: Optional[str] = None

    class Config:
        from_attributes = True
