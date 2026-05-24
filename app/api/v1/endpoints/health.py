"""Health check endpoints."""
from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy", "message": "Service is running"}


@router.get("/readiness")
async def readiness_check():
    """
    Readiness check endpoint for load balancers.

    Returns:
        Readiness status
    """
    return {"status": "ready", "message": "Service is ready to accept requests"}
