"""Feature-level exports for robot use cases.

This module intentionally remains thin, simply re-exporting the application-level
use cases so routers/tests can import them without knowing about layering
details. Feature code should focus on request/response translation, delegating
business orchestration to `application.use_cases`.
"""

from app.application.use_cases.robot import (
    NavigationGoalPayload,
    RobotControlUseCase,
    VelocityCommandPayload,
)

# Backwards-compatible aliases while the codebase migrates to explicit use case names.
RobotControlService = RobotControlUseCase

__all__ = [
    "NavigationGoalPayload",
    "RobotControlService",
    "RobotControlUseCase",
    "VelocityCommandPayload",
]
