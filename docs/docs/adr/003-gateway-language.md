# ADR-003: Gateway Language

## Status
**Accepted**

## Context
The gateway handles:
- Hundreds of concurrent WebSocket connections
- High-frequency sensor data relay (20-50 Hz per robot)
- Safety pipeline with microsecond latency requirements
- Robot adapter plugin system

## Decision
**Go 1.22**

## Alternatives Considered

| Criteria | Go | Rust | Node.js | C++ |
|----------|:--:|:----:|:-------:|:---:|
| Concurrency | ★★★★★ | ★★★★ | ★★★ | ★★★★ |
| Memory safety | ★★★★★ | ★★★★★ | ★★★★ | ★★ |
| WebSocket libs | ★★★★★ | ★★★★ | ★★★★★ | ★★★ |
| Build simplicity | ★★★★★ | ★★ | ★★★★★ | ★ |
| DevOps friendliness | ★★★★★ | ★★★ | ★★★★ | ★★ |

## Rationale
- Goroutines: lightweight concurrency model ideal for per-connection goroutines
- gorilla/websocket: battle-tested WebSocket library
- Single binary deployment (distroless Docker image, ~15MB)
- Low memory footprint (~2MB per idle connection)
- Excellent MessagePack support via vmihailenco/msgpack
- Simple plugin pattern via Go interfaces
