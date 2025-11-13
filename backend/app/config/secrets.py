"""Secret management utilities."""

from __future__ import annotations

from typing import Any


class SecretStore:
    """Placeholder secret storage."""

    def __init__(self) -> None:
        self._secrets: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._secrets[key] = value

    def get(self, key: str, default: Any | None = None) -> Any:
        return self._secrets.get(key, default)


secret_store = SecretStore()
