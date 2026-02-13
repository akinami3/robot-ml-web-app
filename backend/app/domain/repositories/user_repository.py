"""User repository interface."""

from __future__ import annotations

from abc import abstractmethod

from ..entities.user import User
from .base import BaseRepository


class UserRepository(BaseRepository[User]):
    @abstractmethod
    async def get_by_username(self, username: str) -> User | None:
        ...

    @abstractmethod
    async def get_by_email(self, email: str) -> User | None:
        ...

    @abstractmethod
    async def get_active_users(self) -> list[User]:
        ...
