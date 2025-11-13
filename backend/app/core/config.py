"""Application configuration powered by Pydantic settings."""

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Centralised strongly-typed runtime configuration."""

    project_name: str = Field(default="robot-ml-web-app")
    api_prefix: str = Field(default="/api")
    environment: str = Field(default="local")

    backend_cors_origins: List[AnyHttpUrl] = Field(default_factory=list)

    database_url: str = Field(
        default="postgresql+asyncpg://robot_ml:robot_ml@localhost:5432/robot_ml"
    )
    alembic_database_url: str | None = Field(default=None)

    redis_url: str = Field(default="redis://localhost:6379/0")

    mqtt_host: str = Field(default="localhost")
    mqtt_port: int = Field(default=1883)
    mqtt_username: str | None = Field(default=None)
    mqtt_password: str | None = Field(default=None)
    mqtt_keepalive_s: int = Field(default=60)
    mqtt_client_id: str = Field(default="robot-ml-web-app-api")

    websocket_heartbeat_interval_s: int = Field(default=30)

    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")

    object_storage_endpoint: str | None = Field(default=None)
    object_storage_bucket: str = Field(default="robot-ml-artifacts")
    object_storage_access_key: str | None = Field(default=None)
    object_storage_secret_key: str | None = Field(default=None)

    vector_store_url: str | None = Field(default=None)
    llm_api_base: str | None = Field(default=None)
    llm_api_key: str | None = Field(default=None)

    jwt_secret_key: str = Field(default="changeme")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60 * 24)

    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=True)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()


settings = get_settings()
