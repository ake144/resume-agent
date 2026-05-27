"""Dependency injection providers for FastAPI endpoints."""
from typing import Optional
from fastapi import Depends
from app.services.job_service import JobService
from app.services.application_service import ApplicationService
from app.services.resume import ResumeSerives


# Service instances (can be replaced with full DI container in larger projects)
_job_service: Optional[JobService] = None
_application_service: Optional[ApplicationService] = None
_resume_service: Optional[ResumeSerives] = None


def get_job_service() -> JobService:
    """Get job service instance."""
    global _job_service
    if _job_service is None:
        _job_service = JobService()
    return _job_service


def get_application_service() -> ApplicationService:
    """Get application service instance."""
    global _application_service
    if _application_service is None:
        _application_service = ApplicationService()
    return _application_service


def get_resume_service() -> ResumeSerives:
    """Get resume service instance."""
    global _resume_service
    if _resume_service is None:
        _resume_service = ResumeSerives()
    return _resume_service
