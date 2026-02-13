"""
Robot AI Web Application - Backend Configuration

Uses pydantic-settings to load configuration from environment variables.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # General
    environment: str = "development"
    debug: bool = False

    # Server
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    backend_log_level: str = "info"

    # Database
    database_url: str = "postgresql+asyncpg://robot_app:password@localhost:5432/robot_ai_db"
    db_pool_size: int = 10
    db_max_overflow: int = 20

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # JWT / Auth
    secret_key: str = "change-this-in-production"
    jwt_algorithm: str = "RS256"
    jwt_access_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7
    jwt_private_key_path: str = "/app/keys/private.pem"
    jwt_public_key_path: str = "/app/keys/public.pem"

    # Admin
    admin_email: str = "admin@example.com"
    admin_password: str = "changeme123"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Rate limiting
    rate_limit_per_minute: int = 60

    # Ollama
    ollama_url: str = "http://localhost:11434"
    llm_model: str = "llama3"
    embedding_model: str = "nomic-embed-text"

    # RAG
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 100
    rag_top_k: int = 5

    # Gateway gRPC
    gateway_grpc_host: str = "gateway"
    gateway_grpc_port: int = 50051

    # TimescaleDB retention
    timescaledb_retention_sensor_days: int = 90
    timescaledb_retention_command_days: int = 180

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def jwt_private_key(self) -> str | None:
        path = Path(self.jwt_private_key_path)
        if path.exists():
            return path.read_text()
        return None

    @property
    def jwt_public_key(self) -> str | None:
        path = Path(self.jwt_public_key_path)
        if path.exists():
            return path.read_text()
        return None

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
