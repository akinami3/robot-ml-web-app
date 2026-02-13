# Architecture Overview

## System Architecture

```mermaid
graph TB
    subgraph Browser
        FE[React Frontend]
    end

    subgraph Docker Network
        subgraph "Frontend Network"
            FE -- "REST API" --> BE[FastAPI Backend]
            FE -- "WebSocket" --> GW[Go Gateway]
        end

        subgraph "Backend Network"
            BE -- "SQL" --> DB[(PostgreSQL<br/>TimescaleDB + pgvector)]
            BE -- "HTTP" --> OL[Ollama LLM]
            BE -- "XREADGROUP" --> RD[(Redis Streams)]
            GW -- "XADD" --> RD
            GW -- "gRPC" --> BE
        end
    end

    subgraph Robot
        RA[Robot Adapter] -- "vendor protocol" --> HW[Hardware]
    end

    GW -- "Adapter Interface" --> RA

    style FE fill:#61dafb,color:#000
    style BE fill:#009688,color:#fff
    style GW fill:#00ADD8,color:#fff
    style DB fill:#336791,color:#fff
    style RD fill:#DC382D,color:#fff
    style OL fill:#FF6F00,color:#fff
```

## Component Responsibilities

### Frontend (React + TypeScript)
- Real-time robot control via WebSocket (joystick, keyboard)
- Sensor data visualization (LiDAR canvas, IMU charts, odometry, battery)
- Dataset management UI with recording controls
- RAG chat interface with SSE streaming
- JWT authentication with role-based UI

### Gateway (Go)
- WebSocket server for real-time bidirectional communication
- MessagePack + JSON protocol with auto-detection
- Robot adapter plugin system (connect any robot via interface)
- Safety pipeline: E-Stop → Operation Lock → Velocity Limiter → Timeout Watchdog
- Redis Streams publisher for sensor data and commands

### Backend (FastAPI)
- REST API for CRUD operations (users, robots, datasets, recordings, RAG)
- Redis Streams consumer worker for recording sensor data
- RAG pipeline: document ingestion → chunking → embedding → pgvector similarity search → LLM generation
- JWT RS256 auth with RBAC (admin/operator/viewer)
- Alembic database migrations

### Database (PostgreSQL + TimescaleDB + pgvector)
- TimescaleDB hypertables for time-series sensor data
- pgvector HNSW index for embedding similarity search
- UUID primary keys, proper indexing, audit logging

## Clean Architecture

```mermaid
graph LR
    subgraph "API Layer"
        EP[Endpoints]
        SC[Schemas]
        DP[Dependencies]
    end

    subgraph "Domain Layer"
        EN[Entities]
        RI[Repository Interfaces]
        DS[Domain Services]
    end

    subgraph "Infrastructure Layer"
        DB[Database / ORM]
        RE[Redis Client]
        LM[LLM Client]
        GR[gRPC Client]
    end

    EP --> DS
    EP --> DP
    DP --> RI
    DS --> RI
    DB -.-> RI
    RE -.-> DS
    LM -.-> DS

    style EN fill:#ffd54f,color:#000
    style RI fill:#ffd54f,color:#000
    style DS fill:#ffd54f,color:#000
```

The backend follows **Clean Architecture** (Hexagonal):

- **Domain Layer**: Pure Python entities, repository interfaces (ABCs), domain services. No framework dependencies.
- **Infrastructure Layer**: Concrete implementations (SQLAlchemy repos, Ollama client, Redis worker).
- **API Layer**: FastAPI endpoints, Pydantic schemas, dependency injection.

## Robot Adapter Pattern

```mermaid
classDiagram
    class RobotAdapter {
        <<interface>>
        +Connect() error
        +Disconnect() error
        +IsConnected() bool
        +SendCommand(cmd) error
        +SensorDataChannel() chan
        +GetCapabilities() Capabilities
        +EmergencyStop() error
    }

    class MockAdapter {
        +simulateOdometry()
        +simulateLiDAR()
        +simulateIMU()
        +simulateBattery()
    }

    class ROSAdapter {
        +rosbridge connection
        +topic subscriptions
    }

    class CustomAdapter {
        +vendor SDK
    }

    RobotAdapter <|.. MockAdapter
    RobotAdapter <|.. ROSAdapter
    RobotAdapter <|.. CustomAdapter

    class AdapterRegistry {
        +CreateAdapter(id, type, config)
        +GetAdapter(id)
        +GetAllActive()
        +RemoveAdapter(id)
    }

    AdapterRegistry --> RobotAdapter
```

New robot types are supported by implementing the `RobotAdapter` interface and registering in the factory.
