"""Logging configuration for the application."""
import logging
import logging.config

from app.core.config import settings


def configure_logging() -> None:
    """Configure application-wide logging (console only due to disk full)."""
    log_level_name = settings.log_level.upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

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
            }
        },
        "loggers": {
            "": {  # root logger
                "level": logging.INFO,
                "handlers": ["console"]
            },
            "app": {
                "level": log_level,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn": {
                "level": logging.INFO,
                "handlers": ["console"],
                "propagate": False
            },
            "uvicorn.error": {
                "level": logging.INFO,
                "handlers": ["console"],
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
