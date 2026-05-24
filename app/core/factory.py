"""Application factory for creating FastAPI app with all configurations."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.logging import configure_logging
from app.api.middleware import ErrorHandlingMiddleware, RequestLoggingMiddleware
from app.api.v1.router import api_router
from app.utils.scheduler import start_scheduler, scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown logic.
    """
    # Startup
    logger.info("Starting Resume Agent API")
    logger.info(f"Environment: {settings.environment}")
    start_scheduler()
    logger.info("Scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Resume Agent API")
    scheduler.shutdown()
    logger.info("Scheduler stopped")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI instance
    """
    # Configure logging first
    configure_logging()
    logger.info("Logging configured")
    
    # Create FastAPI app
    app = FastAPI(
        title=settings.api_title,
        description=settings.api_description,
        version=settings.api_version,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Add middleware
    logger.info("Adding middleware")
    
    # CORS middleware (should be first)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=settings.cors_methods,
        allow_headers=settings.cors_headers,
        allow_credentials=settings.cors_credentials
    )
    
    # Custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Include API routers
    logger.info("Including API routers")
    app.include_router(api_router)
    
    # Add root endpoint
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "Welcome to Resume Agent API!",
            "status": "success",
            "docs": "/docs",
            "version": settings.api_version
        }
    
    logger.info("FastAPI application created successfully")
    
    return app
