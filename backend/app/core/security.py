"""Security utilities - JWT tokens, password hashing."""

from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_tokens(
    *,
    user_id: str,
    role: str,
    private_key: str | None = None,
    access_expire_minutes: int = 15,
    refresh_expire_days: int = 7,
) -> dict[str, str]:
    """Create both access and refresh tokens."""
    settings = get_settings()
    key = private_key if private_key else settings.secret_key
    algorithm = settings.jwt_algorithm if private_key else "HS256"

    now = datetime.now(UTC)

    access_payload = {
        "sub": user_id,
        "role": role,
        "exp": now + timedelta(minutes=access_expire_minutes),
        "type": "access",
    }
    refresh_payload = {
        "sub": user_id,
        "role": role,
        "exp": now + timedelta(days=refresh_expire_days),
        "type": "refresh",
    }

    return {
        "access_token": jwt.encode(access_payload, key, algorithm=algorithm),
        "refresh_token": jwt.encode(refresh_payload, key, algorithm=algorithm),
    }


def create_access_token(data: dict[str, Any]) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.jwt_access_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})

    private_key = settings.jwt_private_key
    if private_key is None:
        return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")

    return jwt.encode(to_encode, private_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict[str, Any]) -> str:
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.jwt_refresh_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})

    private_key = settings.jwt_private_key
    if private_key is None:
        return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")

    return jwt.encode(to_encode, private_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str, public_key: str | None = None) -> dict[str, Any] | None:
    settings = get_settings()
    try:
        key = public_key if public_key else settings.jwt_public_key
        if key is None:
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        else:
            payload = jwt.decode(token, key, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
