"""Celery application instance."""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "robot_ml_backend",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.task_routes = {
    "app.workers.tasks.train_model_task": {"queue": "ml"},
    "app.workers.tasks.process_batch_telemetry": {"queue": "telemetry"},
}

celery_app.conf.update(task_track_started=True, task_serializer="json")


def get_celery_app() -> Celery:
    return celery_app
