from functools import lru_cache
from typing import List

from pydantic import BaseSettings, Field, AnyHttpUrl


class Settings(BaseSettings):
    api_v1_prefix: str = "/api/v1"
    ws_prefix: str = "/ws"
    project_name: str = "Robot ML Web App"
    environment: str = Field("development", env="APP_ENV")
    backend_cors_origins: List[AnyHttpUrl] = Field(default_factory=list)
    database_url: str = Field("sqlite:///./app.db", env="DATABASE_URL")
    mqtt_broker_url: str = Field("mqtt://localhost:1883", env="MQTT_BROKER_URL")
    mqtt_username: str | None = Field(None, env="MQTT_USERNAME")
    mqtt_password: str | None = Field(None, env="MQTT_PASSWORD")
    media_root: str = Field("/app/data/uploads/media", env="MEDIA_ROOT")
    models_root: str = Field("/app/data/uploads/models", env="MODELS_ROOT")
    telemetry_buffer_size: int = Field(512, env="TELEMETRY_BUFFER_SIZE")
    telemetry_flush_interval_ms: int = Field(500, env="TELEMETRY_FLUSH_INTERVAL_MS")
    llm_provider: str = Field("openai", env="LLM_PROVIDER")
    llm_model: str = Field("gpt-4o", env="LLM_MODEL")
    llm_api_key: str | None = Field(None, env="LLM_API_KEY")
    embedding_model: str = Field("text-embedding-3-large", env="EMBEDDING_MODEL")
    redis_url: str | None = Field(None, env="REDIS_URL")

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
