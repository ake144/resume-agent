"""Logging configuration for the application."""
import logging
import logging.config
from pathlib import Path

from app.core.config import settings


def configure_logging() -> None:
    """Configure application-wide logging."""
    log_level = logging.INFO if settings.environment == "production" else logging.DEBUG
    log_file = Path(__file__).resolve().parents[2] / "logs" / "app.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "detailed",
                "filename": str(log_file),
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            }
        },
        "loggers": {
            "": {  # root logger
                "level": log_level,
                "handlers": ["console", "file"]
            },
            "uvicorn": {
                "level": logging.INFO,
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": logging.INFO,
                "handlers": ["console"],
                "propagate": False
            }
        }
    }

    logging.config.dictConfig(logging_config)
