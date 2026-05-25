"""Application configuration."""
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    api_title: str = "Resume Agent API"
    api_version: str = "1.0.0"
    api_description: str = "AI-powered API for resume analysis and job matching"

    # Environment
    environment: str = "development"

    # API Keys
    groq_api_key: str
    
    # Database
    database_url: str

    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173", "http://localhost:8000"]
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    cors_credentials: bool = False

    # Server
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    reload: bool = False

    # Logging
    log_level: str = "INFO"
    log_dir: str = str(Path.home() / ".cache" / "resume-agent" / "logs")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"


# Create global settings instance
settings = Settings()