# ADR-004: Database Selection

## Status
**Accepted**

## Context
Requirements:
- Time-series sensor data storage (high write throughput)
- Vector similarity search for RAG embeddings
- Standard relational data (users, robots, datasets)
- Aggregation queries (time-bucketed sensor stats)

## Decision
**PostgreSQL 16 + TimescaleDB + pgvector**

## Alternatives Considered

| Requirement | PostgreSQL + Extensions | InfluxDB + PostgreSQL + Milvus | MongoDB + dedicated vector DB |
|-------------|:---:|:---:|:---:|
| Single DB simplicity | ★★★★★ | ★★ | ★★ |
| Time-series | ★★★★ (TimescaleDB) | ★★★★★ | ★★★ |
| Vector search | ★★★★ (pgvector HNSW) | ★★★★★ (Milvus) | ★★★ |
| Relational data | ★★★★★ | ★★★★ | ★★★ |
| Operational complexity | ★★★★★ | ★★ | ★★ |

## Rationale
- **Single database**: Reduces operational complexity dramatically
- **TimescaleDB**: Automatic time-based partitioning, `time_bucket` aggregation, compression, retention policies
- **pgvector**: HNSW index for fast approximate nearest neighbor search (768-dim embeddings)
- **Mature ecosystem**: Excellent tooling, monitoring, backup solutions
- **ACID compliance**: Critical for audit logging and data integrity
- Trade-off: Slightly less optimal than dedicated engines, but acceptable for our scale (<100 robots)
