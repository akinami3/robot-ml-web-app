"""Security utilities (JWT helpers)."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(payload: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token."""

    to_encode = payload.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict[str, Any]:
    """Decode and validate JWT token."""

    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("invalid token") from exc
