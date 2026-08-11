"""Logging configuration for the application."""
import logging
import logging.config
from pathlib import Path

from app.core.config import settings


def configure_logging() -> None:
    """Configure application-wide logging (console + size-capped rotating file)."""
    log_level_name = settings.log_level.upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
                "formatter": "standard",
                "filename": str(log_dir / "app.log"),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 3,
            }
        },
        "loggers": {
            "": {  # root logger
                "level": logging.INFO,
                "handlers": ["console", "file"]
            },
            "app": {
                "level": log_level,
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn": {
                "level": logging.INFO,
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": logging.INFO,
                "handlers": ["console", "file"],
                "propagate": False
            },
            "uvicorn.access": {
                "level": logging.WARNING,
                "handlers": ["console"],
                "propagate": False
            },
            "watchfiles": {
                "level": logging.WARNING,
                "handlers": ["console"],
                "propagate": False
            },
            "watchfiles.main": {
                "level": logging.WARNING,
                "handlers": ["console"],
                "propagate": False
            }
        }
    }

    logging.config.dictConfig(logging_config)
