"""
Configuration management for Robot ML Backend
"""
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "Robot ML Web Application"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql://robot_user:robot_password@localhost:5432/robot_ml_db"
    POSTGRES_USER: str = "robot_user"
    POSTGRES_PASSWORD: str = "robot_password"
    POSTGRES_DB: str = "robot_ml_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    # MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_CLIENT_ID: str = "robot_ml_backend"
    MQTT_KEEPALIVE: int = 60

    # MQTT Topics
    MQTT_TOPIC_CMD_VEL: str = "robot/cmd_vel"
    MQTT_TOPIC_NAV_GOAL: str = "robot/nav/goal"
    MQTT_TOPIC_NAV_CANCEL: str = "robot/nav/cancel"
    MQTT_TOPIC_ROBOT_STATUS: str = "robot/status"
    MQTT_TOPIC_CAMERA_IMAGE: str = "robot/camera/image"
    MQTT_TOPIC_NAV_STATUS: str = "robot/nav/status"

    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 5

    # File Storage
    IMAGE_STORAGE_PATH: str = "/app/data/images"
    DATASET_STORAGE_PATH: str = "/app/data/datasets"
    MODEL_STORAGE_PATH: str = "/app/data/models"

    # Machine Learning
    ML_DEVICE: str = "cpu"  # cuda or cpu
    ML_BATCH_SIZE: int = 32
    ML_NUM_WORKERS: int = 4
    ML_LEARNING_RATE: float = 0.001

    # LLM / RAG
    LLM_PROVIDER: str = "openai"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4"
    RAG_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    RAG_CHUNK_SIZE: int = 1000
    RAG_CHUNK_OVERLAP: int = 200
    RAG_VECTOR_DB_PATH: str = "/app/data/rag/embeddings"

    # Unity Simulator
    UNITY_EXECUTABLE_PATH: str = "/app/unity-simulator/build/RobotSimulator.x86_64"
    UNITY_AUTO_START: bool = False

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Security
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "/app/logs/app.log"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()
