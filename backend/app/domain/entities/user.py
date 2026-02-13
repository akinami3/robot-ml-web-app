"""User domain entity."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


@dataclass
class User:
    username: str
    email: str
    role: UserRole
    hashed_password: str = ""
    id: UUID = field(default_factory=uuid4)
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def can_control_robot(self) -> bool:
        return self.role in (UserRole.ADMIN, UserRole.OPERATOR)

    def can_manage_users(self) -> bool:
        return self.role == UserRole.ADMIN

    def can_view_data(self) -> bool:
        return True
