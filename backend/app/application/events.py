"""Application-level event and channel definitions."""

from __future__ import annotations

from enum import Enum


# Channel identifiers consumed by realtime broadcasters and infrastructure layers.
ROBOT_CHANNEL = "robot"
TELEMETRY_CHANNEL = "telemetry"
ML_CHANNEL = "ml"
CHAT_CHANNEL = "chat"


class RobotEvent(str, Enum):
    VELOCITY = "velocity"
    NAVIGATION = "navigation"


class TelemetryEvent(str, Enum):
    STREAM_UPDATE = "stream_update"


class MLEvent(str, Enum):
    TRAINING_QUEUED = "training_queued"


class ChatEvent(str, Enum):
    MESSAGE = "message"


__all__ = [
    "ROBOT_CHANNEL",
    "TELEMETRY_CHANNEL",
    "ML_CHANNEL",
    "CHAT_CHANNEL",
    "RobotEvent",
    "TelemetryEvent",
    "MLEvent",
    "ChatEvent",
]
