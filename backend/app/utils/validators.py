"""Input validation helpers."""

from __future__ import annotations

from fastapi import HTTPException, status


def ensure_positive(value: float, name: str) -> float:
    if value < 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{name} must be non-negative",
        )
    return value
