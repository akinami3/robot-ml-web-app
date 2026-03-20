# Robot AI Web Application — Mermaid 図表集

> クラス図、シーケンス図、ER図、アーキテクチャ図をMermaidで表現

---

## 目次

1. [システムアーキテクチャ全体図](#1-システムアーキテクチャ全体図)
2. [ER図 (データベース)](#2-er図-データベース)
3. [バックエンド クラス図](#3-バックエンド-クラス図)
4. [ゲートウェイ クラス図](#4-ゲートウェイ-クラス図)
5. [フロントエンド クラス図](#5-フロントエンド-クラス図)
6. [シーケンス図 — 認証フロー](#6-シーケンス図--認証フロー)
7. [シーケンス図 — ロボット操作](#7-シーケンス図--ロボット操作)
8. [シーケンス図 — センサーデータ配信](#8-シーケンス図--センサーデータ配信)
9. [シーケンス図 — RAG質問応答](#9-シーケンス図--rag質問応答)
10. [シーケンス図 — 緊急停止 (E-Stop)](#10-シーケンス図--緊急停止-e-stop)
11. [シーケンス図 — データ記録](#11-シーケンス図--データ記録)
12. [状態遷移図 — ロボット状態](#12-状態遷移図--ロボット状態)
13. [状態遷移図 — データセット状態](#13-状態遷移図--データセット状態)
14. [依存性注入フロー図](#14-依存性注入フロー図)
15. [Docker ネットワーク構成図](#15-docker-ネットワーク構成図)
16. [CI/CD パイプライン図](#16-cicd-パイプライン図)

---

## 1. システムアーキテクチャ全体図

```mermaid
graph TB
    subgraph Browser["ブラウザ (React + TypeScript)"]
        UI[UI Components]
        Zustand[Zustand Store]
        Axios[Axios API Client]
        WS_Client[WebSocket Client]
    end

    subgraph Gateway["Gateway (Go)"]
        WSServer[WebSocket Server]
        Handler[Message Handler]
        Hub[Client Hub]
        Safety[Safety Module]
        Adapter[Robot Adapter]
        Codec[Protocol Codec]
    end

    subgraph Backend["Backend (FastAPI / Python)"]
        API[REST API]
        DI[Dependency Injection]
        Domain[Domain Layer]
        Infra[Infrastructure Layer]
        Worker[Recording Worker]
    end

    subgraph DataStores["データストア"]
        PG[(PostgreSQL<br/>+ TimescaleDB<br/>+ pgvector)]
        Redis[(Redis 7<br/>Streams + Cache)]
        Ollama[Ollama<br/>Llama3 + nomic-embed-text]
    end

    UI --> Axios
    UI --> WS_Client
    Axios -->|REST API| API
    WS_Client -->|WebSocket| WSServer

    WSServer --> Hub
    Hub --> Handler
    Handler --> Safety
    Handler --> Adapter
    Handler -->|Publish| Redis

    API --> DI --> Domain --> Infra
    Infra --> PG
    Infra --> Redis
    Infra --> Ollama

    Worker -->|Subscribe| Redis
    Worker --> PG

    Adapter -->|Sensor Data| Hub
    Hub -->|Broadcast| WS_Client

    style Browser fill:#dbeafe,stroke:#3b82f6
    style Gateway fill:#dcfce7,stroke:#22c55e
    style Backend fill:#fef3c7,stroke:#f59e0b
    style DataStores fill:#f3e8ff,stroke:#a855f7
```

---

## 2. ER図 (データベース)

```mermaid
erDiagram
    users {
        UUID id PK
        VARCHAR username UK
        VARCHAR email UK
        VARCHAR hashed_password
        ENUM role "admin|operator|viewer"
        BOOLEAN is_active
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    robots {
        UUID id PK
        VARCHAR name UK
        VARCHAR adapter_type
        ENUM state "disconnected|connecting|idle|moving|error|emergency_stopped"
        ARRAY capabilities
        JSONB connection_params
        FLOAT battery_level
        TIMESTAMPTZ last_seen
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    sensor_data {
        UUID id PK
        TIMESTAMPTZ timestamp PK "TimescaleDB hypertable"
        UUID robot_id FK
        ENUM sensor_type "lidar|camera|imu|odometry|battery|gps|point_cloud|joint_state"
        JSONB data
        UUID session_id FK "nullable"
        INTEGER sequence_number
    }

    datasets {
        UUID id PK
        VARCHAR name
        TEXT description
        UUID owner_id FK
        ENUM status "creating|ready|exporting|archived|error"
        ARRAY sensor_types
        ARRAY robot_ids
        TIMESTAMPTZ start_time
        TIMESTAMPTZ end_time
        INTEGER record_count
        INTEGER size_bytes
        ARRAY tags
        JSONB metadata
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    rag_documents {
        UUID id PK
        VARCHAR title
        TEXT content
        VARCHAR source
        UUID owner_id FK
        VARCHAR file_type
        INTEGER file_size
        INTEGER chunk_count
        JSONB metadata
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }

    document_chunks {
        UUID id PK
        UUID document_id FK
        TEXT content
        VECTOR_768 embedding "pgvector HNSW index"
        INTEGER chunk_index
        INTEGER token_count
        JSONB metadata
        TIMESTAMPTZ created_at
    }

    recording_sessions {
        UUID id PK
        UUID robot_id FK
        UUID user_id FK
        JSONB config
        BOOLEAN is_active
        INTEGER record_count
        INTEGER size_bytes
        TIMESTAMPTZ started_at
        TIMESTAMPTZ stopped_at
        UUID dataset_id FK "nullable"
    }

    audit_logs {
        UUID id PK
        UUID user_id FK
        ENUM action "login|logout|robot_connect|estop_activate|..."
        VARCHAR resource_type
        VARCHAR resource_id
        JSONB details
        VARCHAR ip_address
        VARCHAR user_agent
        TIMESTAMPTZ timestamp
    }

    users ||--o{ datasets : "owns"
    users ||--o{ rag_documents : "uploads"
    users ||--o{ recording_sessions : "starts"
    users ||--o{ audit_logs : "performs"
    robots ||--o{ sensor_data : "generates"
    rag_documents ||--o{ document_chunks : "contains"
    recording_sessions ||--o{ sensor_data : "records"
    datasets ||--o{ recording_sessions : "linked to"
```

---

## 3. バックエンド クラス図

### 3.1 ドメインエンティティ

```mermaid
classDiagram
    class User {
        +UUID id
        +str username
        +str email
        +str hashed_password
        +UserRole role
        +bool is_active
        +datetime created_at
        +datetime updated_at
        +can_control_robot() bool
        +can_manage_users() bool
        +can_view_data() bool
    }

    class UserRole {
        <<enumeration>>
        ADMIN
        OPERATOR
        VIEWER
    }

    class Robot {
        +UUID id
        +str name
        +str adapter_type
        +RobotState state
        +list~RobotCapability~ capabilities
        +dict connection_params
        +float battery_level
        +datetime last_seen
        +datetime created_at
        +datetime updated_at
        +is_connected() bool
        +is_emergency_stopped() bool
    }

    class RobotState {
        <<enumeration>>
        DISCONNECTED
        CONNECTING
        IDLE
        MOVING
        ERROR
        EMERGENCY_STOPPED
    }

    class RobotCapability {
        <<enumeration>>
        VELOCITY_CONTROL
        NAVIGATION
        LIDAR
        CAMERA
        IMU
        ODOMETRY
        BATTERY_MONITOR
        GPS
        ARM_CONTROL
    }

    class SensorData {
        +UUID id
        +UUID robot_id
        +SensorType sensor_type
        +dict data
        +datetime timestamp
        +UUID session_id
        +int sequence_number
        +is_image_type() bool
        +is_time_series() bool
    }

    class SensorType {
        <<enumeration>>
        LIDAR
        CAMERA
        IMU
        ODOMETRY
        BATTERY
        GPS
        POINT_CLOUD
        JOINT_STATE
    }

    class Dataset {
        +UUID id
        +str name
        +str description
        +UUID owner_id
        +DatasetStatus status
        +list sensor_types
        +list robot_ids
        +datetime start_time
        +datetime end_time
        +int record_count
        +int size_bytes
        +list tags
        +dict metadata
        +is_exportable() bool
    }

    class DatasetStatus {
        <<enumeration>>
        CREATING
        READY
        EXPORTING
        ARCHIVED
        ERROR
    }

    class RAGDocument {
        +UUID id
        +str title
        +str content
        +str source
        +UUID owner_id
        +str file_type
        +int file_size
        +int chunk_count
        +dict metadata
        +datetime created_at
    }

    class DocumentChunk {
        +UUID id
        +UUID document_id
        +str content
        +list~float~ embedding
        +int chunk_index
        +int token_count
        +dict metadata
        +datetime created_at
    }

    class RecordingSession {
        +UUID id
        +UUID robot_id
        +UUID user_id
        +RecordingConfig config
        +bool is_active
        +int record_count
        +int size_bytes
        +datetime started_at
        +datetime stopped_at
        +UUID dataset_id
        +stop() void
        +duration_seconds() float
    }

    class RecordingConfig {
        +list~SensorType~ sensor_types
        +dict max_frequency_hz
        +bool enabled
        +is_sensor_enabled(SensorType) bool
        +get_max_frequency(SensorType) float
    }

    class AuditLog {
        +UUID id
        +UUID user_id
        +AuditAction action
        +str resource_type
        +str resource_id
        +dict details
        +str ip_address
        +str user_agent
        +datetime timestamp
    }

    class AuditAction {
        <<enumeration>>
        LOGIN
        LOGOUT
        TOKEN_REFRESH
        ROBOT_CONNECT
        ROBOT_DISCONNECT
        VELOCITY_COMMAND
        ESTOP_ACTIVATE
        ESTOP_RELEASE
        RECORDING_START
        RECORDING_STOP
        DATASET_CREATE
        DOCUMENT_UPLOAD
        RAG_QUERY
        USER_CREATE
        USER_UPDATE
    }

    User --> UserRole
    Robot --> RobotState
    Robot --> RobotCapability
    SensorData --> SensorType
    Dataset --> DatasetStatus
    RAGDocument "1" --> "*" DocumentChunk
    RecordingSession --> RecordingConfig
    RecordingSession --> SensorData : records
    AuditLog --> AuditAction
```

### 3.2 リポジトリ層 (抽象 + 実装)

```mermaid
classDiagram
    class BaseRepository~T~ {
        <<abstract>>
        +get_by_id(UUID) T
        +create(T) T
        +update(T) T
        +delete(UUID) bool
        +list_all() list~T~
    }

    class UserRepository {
        <<abstract>>
        +get_by_email(str) User
        +get_by_username(str) User
    }

    class RobotRepository {
        <<abstract>>
        +get_by_name(str) Robot
        +update_state(UUID, RobotState) void
    }

    class SensorDataRepository {
        <<abstract>>
        +get_by_robot(UUID, SensorType) list
        +get_latest(UUID, SensorType) SensorData
        +get_aggregated(UUID, str, str) list
    }

    class DatasetRepository {
        <<abstract>>
        +get_by_owner(UUID) list
        +update_status(UUID, DatasetStatus) void
        +update_stats(UUID, int, int) void
    }

    class RAGRepository {
        <<abstract>>
        +get_by_owner(UUID) list
        +create_chunk(DocumentChunk) DocumentChunk
        +create_chunks_bulk(list) int
        +search_similar_chunks(list, int, float) list
        +delete_chunks_by_document(UUID) int
    }

    class RecordingRepository {
        <<abstract>>
        +get_active_by_robot(UUID) RecordingSession
    }

    class AuditRepository {
        <<abstract>>
        +get_by_user(UUID) list
        +get_by_action(AuditAction) list
    }

    class SQLAlchemyUserRepository {
        -AsyncSession _session
    }
    class SQLAlchemyRobotRepository {
        -AsyncSession _session
    }
    class SQLAlchemySensorDataRepository {
        -AsyncSession _session
    }
    class SQLAlchemyDatasetRepository {
        -AsyncSession _session
    }
    class SQLAlchemyRAGRepository {
        -AsyncSession _session
    }
    class SQLAlchemyRecordingRepository {
        -AsyncSession _session
    }
    class SQLAlchemyAuditRepository {
        -AsyncSession _session
    }

    BaseRepository <|-- UserRepository
    BaseRepository <|-- RobotRepository
    BaseRepository <|-- SensorDataRepository
    BaseRepository <|-- DatasetRepository
    BaseRepository <|-- RAGRepository
    BaseRepository <|-- RecordingRepository
    BaseRepository <|-- AuditRepository

    UserRepository <|.. SQLAlchemyUserRepository
    RobotRepository <|.. SQLAlchemyRobotRepository
    SensorDataRepository <|.. SQLAlchemySensorDataRepository
    DatasetRepository <|.. SQLAlchemyDatasetRepository
    RAGRepository <|.. SQLAlchemyRAGRepository
    RecordingRepository <|.. SQLAlchemyRecordingRepository
    AuditRepository <|.. SQLAlchemyAuditRepository
```

### 3.3 サービス層

```mermaid
classDiagram
    class DatasetService {
        -DatasetRepository _dataset_repo
        -SensorDataRepository _sensor_data_repo
        +create_dataset(name, desc, owner_id, ...) Dataset
        +get_user_datasets(owner_id) list~Dataset~
        +get_dataset(dataset_id) Dataset
        +delete_dataset(dataset_id) bool
        +export_dataset(dataset_id, format) str
    }

    class RAGService {
        -RAGRepository _repo
        -EmbeddingProvider _embedder
        -LLMProvider _llm
        -TextSplitter _splitter
        +ingest_document(title, content, ...) RAGDocument
        +query(question, top_k) dict
        +query_stream(question, top_k) AsyncIterator
        +delete_document(doc_id) bool
    }

    class RecordingService {
        -RecordingRepository _recording_repo
        -SensorDataRepository _sensor_repo
        +start_recording(robot_id, user_id, config) RecordingSession
        +stop_recording(session_id) RecordingSession
        +should_record(robot_id, sensor_type) RecordingSession
        +record_data(session, sensor_data) void
    }

    class AuditService {
        -AuditRepository _repo
        +log(user_id, action, ...) AuditLog
        +get_user_logs(user_id) list~AuditLog~
    }

    class TextSplitter {
        +int chunk_size
        +int overlap
        +split(text) list~str~
    }

    class EmbeddingProvider {
        <<protocol>>
        +embed(text) list~float~
        +embed_batch(texts) list~list~float~~
    }

    class LLMProvider {
        <<protocol>>
        +generate(prompt, context) str
        +generate_stream(prompt, context) AsyncIterator
    }

    class EmbeddingService {
        -AsyncClient _client
        +str model
        +embed(text) list~float~
        +embed_batch(texts) list~list~float~~
    }

    class OllamaClient {
        -AsyncClient _client
        +str model
        +generate(prompt, context) str
        +generate_stream(prompt, context) AsyncIterator
        +health_check() bool
        +list_models() list
    }

    RAGService --> RAGRepository
    RAGService --> EmbeddingProvider
    RAGService --> LLMProvider
    RAGService --> TextSplitter
    DatasetService --> DatasetRepository
    DatasetService --> SensorDataRepository
    RecordingService --> RecordingRepository
    RecordingService --> SensorDataRepository
    AuditService --> AuditRepository

    EmbeddingProvider <|.. EmbeddingService
    LLMProvider <|.. OllamaClient
```


---

## 4. ゲートウェイ クラス図

### 4.1 サーバー・メッセージ処理

```mermaid
classDiagram
    class Handler {
        -Hub hub
        -Registry registry
        -EStopManager estop
        -VelocityLimiter velocityLimiter
        -TimeoutWatchdog watchdog
        -OperationLock opLock
        -Codec codec
        -RedisPublisher redisPublisher
        +HandleWebSocket(w, r)
        +HandleHealth(w, r)
        +HandleMessage(Client, Message)
    }

    class Hub {
        -map clients
        -chan register
        -chan unregister
        -chan broadcast
        -Codec codec
        +Run()
        +BroadcastToRobot(robotID, data)
        +BroadcastToAll(data)
        +GetClient(clientID) Client
        +ClientCount() int
    }

    class Client {
        +string ID
        +string UserID
        +WSConn Conn
        +chan Send
        +Hub Hub
        +bool Authenticated
        +map Subscriptions
        +time ConnectedAt
    }

    class WSConn {
        <<interface>>
        +WriteMessage(int, bytes) error
        +ReadMessage() int, bytes, error
        +Close() error
        +SetReadDeadline(Time) error
        +SetWriteDeadline(Time) error
        +SetPongHandler(func) error
    }

    class BroadcastMessage {
        +string RobotID
        +bytes Data
    }

    class RedisPublisher {
        <<interface>>
        +PublishSensorData(ctx, robotID, SensorData) error
        +PublishCommand(ctx, robotID, Command) error
    }

    class RedisPublisherImpl {
        -redis.Client client
        +PublishSensorData(ctx, robotID, SensorData) error
        +PublishCommand(ctx, robotID, Command) error
    }

    Handler --> Hub
    Handler --> RedisPublisher
    Hub --> Client
    Hub --> BroadcastMessage
    Client --> WSConn
    RedisPublisher <|.. RedisPublisherImpl
```

### 4.2 アダプタパターン

```mermaid
classDiagram
    class RobotAdapter {
        <<interface>>
        +Name() string
        +Connect(ctx, config) error
        +Disconnect(ctx) error
        +IsConnected() bool
        +SendCommand(ctx, Command) error
        +SensorDataChannel() chan SensorData
        +GetCapabilities() Capabilities
        +EmergencyStop(ctx) error
    }

    class AdapterSensorData {
        +string RobotID
        +string Topic
        +string DataType
        +string FrameID
        +int64 Timestamp
        +map Data
    }

    class Command {
        +string RobotID
        +string Type
        +map Payload
        +int64 Timestamp
    }

    class Capabilities {
        +bool SupportsVelocityControl
        +bool SupportsNavigation
        +bool SupportsEStop
        +list SensorTopics
        +float64 MaxLinearVelocity
        +float64 MaxAngularVelocity
    }

    class Registry {
        -map factories
        -map adapters
        -RWMutex mu
        +RegisterFactory(name, factory)
        +Create(name, robotID, config) RobotAdapter
        +GetAdapter(robotID) RobotAdapter
        +GetAllActive() map
        +RemoveAdapter(robotID)
    }

    class AdapterFactory {
        <<function>>
        +(config, logger) RobotAdapter, error
    }

    class MockAdapter {
        -string robotID
        -chan sensorCh
        -bool connected
        -float64 posX
        -float64 posY
        -float64 theta
        +Name() string
        +Connect(ctx, config) error
        +Disconnect(ctx) error
        +SendCommand(ctx, Command) error
        +SensorDataChannel() chan
        +EmergencyStop(ctx) error
        -startSensorSimulation()
        -simulateLiDAR() list
    }

    RobotAdapter <|.. MockAdapter
    Registry --> AdapterFactory
    Registry --> RobotAdapter
    RobotAdapter --> AdapterSensorData
    RobotAdapter --> Command
    RobotAdapter --> Capabilities
```

### 4.3 安全機能

```mermaid
classDiagram
    class EStopManager {
        -RWMutex mu
        -map~string,bool~ active
        -Registry registry
        +Activate(ctx, robotID, userID, reason) error
        +ActivateAll(ctx, userID, reason) int, list
        +Release(robotID, userID)
        +IsActive(robotID) bool
    }

    class VelocityLimiter {
        -float64 maxLinearVel
        -float64 maxAngularVel
        +Limit(VelocityInput) LimitResult
    }

    class VelocityInput {
        +float64 LinearX
        +float64 LinearY
        +float64 AngularZ
    }

    class LimitResult {
        +float64 LinearX
        +float64 LinearY
        +float64 AngularZ
        +bool Clamped
    }

    class TimeoutWatchdog {
        -RWMutex mu
        -map lastCommand
        -Duration timeout
        -Registry registry
        -func onTimeout
        +RecordCommand(robotID)
        +RemoveRobot(robotID)
        +Start(ctx)
        +Stop()
        +SetTimeoutCallback(func)
        -run(ctx)
        -checkTimeouts(ctx, Time)
    }

    class OperationLock {
        -RWMutex mu
        -map~string,LockInfo~ locks
        -Duration timeout
        +Acquire(robotID, userID) LockInfo, error
        +Release(robotID, userID) error
        +HasLock(robotID, userID) bool
        +GetLockInfo(robotID) LockInfo
        +StartCleanup(done chan)
        -cleanupExpired()
    }

    class LockInfo {
        +string RobotID
        +string UserID
        +Time AcquiredAt
        +Time ExpiresAt
    }

    VelocityLimiter --> VelocityInput
    VelocityLimiter --> LimitResult
    OperationLock --> LockInfo
    EStopManager --> Registry
    TimeoutWatchdog --> Registry
```

### 4.4 プロトコル

```mermaid
classDiagram
    class Message {
        +MessageType Type
        +string Topic
        +string RobotID
        +string UserID
        +int64 Timestamp
        +map Payload
        +string Error
    }

    class MessageType {
        <<enumeration>>
        auth
        velocity_cmd
        nav_goal
        nav_cancel
        estop
        op_lock
        op_unlock
        ping
        sensor_data
        robot_status
        cmd_ack
        lock_status
        conn_status
        error
        pong
        safety_alert
    }

    class VelocityPayload {
        +float64 LinearX
        +float64 LinearY
        +float64 AngularZ
    }

    class NavigationGoalPayload {
        +float64 X
        +float64 Y
        +float64 Z
        +float64 OrientationW
        +string FrameID
        +float64 TolerancePosition
        +float64 ToleranceOrientation
    }

    class EStopPayload {
        +bool Activate
        +string Reason
    }

    class Codec {
        +Encode(Message) bytes, error
        +Decode(bytes) Message, error
    }

    Message --> MessageType
    Message ..> VelocityPayload
    Message ..> NavigationGoalPayload
    Message ..> EStopPayload
    Codec --> Message
```

---

## 5. フロントエンド クラス図

```mermaid
classDiagram
    class AuthStore {
        +string accessToken
        +string refreshToken
        +User user
        +bool isAuthenticated
        +setTokens(AuthTokens)
        +setUser(User)
        +logout()
        +hasRole(...UserRole) bool
        +canControlRobot() bool
    }

    class RobotStore {
        +string selectedRobotId
        +map sensorData
        +bool isEstopped
        +selectRobot(id)
        +updateSensor(type, data)
        +setEstop(active)
    }

    class ApiClient {
        +authApi: AuthApi
        +robotApi: RobotApi
        +sensorApi: SensorApi
        +datasetApi: DatasetApi
        +recordingApi: RecordingApi
        +ragApi: RagApi
    }

    class AuthApi {
        +login(username, password) AuthTokens
        +register(data) User
        +me() User
    }

    class RobotApi {
        +list() Robot[]
        +get(id) Robot
        +create(data) Robot
        +update(id, data) Robot
        +delete(id) void
    }

    class SensorApi {
        +query(params) SensorData[]
        +latest(robot_id, type) SensorData
        +types() SensorType[]
    }

    class DatasetApi {
        +list() Dataset[]
        +get(id) Dataset
        +create(data) Dataset
        +export(id, format) void
        +delete(id) void
    }

    class RecordingApi {
        +list() RecordingSession[]
        +get(id) RecordingSession
        +start(data) RecordingSession
        +stop(id) RecordingSession
    }

    class RagApi {
        +uploadDocument(file) RAGDocument
        +listDocuments() RAGDocument[]
        +deleteDocument(id) void
        +query(question, top_k) RAGQueryResult
    }

    class useWebSocket {
        +bool isConnected
        +sendCommand(type, payload)
        -connect()
        -reconnect()
    }

    class useKeyboardControl {
        +sendVelocity(linear, angular)
        -handleKeyDown(event)
        -handleKeyUp(event)
    }

    ApiClient --> AuthApi
    ApiClient --> RobotApi
    ApiClient --> SensorApi
    ApiClient --> DatasetApi
    ApiClient --> RecordingApi
    ApiClient --> RagApi
```

### 5.1 ページコンポーネント構成

```mermaid
classDiagram
    class App {
        +Routes
        +ProtectedRoute
    }

    class AppLayout {
        +Sidebar
        +StatusBar
        +Outlet
    }

    class LoginPage {
        -email: string
        -password: string
        -loading: bool
        +handleLogin()
    }

    class SignupPage {
        -username: string
        -email: string
        -password: string
        +handleSignup()
    }

    class DashboardPage {
        -robots: Robot[]
        +RobotCards
        +SystemStatus
    }

    class ManualControlPage {
        +JoystickController
        +EStopButton
        +SensorPanels
    }

    class NavigationPage {
        +GoalInput
        +MapView
    }

    class SensorViewPage {
        +LiDARViewer
        +IMUChart
        +OdometryDisplay
        +BatteryGauge
    }

    class DataManagementPage {
        +DatasetList
        +RecordingControls
    }

    class RAGChatPage {
        +DocumentUpload
        +ChatMessages
        +QueryInput
    }

    class SettingsPage {
        +UserProfile
        +SystemSettings
    }

    App --> AppLayout
    App --> LoginPage
    App --> SignupPage
    AppLayout --> DashboardPage
    AppLayout --> ManualControlPage
    AppLayout --> NavigationPage
    AppLayout --> SensorViewPage
    AppLayout --> DataManagementPage
    AppLayout --> RAGChatPage
    AppLayout --> SettingsPage
```

### 5.2 センサーコンポーネント

```mermaid
classDiagram
    class LiDARViewer {
        -canvasRef: HTMLCanvasElement
        -ranges: number[]
        +draw(ranges)
        -drawGrid()
        -drawRays()
    }

    class IMUChart {
        -data: IMUData[]
        +LineChart
        +accelX, accelY, accelZ
        +gyroX, gyroY, gyroZ
    }

    class OdometryDisplay {
        -x: number
        -y: number
        -theta: number
        +SVG compass
        +position text
    }

    class BatteryGauge {
        -percentage: number
        -voltage: number
        -status: string
        +colorByLevel()
    }

    class JoystickController {
        -nippleManager
        +onMove(linear, angular)
        +onEnd()
    }

    class EStopButton {
        -isEstopped: bool
        +onClick()
        +pulse animation
    }
```


---

## 6. シーケンス図 — 認証フロー

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant Browser as ブラウザ (React)
    participant Store as AuthStore (Zustand)
    participant Axios as Axios Interceptor
    participant API as Backend API (FastAPI)
    participant Security as Security Module
    participant DB as PostgreSQL

    Note over User, DB: ログインフロー

    User->>Browser: メール・パスワード入力
    Browser->>Axios: POST /api/v1/auth/login
    Axios->>API: リクエスト送信
    API->>DB: ユーザー検索 (email)
    DB-->>API: UserModel
    API->>Security: verify_password(plain, hashed)
    Security-->>API: true
    API->>Security: create_tokens(user_id, role)
    Security-->>API: {access_token, refresh_token}
    API-->>Axios: 200 {access_token, refresh_token}
    Axios-->>Browser: レスポンス
    Browser->>Store: setTokens(tokens)
    Store->>Store: localStorage に保存 (persist)
    Browser->>Axios: GET /api/v1/auth/me
    Axios->>Axios: Authorization: Bearer <token> を自動付与
    Axios->>API: リクエスト送信
    API->>Security: decode_token(token)
    Security-->>API: payload {sub, role}
    API->>DB: get_by_id(user_id)
    DB-->>API: User
    API-->>Browser: 200 User情報
    Browser->>Store: setUser(user)
    Browser->>User: ダッシュボードへ遷移

    Note over User, DB: トークン自動更新フロー

    Browser->>Axios: GET /api/v1/robots
    Axios->>API: Authorization: Bearer <expired_token>
    API-->>Axios: 401 Unauthorized
    Axios->>Axios: interceptor: 401検出
    Axios->>API: POST /api/v1/auth/refresh {refresh_token}
    API->>Security: decode_token(refresh_token)
    Security-->>API: payload (type=refresh)
    API->>Security: create_tokens(user_id, role)
    Security-->>API: 新しい tokens
    API-->>Axios: 200 {new access_token, new refresh_token}
    Axios->>Store: setTokens(newTokens)
    Axios->>API: GET /api/v1/robots (新しいtoken)
    API-->>Axios: 200 Robot[]
    Axios-->>Browser: レスポンス
```

---

## 7. シーケンス図 — ロボット操作

```mermaid
sequenceDiagram
    actor Operator as オペレーター
    participant Browser as ブラウザ
    participant WS as WebSocket Client
    participant GW as Gateway (Go)
    participant Handler as Handler
    participant Safety as Safety Module
    participant Adapter as Mock Adapter
    participant Redis as Redis Streams

    Note over Operator, Redis: 操作ロック取得 → 速度コマンド送信

    Operator->>Browser: ManualControlPage を開く
    Browser->>WS: WebSocket接続
    WS->>GW: ws://gateway:8080/ws?robot_id=xxx&token=yyy
    GW->>GW: トークン検証
    GW->>Handler: Client登録
    Handler->>Handler: Hub.Register(client)

    Operator->>Browser: 操作ロック取得ボタン
    Browser->>WS: {type: "op_lock", robot_id: "robot-1"}
    WS->>GW: メッセージ送信
    GW->>Handler: HandleMessage
    Handler->>Safety: OperationLock.Acquire("robot-1", "user-1")
    Safety-->>Handler: LockInfo (成功)
    Handler-->>WS: {type: "lock_status", payload: {locked: true}}
    WS-->>Browser: ロック取得完了

    Operator->>Browser: ジョイスティック操作
    Browser->>WS: {type: "velocity_cmd", payload: {linear_x: 0.5, angular_z: 0.3}}
    WS->>GW: メッセージ送信
    GW->>Handler: HandleMessage
    Handler->>Safety: EStop.IsActive("robot-1")
    Safety-->>Handler: false (停止していない)
    Handler->>Safety: OpLock.HasLock("robot-1", "user-1")
    Safety-->>Handler: true (ロック保持中)
    Handler->>Safety: VelocityLimiter.Limit({0.5, 0, 0.3})
    Safety-->>Handler: {0.5, 0, 0.3, clamped: false}
    Handler->>Safety: Watchdog.RecordCommand("robot-1")
    Handler->>Adapter: SendCommand(velocity_cmd)
    Adapter-->>Handler: nil (成功)
    Handler->>Redis: PublishCommand("robot-1", cmd)
    Handler-->>WS: {type: "cmd_ack"}
```

---

## 8. シーケンス図 — センサーデータ配信

```mermaid
sequenceDiagram
    participant Adapter as MockAdapter (Go)
    participant Hub as Hub
    participant Redis as Redis Streams
    participant Client1 as Client A (robot-1購読)
    participant Client2 as Client B (robot-2購読)
    participant Worker as RecordingWorker (Python)
    participant DB as PostgreSQL

    Note over Adapter, DB: センサーデータのリアルタイム配信と記録

    loop 20Hz (50ms間隔)
        Adapter->>Adapter: generateOdometry()
        Adapter->>Hub: SensorData{type:"odometry", x, y, theta}
        Hub->>Hub: BroadcastToRobot("robot-1")
        Hub->>Client1: WebSocket送信 (購読中)
        Hub--xClient2: 送信しない (別ロボット購読)
        Hub->>Redis: XADD robot:sensor_data
    end

    loop 10Hz (100ms間隔)
        Adapter->>Adapter: simulateLiDAR()
        Adapter->>Hub: SensorData{type:"lidar", ranges[360]}
        Hub->>Client1: WebSocket送信
        Hub->>Redis: XADD robot:sensor_data
    end

    loop バッチ処理
        Worker->>Redis: XREADGROUP robot:sensor_data (50件/回)
        Redis-->>Worker: メッセージ群
        Worker->>Worker: should_record(robot_id, sensor_type)
        alt 記録セッション有効
            Worker->>DB: INSERT INTO sensor_data
            Worker->>Redis: XACK (処理完了通知)
        else 記録なし
            Worker->>Redis: XACK (スキップ)
        end
    end
```

---

## 9. シーケンス図 — RAG質問応答

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant Browser as ブラウザ (RAGChatPage)
    participant API as Backend API
    participant RAGSvc as RAGService
    participant Embed as EmbeddingService (nomic-embed-text)
    participant PGV as PostgreSQL + pgvector
    participant LLM as OllamaClient (Llama 3)

    Note over User, LLM: ドキュメントアップロード

    User->>Browser: PDFファイルをアップロード
    Browser->>API: POST /api/v1/rag/documents (multipart/form-data)
    API->>RAGSvc: ingest_document(title, content, ...)
    RAGSvc->>RAGSvc: TextSplitter.split(content) → 10 chunks
    RAGSvc->>Embed: embed_batch(10 chunks)
    loop 各チャンク
        Embed->>Embed: POST /api/embeddings {model: "nomic-embed-text"}
    end
    Embed-->>RAGSvc: list[list[float]] (768次元 × 10)
    RAGSvc->>PGV: INSERT rag_documents + document_chunks
    PGV-->>RAGSvc: created
    RAGSvc-->>API: RAGDocument
    API-->>Browser: 200 {id, title, chunk_count: 10}

    Note over User, LLM: 質問応答

    User->>Browser: "ロボットのLiDARセンサーの仕様は？"
    Browser->>API: POST /api/v1/rag/query {question, top_k: 5}
    API->>RAGSvc: query(question, top_k=5)
    RAGSvc->>Embed: embed("ロボットのLiDARセンサーの仕様は？")
    Embed-->>RAGSvc: question_embedding (768次元)
    RAGSvc->>PGV: search_similar_chunks(embedding, limit=5, min_similarity=0.7)
    Note right of PGV: SELECT *, 1-(embedding <=> query::vector)<br/>FROM document_chunks<br/>WHERE similarity >= 0.7<br/>ORDER BY distance LIMIT 5
    PGV-->>RAGSvc: [(chunk1, 0.92), (chunk2, 0.88), (chunk3, 0.85)]
    RAGSvc->>RAGSvc: context = "[Source 1] ..." + "[Source 2] ..." + ...
    RAGSvc->>LLM: generate(prompt=question, context=context)
    Note right of LLM: POST /api/chat<br/>{model: "llama3",<br/>messages: [system+context, user]}
    LLM-->>RAGSvc: "LiDARセンサーは360度スキャンで..."
    RAGSvc-->>API: {answer, sources: [{chunk, similarity}]}
    API-->>Browser: 200 RAGQueryResult
    Browser-->>User: 回答とソース情報を表示
```

---

## 10. シーケンス図 — 緊急停止 (E-Stop)

```mermaid
sequenceDiagram
    actor Operator as オペレーター
    participant Browser as ブラウザ
    participant WS as WebSocket
    participant Handler as Gateway Handler
    participant EStop as EStopManager
    participant Adapter as RobotAdapter
    participant Hub as Hub
    participant Client2 as 他のクライアント

    Note over Operator, Client2: 緊急停止の発動

    Operator->>Browser: E-STOPボタン押下（赤い大きなボタン）
    Browser->>WS: {type: "estop", payload: {activate: true, reason: "operator_request"}}
    WS->>Handler: HandleMessage
    Handler->>EStop: Activate(ctx, "robot-1", "user-1", "operator_request")
    EStop->>EStop: active["robot-1"] = true
    EStop->>Adapter: EmergencyStop(ctx)
    Adapter->>Adapter: 全モーター即時停止
    Adapter-->>EStop: nil (成功)
    EStop-->>Handler: nil
    Handler->>Hub: BroadcastToRobot("robot-1", estop_status)
    Hub->>WS: {type: "safety_alert", payload: {estop: true}}
    Hub->>Client2: {type: "safety_alert", payload: {estop: true}}
    WS-->>Browser: 緊急停止通知
    Browser->>Browser: EStopButton → 黄色 "RESET" 表示
    Browser->>Browser: コマンド送信を無効化

    Note over Operator, Client2: 以降のコマンドは拒否

    Operator->>Browser: ジョイスティック操作
    Browser->>WS: {type: "velocity_cmd", ...}
    WS->>Handler: HandleMessage
    Handler->>EStop: IsActive("robot-1")
    EStop-->>Handler: true
    Handler-->>WS: {type: "error", error: "E-Stop is active"}
    WS-->>Browser: エラー表示

    Note over Operator, Client2: E-Stop 解除

    Operator->>Browser: RESETボタン押下
    Browser->>WS: {type: "estop", payload: {activate: false}}
    WS->>Handler: HandleMessage
    Handler->>EStop: Release("robot-1", "user-1")
    EStop->>EStop: delete active["robot-1"]
    Handler->>Hub: BroadcastToRobot("robot-1", estop_released)
    Hub->>WS: {type: "safety_alert", payload: {estop: false}}
    Hub->>Client2: {type: "safety_alert", payload: {estop: false}}
    Browser->>Browser: EStopButton → 赤 "E-STOP" 表示（通常状態）
```

---

## 11. シーケンス図 — データ記録

```mermaid
sequenceDiagram
    actor User as ユーザー
    participant Browser as ブラウザ
    participant API as Backend API
    participant RecSvc as RecordingService
    participant DB as PostgreSQL
    participant Redis as Redis Streams
    participant Worker as RecordingWorker
    participant Gateway as Gateway

    Note over User, Gateway: 記録セッション開始

    User->>Browser: 記録開始ボタン
    Browser->>API: POST /api/v1/recordings {robot_id, sensor_types}
    API->>RecSvc: start_recording(robot_id, user_id, config)
    RecSvc->>DB: INSERT recording_sessions (is_active=true)
    DB-->>RecSvc: RecordingSession
    RecSvc-->>API: RecordingSession
    API-->>Browser: 200 {id, is_active: true, started_at}

    Note over User, Gateway: データ記録中

    loop センサーデータ受信
        Gateway->>Redis: XADD robot:sensor_data {robot_id, sensor_type, data}
        Worker->>Redis: XREADGROUP (消費)
        Worker->>RecSvc: should_record(robot_id, sensor_type)
        RecSvc->>DB: SELECT recording_sessions WHERE robot_id AND is_active
        DB-->>RecSvc: RecordingSession (active)
        RecSvc-->>Worker: session (記録対象)
        Worker->>RecSvc: record_data(session, sensor_data)
        RecSvc->>DB: INSERT sensor_data (session_id=session.id)
        RecSvc->>DB: UPDATE recording_sessions SET record_count += 1
    end

    Note over User, Gateway: 記録セッション停止

    User->>Browser: 記録停止ボタン
    Browser->>API: POST /api/v1/recordings/{id}/stop
    API->>RecSvc: stop_recording(session_id)
    RecSvc->>DB: UPDATE recording_sessions SET is_active=false, stopped_at=now()
    DB-->>RecSvc: RecordingSession (stopped)
    RecSvc-->>API: RecordingSession
    API-->>Browser: 200 {is_active: false, record_count: 1500, stopped_at}
```

---

## 12. 状態遷移図 — ロボット状態

```mermaid
stateDiagram-v2
    [*] --> DISCONNECTED

    DISCONNECTED --> CONNECTING : Connect()
    CONNECTING --> IDLE : 接続成功
    CONNECTING --> ERROR : 接続失敗
    CONNECTING --> DISCONNECTED : タイムアウト

    IDLE --> MOVING : velocity_cmd 受信
    IDLE --> EMERGENCY_STOPPED : E-Stop発動
    IDLE --> DISCONNECTED : Disconnect()

    MOVING --> IDLE : 速度 = 0 / タイムアウト
    MOVING --> EMERGENCY_STOPPED : E-Stop発動
    MOVING --> ERROR : エラー発生
    MOVING --> DISCONNECTED : 接続断

    EMERGENCY_STOPPED --> IDLE : E-Stop解除
    EMERGENCY_STOPPED --> DISCONNECTED : Disconnect()

    ERROR --> IDLE : エラー復旧
    ERROR --> DISCONNECTED : Disconnect()
    ERROR --> CONNECTING : 再接続試行

    note right of DISCONNECTED
        初期状態
        アダプタ未接続
    end note

    note right of IDLE
        接続済み・待機中
        コマンド受付可能
    end note

    note right of MOVING
        移動中
        ウォッチドッグ監視中
    end note

    note right of EMERGENCY_STOPPED
        緊急停止中
        全コマンド拒否
    end note
```

---

## 13. 状態遷移図 — データセット状態

```mermaid
stateDiagram-v2
    [*] --> CREATING

    CREATING --> READY : データ収集完了
    CREATING --> ERROR : 収集エラー

    READY --> EXPORTING : export_dataset()
    READY --> ARCHIVED : archive()
    READY --> [*] : delete()

    EXPORTING --> READY : エクスポート完了
    EXPORTING --> ERROR : エクスポートエラー

    ARCHIVED --> READY : restore()
    ARCHIVED --> [*] : delete()

    ERROR --> CREATING : 再試行
    ERROR --> [*] : delete()

    note right of CREATING
        センサーデータ収集中
        record_count 計算中
    end note

    note right of READY
        利用可能
        エクスポート可能
    end note

    note right of EXPORTING
        CSV/Parquet/JSON
        ファイル生成中
    end note
```

---

## 14. 依存性注入フロー図

```mermaid
graph TD
    subgraph "FastAPI Request"
        REQ[HTTP Request]
    end

    subgraph "Dependencies Chain"
        DB_SESSION["get_db()<br/>AsyncSession"]
        SETTINGS["get_settings()<br/>Settings (@lru_cache)"]
        SECURITY["HTTPBearer<br/>credentials"]

        USER_REPO["get_user_repo(session)<br/>→ SQLAlchemyUserRepository"]
        ROBOT_REPO["get_robot_repo(session)<br/>→ SQLAlchemyRobotRepository"]
        SENSOR_REPO["get_sensor_data_repo(session)<br/>→ SQLAlchemySensorDataRepository"]
        DATASET_REPO["get_dataset_repo(session)<br/>→ SQLAlchemyDatasetRepository"]
        RAG_REPO["get_rag_repo(session)<br/>→ SQLAlchemyRAGRepository"]
        AUDIT_REPO["get_audit_repo(session)<br/>→ SQLAlchemyAuditRepository"]
        RECORDING_REPO["get_recording_repo(session)<br/>→ SQLAlchemyRecordingRepository"]

        CURRENT_USER["get_current_user()<br/>→ User"]
        ADMIN_USER["require_role(ADMIN)<br/>→ User"]
        OPERATOR_USER["require_role(ADMIN, OPERATOR)<br/>→ User"]

        DATASET_SVC["get_dataset_service()<br/>→ DatasetService"]
        RECORDING_SVC["get_recording_service()<br/>→ RecordingService"]
        AUDIT_SVC["get_audit_service()<br/>→ AuditService"]
    end

    subgraph "Endpoint"
        ENDPOINT["@router.post('/robots')"]
    end

    REQ --> DB_SESSION
    REQ --> SETTINGS
    REQ --> SECURITY

    DB_SESSION --> USER_REPO
    DB_SESSION --> ROBOT_REPO
    DB_SESSION --> SENSOR_REPO
    DB_SESSION --> DATASET_REPO
    DB_SESSION --> RAG_REPO
    DB_SESSION --> AUDIT_REPO
    DB_SESSION --> RECORDING_REPO

    USER_REPO --> CURRENT_USER
    SETTINGS --> CURRENT_USER
    SECURITY --> CURRENT_USER

    CURRENT_USER --> ADMIN_USER
    CURRENT_USER --> OPERATOR_USER

    DATASET_REPO --> DATASET_SVC
    SENSOR_REPO --> DATASET_SVC
    RECORDING_REPO --> RECORDING_SVC
    SENSOR_REPO --> RECORDING_SVC
    AUDIT_REPO --> AUDIT_SVC

    OPERATOR_USER --> ENDPOINT
    ROBOT_REPO --> ENDPOINT
    AUDIT_SVC --> ENDPOINT

    style REQ fill:#e0f2fe
    style ENDPOINT fill:#dcfce7
    style DB_SESSION fill:#fef3c7
    style CURRENT_USER fill:#fce7f3
    style ADMIN_USER fill:#fee2e2
    style OPERATOR_USER fill:#fee2e2
```

---

## 15. Docker ネットワーク構成図

```mermaid
graph TB
    subgraph frontend_network["frontend-network (bridge)"]
        FE[Frontend<br/>:5173 / :3000]
        BE_F[Backend<br/>:8000]
        GW_F[Gateway<br/>:8080]
    end

    subgraph backend_network["backend-network (bridge)"]
        BE_B[Backend<br/>:8000]
        GW_B[Gateway<br/>:8080 / :50051]
        PG[(PostgreSQL<br/>:5432<br/>TimescaleDB + pgvector)]
        RD[(Redis<br/>:6379<br/>Streams)]
        OL[Ollama<br/>:11434<br/>Llama3 + nomic-embed-text]
    end

    subgraph volumes["Persistent Volumes"]
        PG_VOL[(postgres-data)]
        RD_VOL[(redis-data)]
        OL_VOL[(ollama-data)]
        UP_VOL[(backend-uploads)]
        DA_VOL[(backend-data)]
    end

    FE -.->|REST API| BE_F
    FE -.->|WebSocket| GW_F

    BE_B -->|asyncpg| PG
    BE_B -->|redis-py| RD
    BE_B -->|httpx| OL
    GW_B -->|go-redis| RD

    PG --- PG_VOL
    RD --- RD_VOL
    OL --- OL_VOL
    BE_B --- UP_VOL
    BE_B --- DA_VOL

    BE_F -.- BE_B
    GW_F -.- GW_B

    style frontend_network fill:#dbeafe,stroke:#3b82f6
    style backend_network fill:#fef3c7,stroke:#f59e0b
    style volumes fill:#f3e8ff,stroke:#a855f7
```

---

## 16. CI/CD パイプライン図

```mermaid
graph LR
    subgraph Trigger["トリガー"]
        PUSH[Push to main/develop]
        PR[Pull Request to main]
        TAG[Tag v*.*.*]
    end

    subgraph CI["CI Pipeline (ci.yml)"]
        direction TB
        BT[Backend Test<br/>Python 3.12<br/>pytest --cov]
        FT[Frontend Test<br/>Node 20<br/>npm test + lint + build]
        GT[Gateway Test<br/>Go 1.22<br/>go test + vet + build]
        DC[Docker Compose<br/>Validation]
    end

    subgraph CD_STG["CD Staging (cd-staging.yml)"]
        BUILD_STG[Docker Build<br/>All Services]
        PUSH_STG[Push to GHCR<br/>:staging tag]
        DEPLOY_STG[Deploy to<br/>Staging]
    end

    subgraph CD_PROD["CD Production (cd-production.yml)"]
        BUILD_PROD[Docker Build<br/>All Services]
        PUSH_PROD[Push to GHCR<br/>:latest + :vX.Y.Z]
        DEPLOY_PROD[Deploy to<br/>Production]
    end

    PUSH --> CI
    PR --> CI

    PUSH -->|develop branch| CD_STG
    CI -->|pass| CD_STG
    BUILD_STG --> PUSH_STG --> DEPLOY_STG

    TAG --> CD_PROD
    CI -->|pass| CD_PROD
    BUILD_PROD --> PUSH_PROD --> DEPLOY_PROD

    style Trigger fill:#e0f2fe
    style CI fill:#dcfce7
    style CD_STG fill:#fef3c7
    style CD_PROD fill:#fee2e2
```

---

> **注意**: これらのMermaid図はGitHub、VS Code (Markdown Preview Mermaid Support拡張)、MkDocs (pymdownx.superfences) などで直接レンダリングできます。
