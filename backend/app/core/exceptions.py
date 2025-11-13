"""Application specific exceptions."""

from __future__ import annotations


class ApplicationError(Exception):
    """Base application error."""


class ResourceNotFoundError(ApplicationError):
    """Raised when an entity is not found."""


class ValidationError(ApplicationError):
    """Raised when business validation fails."""


class SessionInactiveError(ApplicationError):
    """Raised when trying to persist data without an active session."""
