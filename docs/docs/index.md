# Robot AI Web Application

A comprehensive web application for robot control, sensor data visualization, ML dataset management, and RAG-based document Q&A using local LLMs.

## Quick Links

- [Architecture Overview](architecture/overview.md)
- [Data Flow](architecture/data-flow.md)
- [REST API Reference](api/rest-api.md)
- [Deployment Guide](deployment/docker.md)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2.0 |
| Gateway | Go 1.22 + gorilla/websocket + MessagePack |
| Database | PostgreSQL 16 + TimescaleDB + pgvector |
| Message Broker | Redis 7 (Streams) |
| LLM | Ollama + Llama 3 + nomic-embed-text |
| CI/CD | GitHub Actions |
