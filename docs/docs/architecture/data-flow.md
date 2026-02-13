# Data Flow

## Real-Time Control Flow

```mermaid
sequenceDiagram
    participant U as User Browser
    participant GW as Gateway (Go)
    participant SA as Safety Pipeline
    participant RA as Robot Adapter
    participant RD as Redis Streams
    participant BW as Backend Worker
    participant DB as PostgreSQL

    U->>GW: WebSocket: velocity_cmd
    GW->>SA: Check E-Stop
    SA->>SA: Check Operation Lock
    SA->>SA: Velocity Limiter (clamp)
    SA-->>GW: Approved command
    GW->>RA: SendCommand()
    GW->>RD: XADD robot:commands

    loop Sensor Data (20-50 Hz)
        RA-->>GW: SensorDataChannel
        GW-->>U: WebSocket: sensor_data
        GW->>RD: XADD robot:sensor_data
    end

    BW->>RD: XREADGROUP (consumer group)
    BW->>BW: Filter by active recordings
    BW->>DB: Bulk INSERT sensor_data
```

## Recording Pipeline

```mermaid
sequenceDiagram
    participant U as User
    participant API as Backend API
    participant DB as PostgreSQL
    participant RD as Redis Streams
    participant BW as Recording Worker

    U->>API: POST /recordings/start
    API->>DB: Create RecordingSession (active)
    API-->>U: 201 Created

    Note over BW: Worker runs continuously

    loop Every batch
        BW->>RD: XREADGROUP robot:sensor_data
        BW->>DB: Get active recording sessions
        BW->>BW: Filter: sensor_type match? frequency limit?
        BW->>DB: Bulk INSERT filtered sensor_data
        BW->>DB: UPDATE recording stats (count, duration)
    end

    U->>API: POST /recordings/{id}/stop
    API->>DB: Set status=completed, end_time
    API-->>U: 200 OK
```

### Recording Configuration

Users configure recording at the **sensor-type level**:

```json
{
  "sensor_types": ["lidar", "imu", "odometry"],
  "max_frequency_hz": 10,
  "exclude_sensor_types": ["camera"]
}
```

The worker respects:

- **Sensor type filtering**: Only records configured sensor types
- **Frequency limiting**: Drops samples exceeding `max_frequency_hz`
- **Per-session isolation**: Multiple users can record different sensor combinations simultaneously

## RAG Query Flow

```mermaid
sequenceDiagram
    participant U as User
    participant API as Backend API
    participant ES as Embedding Service
    participant PG as pgvector (PostgreSQL)
    participant LM as Ollama (Llama 3)

    U->>API: POST /rag/query {query, top_k}
    API->>ES: Embed query text
    ES->>LM: POST /api/embeddings (nomic-embed-text)
    LM-->>ES: vector[768]
    ES-->>API: query_embedding

    API->>PG: SELECT ... ORDER BY embedding <=> query_embedding LIMIT top_k
    PG-->>API: relevant chunks

    API->>API: Assemble context prompt
    API->>LM: POST /api/chat (Llama 3, stream=true)

    loop SSE tokens
        LM-->>API: token
        API-->>U: SSE: data: {token}
    end

    API-->>U: SSE: data: [DONE]
```

### Document Ingestion

```mermaid
flowchart LR
    A[Upload PDF/TXT/MD] --> B[Extract Text]
    B --> C[TextSplitter<br/>paragraph-aware]
    C --> D[Chunks<br/>~500 chars]
    D --> E[Embed each chunk<br/>nomic-embed-text]
    E --> F[Store in pgvector<br/>HNSW index]

    style F fill:#336791,color:#fff
```

## WebSocket Message Flow

```mermaid
flowchart LR
    subgraph Client
        C[Browser]
    end

    subgraph Gateway
        H[Handler]
        HB[Hub]
        P[Publisher]
    end

    C -- "auth / velocity_cmd / estop / nav_goal" --> H
    H -- "broadcast" --> HB
    HB -- "sensor_data / robot_status" --> C
    H -- "XADD" --> P
    P --> R[(Redis)]
```

### Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `auth` | Client → Gateway | JWT token authentication |
| `velocity_cmd` | Client → Gateway | Velocity command (linear_x, linear_y, angular_z) |
| `estop` | Client → Gateway | Emergency stop activate/release |
| `nav_goal` | Client → Gateway | Navigation goal (x, y, theta) |
| `sensor_data` | Gateway → Client | Real-time sensor data |
| `robot_status` | Gateway → Client | Robot state updates |
| `error` | Gateway → Client | Error messages |
| `ping` / `pong` | Bidirectional | Keepalive |
