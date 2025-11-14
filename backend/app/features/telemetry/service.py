"""Feature-level exports for telemetry use cases."""

from app.application.use_cases.telemetry import (
    DataLoggerUseCase,
    TelemetryMessage,
    TelemetryProcessorUseCase,
)

# Backwards-compatible aliases.
DataLoggerService = DataLoggerUseCase
TelemetryProcessorService = TelemetryProcessorUseCase

__all__ = [
    "DataLoggerService",
    "DataLoggerUseCase",
    "TelemetryMessage",
    "TelemetryProcessorService",
    "TelemetryProcessorUseCase",
]
