"""Main API router configuration."""
from fastapi import APIRouter
from app import api
from app.api.v1.endpoints import health, job, application, resume, users, profile

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(health.router, prefix="", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(profile.router, prefix="/profile", tags=["profile"])
api_router.include_router(job.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(application.router, prefix="/applications", tags=["applications"])
api_router.include_router(resume.router, prefix="/resume", tags=["resume"])
