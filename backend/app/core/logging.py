"""Structured logging configuration for the application."""

from __future__ import annotations

import logging
from typing import Any

import structlog

from .config import settings


def configure_logging() -> None:
    """Configure stdlib + structlog logging according to settings."""

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        timestamper,
        structlog.processors.add_log_level,
    ]

    if settings.log_json:
        renderer: Any = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    structlog.configure(
        processors=shared_processors
        + [
            structlog.processors.EventRenamer("message"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level.upper(), logging.INFO)),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=settings.log_level)
