# ADR-002: Backend Framework

## Status
**Accepted**

## Context
Backend needs to support:
- REST API for CRUD operations
- Background workers (Redis Streams consumer)
- Integration with Ollama LLM API
- Async database operations (PostgreSQL)
- Data export (CSV, Parquet)

## Decision
**Python 3.12 + FastAPI + SQLAlchemy 2.0 (async)**

## Alternatives Considered

| Criteria | FastAPI | Django | Go (Chi) | Node (NestJS) |
|----------|:-------:|:-----:|:--------:|:-------------:|
| Async support | ★★★★★ | ★★★ | ★★★★★ | ★★★★ |
| ML ecosystem | ★★★★★ | ★★★★ | ★★ | ★★ |
| Auto API docs | ★★★★★ | ★★★ | ★★ | ★★★★ |
| Data science tools | ★★★★★ | ★★★★ | ★★ | ★★ |
| Performance | ★★★★ | ★★★ | ★★★★★ | ★★★★ |

## Rationale
- Native async support with asyncio
- Automatic OpenAPI documentation
- Python has the best ML/data science ecosystem (pandas, PyArrow, scikit-learn)
- Pydantic v2 for fast, validated schemas
- SQLAlchemy 2.0 async mode for non-blocking DB operations
- Easy integration with Ollama HTTP API via httpx
