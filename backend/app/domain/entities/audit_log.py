"""Audit log domain entity."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


class AuditAction(str, enum.Enum):
    # Auth
    LOGIN = "login"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    # Robot control
    ROBOT_CONNECT = "robot_connect"
    ROBOT_DISCONNECT = "robot_disconnect"
    VELOCITY_COMMAND = "velocity_command"
    NAVIGATION_START = "navigation_start"
    NAVIGATION_CANCEL = "navigation_cancel"
    # Safety
    ESTOP_ACTIVATE = "estop_activate"
    ESTOP_RELEASE = "estop_release"
    OPERATION_LOCK_ACQUIRE = "operation_lock_acquire"
    OPERATION_LOCK_RELEASE = "operation_lock_release"
    # Data
    RECORDING_START = "recording_start"
    RECORDING_STOP = "recording_stop"
    DATASET_CREATE = "dataset_create"
    DATASET_EXPORT = "dataset_export"
    DATASET_DELETE = "dataset_delete"
    # RAG
    DOCUMENT_UPLOAD = "document_upload"
    DOCUMENT_DELETE = "document_delete"
    RAG_QUERY = "rag_query"
    # Admin
    USER_CREATE = "user_create"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    SETTINGS_CHANGE = "settings_change"


@dataclass
class AuditLog:
    user_id: UUID
    action: AuditAction
    id: UUID = field(default_factory=uuid4)
    resource_type: str = ""
    resource_id: str = ""
    details: dict[str, Any] = field(default_factory=dict)
    ip_address: str = ""
    user_agent: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
