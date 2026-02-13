# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project structure
- Frontend (React + TypeScript + Vite)
- Backend (FastAPI + SQLAlchemy + TimescaleDB + pgvector)
- Gateway (Go + gorilla/websocket)
- Docker Compose orchestration (dev/prod)
- WebSocket real-time communication (Frontend ↔ Gateway)
- Robot adapter plugin system (Mock, ROS2, MQTT, gRPC)
- Sensor data recording with user-configurable topics
- ML dataset export (CSV/Parquet)
- RAG system with Ollama (Llama 3) + pgvector
- Safety features (E-Stop, velocity limiter, operation timeout, operation lock)
- Audit logging (immutable)
- JWT authentication (RS256) with RBAC
- GitHub Actions CI/CD pipelines
- MkDocs (Material) design documentation
- OSS license management
