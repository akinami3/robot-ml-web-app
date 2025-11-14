"""Gateway re-exporting all dependency providers."""

from __future__ import annotations

from app.core.base_dependencies import (
    get_celery_app,
    get_dataset_session_repository,
    get_db_session,
    get_llm_client,
    get_mqtt_adapter,
    get_rag_repository,
    get_robot_state_repository,
    get_sensor_data_repository,
    get_training_metric_repository,
    get_training_run_repository,
    get_vector_store,
    get_websocket_hub,
    get_unit_of_work,
)
from app.features.chat.dependencies import get_chatbot_service
from app.features.ml.dependencies import get_ml_pipeline_service
from app.features.robot.dependencies import get_robot_control_service
from app.features.telemetry.dependencies import (
    get_datalogger_service,
    get_telemetry_processor_service,
)

__all__ = [
    "get_celery_app",
    "get_dataset_session_repository",
    "get_db_session",
    "get_llm_client",
    "get_mqtt_adapter",
    "get_rag_repository",
    "get_robot_control_service",
    "get_robot_state_repository",
    "get_sensor_data_repository",
    "get_training_metric_repository",
    "get_training_run_repository",
    "get_vector_store",
    "get_websocket_hub",
    "get_unit_of_work",
    "get_chatbot_service",
    "get_ml_pipeline_service",
    "get_datalogger_service",
    "get_telemetry_processor_service",
]
