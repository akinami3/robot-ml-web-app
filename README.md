# AMR SaaS Platform

自律移動ロボット（AMR）のフリート管理を行うSaaSプラットフォームです。

## 📋 目次

- [システム概要](#システム概要)
- [アーキテクチャ](#アーキテクチャ)
- [必要要件](#必要要件)
- [環境構築](#環境構築)
- [起動方法](#起動方法)
- [操作方法](#操作方法)
- [API仕様](#api仕様)
- [開発ガイド](#開発ガイド)

## 📖 システム概要

### 主な機能

- **ロボット管理**: ロボットの登録・削除・状態監視
- **ミッション管理**: タスクの作成・割り当て・進捗追跡
- **リアルタイム監視**: Frontend↔Gateway直接WebSocket通信による低レイテンシ状態更新
- **ML用データ記録**: センサ/制御値のON/OFF切替でDB保存（機械学習対応）
- **コマンドデータ記録**: 操作者の制御コマンド（state, action）ペアをDB保存（模倣学習・強化学習対応）
- **マルチベンダー対応**: Adapterパターンによる異なるメーカーのロボット統合
- **認証・認可**: JWT認証とRBACによるアクセス制御

### 技術スタック

| コンポーネント | 技術 |
|--------------|------|
| Backend | Python 3.11, FastAPI 0.109, SQLAlchemy 2.0, gRPC |
| Gateway | Go 1.21, WebSocket, gRPC, MQTT |
| Frontend | Next.js 14, React 18, TypeScript, TanStack Query |
| Database | PostgreSQL 15, Redis 7 |
| Message Broker | Eclipse Mosquitto (MQTT) |
| Container | Docker, Docker Compose |

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                   (Next.js + React)                          │
└───────┬───────────────────┬─────────────────────────────────┘
        │ WebSocket             │ REST API
        │ (リアルタイム操作)       │ (CRUD/認証/ML)
        │                       │
┌───────▼────────────┐  ┌────▼────────────────────────┐
│  Fleet Gateway       │  │          Backend                  │
│   (Go + WS/gRPC)    │  │         (FastAPI)                 │
│ ┌─────┐ ┌─────┐    │  │ ┌─────┐ ┌─────┐ ┌────────┐   │
│ │ WS  │ │MQTT │    │  │ │Auth │ │CRUD │ │ Sensor │   │
│ └─────┘ └─────┘    │  │ └─────┘ └─────┘ │  Data  │   │
│ ┌─────┐ ┌─────┐    │  │ ┌─────┐ ┌─────┐ │ Record │   │
│ │ FSM │ │Adapt│    │  │ │Misn │ │ ML  │ └────────┘   │
│ └─────┘ └─────┘    │  │ └─────┘ └─────┘             │
└────────┬─────────────┘  └─────────┬───────────────────┘
        │ MQTT                  │       ▲
        │                 ┌────┴────┐ │ gRPC
        │                 │PostgreSQL│ │ (データ記録転送)
┌───────▼─────────────┐ │  Redis  │ │
│       Robots        │ └─────────┘ │
│  (Adapter Pattern)  │             │
└─────────────────────┘   Gateway ──┘
```

**ハイブリッド通信アーキテクチャ：**

| 経路 | プロトコル | 用途 | 特性 |
|------|------------|------|------|
| Frontend ↔ Gateway | WebSocket | ロボット操作・リアルタイム状態・記録ON/OFF | 低レイテンシ |
| Frontend ↔ Backend | REST | 認証・CRUD・ML・センサ/コマンドデータ照会 | ビジネスロジック |
| Gateway → Backend | gRPC | センサ/制御値・コマンドデータのDB保存転送 | 確実性重視 |
| Gateway ↔ AMR | MQTT | ロボット制御 | ベンダー対応 |

### クラス図

```mermaid
classDiagram
    direction TB
    
    %% Frontend Layer
    class Frontend {
        +Dashboard
        +RobotList
        +MissionPanel
        +RecordingToggle
    }
    
    class useGatewayWS {
        +sendCommand(robotId, cmd)
        +setRecording(robotId, on/off)
        +subscribe(robotIds)
        +robotStatuses
        +recordingState
    }
    
    %% Backend Layer
    class Backend {
        +FastAPI app
        +REST API
        +gRPC Server (DataRecording)
    }
    
    class AuthService {
        +login(credentials)
        +verify_token(token)
        +refresh_token()
    }
    
    class RobotService {
        +get_robots()
        +create_robot()
        +delete_robot()
    }
    
    class MissionService {
        +create_mission()
        +assign_robot()
        +update_progress()
    }
    
    class SensorDataService {
        +get_sensor_data(filters)
        +get_stats()
        +record_batch(records)
    }
    
    class CommandDataService {
        +get_command_data(filters)
        +get_stats()
        +get_training_pairs(robot_id)
        +record_batch(records)
    }
    
    class DataRecordingServer {
        +RecordSensorData(batch)
        +StreamSensorData(stream)
        +RecordCommandData(batch)
    }
    
    %% Gateway Layer
    class FleetGateway {
        +WebSocket Server
        +gRPC Server
        +handleMessage()
    }
    
    class WSServer {
        +HandleWebSocket()
        +broadcastRobotStatus()
        +handleCommand()
        +handleSetRecording()
    }
    
    class BackendForwarder {
        -sensorBuf recordBuffer
        -commandBuf recordBuffer
        +ForwardSensorData()
        +ForwardCommandData()
    }
    
    class RobotManager {
        -robots Map
        +RegisterRobot()
        +GetRobot()
        +UpdateStatus()
        +GetSensorData()
    }
    
    class StateMachine {
        -currentState State
        +Transition(event)
        +GetState()
    }
    
    class MQTTClient {
        +Subscribe(topic)
        +Publish(topic, message)
    }
    
    class RobotAdapter {
        <<interface>>
        +ParseStatus(payload)
        +FormatCommand(cmd)
    }
    
    class MiRAdapter {
        +ParseStatus(payload)
        +FormatCommand(cmd)
    }
    
    class CustomAdapter {
        +ParseStatus(payload)
        +FormatCommand(cmd)
    }
    
    %% Database
    class PostgreSQL {
        +robots table
        +missions table
        +users table
        +sensor_data_records table
        +command_data_records table
    }
    
    %% Relationships
    Frontend --> useGatewayWS
    useGatewayWS --> WSServer : WebSocket
    Frontend --> Backend : REST API
    
    Backend --> AuthService
    Backend --> RobotService
    Backend --> MissionService
    Backend --> SensorDataService
    Backend --> CommandDataService
    Backend --> DataRecordingServer
    Backend --> PostgreSQL
    
    FleetGateway --> WSServer
    FleetGateway --> RobotManager
    FleetGateway --> MQTTClient
    FleetGateway --> BackendForwarder
    
    BackendForwarder --> DataRecordingServer : gRPC
    RobotManager --> StateMachine
    MQTTClient --> RobotAdapter
    RobotAdapter <|.. MiRAdapter
    RobotAdapter <|.. CustomAdapter
```

### シーケンス図

#### ロボットへのコマンド送信フロー

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant F as Frontend
    participant G as Gateway (Go)
    participant M as MQTT Broker
    participant R as Robot

    U->>F: コマンド実行ボタンクリック
    F->>G: WebSocket {type: "command", command: "move"}
    
    Note over G: コマンドをロボット形式に変換
    G->>G: Adapter.FormatCommand()
    
    G->>M: Publish fleet/{robot_id}/command
    M->>R: コマンド配信
    
    G-->>F: WebSocket {type: "command_response", success: true}
    F-->>U: コマンド応答表示
    
    R->>M: Publish fleet/{robot_id}/status
    M->>G: ステータス受信
    
    Note over G: ステータスをパース
    G->>G: Adapter.ParseStatus()
    G->>G: StateMachine.Transition()
    
    G-->>F: WebSocket {type: "robot_status", data: {...}}
    F-->>U: UI更新（リアルタイム）
```

#### データ記録フロー（ML用センサデータ保存）

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant F as Frontend
    participant G as Gateway
    participant B as Backend
    participant DB as PostgreSQL
    participant R as Robot

    Note over U,F: 記録ONボタンを押下
    U->>F: データ記録 ON
    F->>G: WebSocket {type: "set_recording", robot_id: "R1", recording: true}
    G-->>F: WebSocket {type: "recording_status", recording: true}
    F-->>U: 記録中インジケータ点灯
    
    loop 記録中（リアルタイム）
        R->>G: MQTT センサ/制御値
        G-->>F: WebSocket {type: "robot_status", sensor_data: {...}}
        F-->>U: リアルタイム表示
        
        Note over G: バッファリング
        G->>G: buffer.append(record)
        
        alt バッファ満 or タイマー
            G->>B: gRPC RecordSensorData(batch)
            B->>DB: INSERT sensor_data_records
            B-->>G: {success: true, recorded_count: N}
        end
    end
    
    U->>F: データ記録 OFF
    F->>G: WebSocket {type: "set_recording", recording: false}
    G->>G: 残りバッファをflush
    G->>B: gRPC RecordSensorData(remaining)
    B->>DB: INSERT
    G-->>F: WebSocket {type: "recording_status", recording: false}
    F-->>U: 記録停止
    
    Note over U,DB: 後日ML学習時
    F->>B: GET /api/v1/sensor-data?robot_id=R1
    B->>DB: SELECT * FROM sensor_data_records
    B-->>F: センサデータ一覧
```

#### コマンドデータ記録フロー（ML用 状態-行動ペア）

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant F as Frontend
    participant G as Gateway
    participant B as Backend
    participant DB as PostgreSQL

    Note over U,F: 記録ONの状態でコマンド操作
    U->>F: 移動コマンド送信
    F->>G: WebSocket {type: "command", command: "move", params: {x,y}}

    Note over G: コマンド実行前にロボット状態を取得
    G->>G: robotStateBefore = GetSensorData + GetControlData

    G->>G: RobotManager.MoveRobot()

    alt 記録ON
        Note over G: (state, action)ペアをバッファリング
        G->>G: commandBuf.add({state, command, params})

        alt バッファ満 or タイマー
            G->>B: gRPC RecordCommandData(batch)
            B->>DB: INSERT command_data_records
            B-->>G: {success: true, recorded_count: N}
        end
    end

    G-->>F: WebSocket {type: "command_response", success: true}
    F-->>U: コマンド応答表示

    Note over U,DB: 後日ML学習時
    F->>B: GET /api/v1/command-data/training-pairs?robot_id=R1
    B->>DB: SELECT * FROM command_data_records
    B-->>F: (state, action)ペア一覧
```

#### ミッション実行フロー

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant DB as PostgreSQL
    participant G as Gateway
    participant M as MQTT Broker
    participant R as Robot

    U->>F: ミッション作成
    F->>B: POST /api/v1/missions
    B->>DB: INSERT mission
    B-->>F: mission_id
    
    U->>F: ロボット割り当て
    F->>B: POST /api/v1/missions/{id}/assign
    B->>DB: UPDATE mission (robot_id)
    
    Note over F,G: ミッション開始はGatewayへ直接指示
    F->>G: WebSocket {type: "command", command: "start_mission"}
    G->>G: RobotManager.GetRobot()
    G->>G: StateMachine.Transition(MISSION_START)
    
    G->>M: Publish fleet/{robot_id}/mission
    M->>R: ミッション開始
    
    loop ミッション実行中
        R->>M: Publish fleet/{robot_id}/status
        M->>G: ステータス受信
        G->>G: ステータス更新
        G-->>F: WebSocket ロボット状態
        F-->>U: プログレスバー更新
    end
    
    R->>M: ミッション完了通知
    M->>G: 完了ステータス
    G->>G: StateMachine.Transition(MISSION_COMPLETE)
    G-->>F: WebSocket 完了通知
    
    Note over F,B: 完了状態をBackendにDB保存
    F->>B: PUT /api/v1/missions/{id} (status=completed)
    B->>DB: UPDATE mission (status=completed)
    F-->>U: 完了表示
```

#### 認証フロー

```mermaid
sequenceDiagram
    autonumber
    participant U as User
    participant F as Frontend
    participant B as Backend
    participant DB as PostgreSQL
    participant R as Redis

    U->>F: ログイン情報入力
    F->>B: POST /api/v1/auth/login
    
    B->>DB: SELECT user WHERE email=?
    DB-->>B: user record
    
    B->>B: パスワード検証 (bcrypt)
    
    alt 認証成功
        B->>B: JWT生成 (access + refresh)
        B->>R: セッション保存
        B-->>F: {access_token, refresh_token}
        F->>F: LocalStorageに保存
        F-->>U: ダッシュボードへリダイレクト
    else 認証失敗
        B-->>F: 401 Unauthorized
        F-->>U: エラーメッセージ表示
    end
    
    Note over F,B: 以降のAPIリクエスト
    F->>B: GET /api/v1/robots (Authorization: Bearer token)
    B->>B: JWT検証
    B->>R: セッション確認
    B-->>F: ロボット一覧
```

## 📦 必要要件

### ローカル開発

- Docker 24.0+
- Docker Compose 2.20+
- Git

### 個別開発（Dockerを使わない場合）

- Python 3.11+
- Go 1.21+
- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- Mosquitto (MQTT Broker)

## 🚀 環境構築

### 1. リポジトリのクローン

```bash
git clone https://github.com/your-org/amr-saas-platform.git
cd amr-saas-platform
```

### 2. 環境変数の設定

```bash
# 環境変数ファイルを作成
cp .env.example .env

# 必要に応じて編集
vim .env
```

**.env ファイルの例:**

```env
# Database
POSTGRES_USER=amr_user
POSTGRES_PASSWORD=amr_password
POSTGRES_DB=amr_db
DATABASE_URL=postgresql+asyncpg://amr_user:amr_password@postgres:5432/amr_db

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# MQTT
MQTT_BROKER_HOST=mosquitto
MQTT_BROKER_PORT=1883

# Gateway (gRPC)
GRPC_PORT=50051
GATEWAY_GRPC_ADDRESS=gateway:50051

# Gateway (WebSocket for Frontend)
WEBSOCKET_PORT=8082

# Backend gRPC Server (data recording)
BACKEND_GRPC_ADDRESS=backend:50052
GRPC_SERVER_PORT=50052

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GATEWAY_WS_URL=ws://localhost:8082/ws
```

### 3. Docker Composeでの起動

```bash
# 全サービスをビルド・起動
docker-compose up -d --build

# ログの確認
docker-compose logs -f
```

### 4. 個別サービスの起動（開発用）

#### Backend (FastAPI)

```bash
cd backend

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Linux/Mac
# または
.\venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt

# 環境変数の設定
export DATABASE_URL="postgresql+asyncpg://amr_user:amr_password@localhost:5432/amr_db"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET_KEY="your-secret-key"

# サーバー起動
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Gateway (Go)

```bash
cd gateway

# 依存関係のダウンロード
go mod download

# 環境変数の設定
export MQTT_BROKER_HOST="localhost"
export MQTT_BROKER_PORT="1883"
export GRPC_PORT="50051"
export WEBSOCKET_PORT="8082"
export JWT_SECRET_KEY="your-secret-key"
export BACKEND_GRPC_ADDRESS="localhost:50052"

# サーバー起動
go run cmd/gateway/main.go
```

#### Frontend (Next.js)

```bash
cd frontend

# 依存関係のインストール
npm install

# 環境変数の設定
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
echo "NEXT_PUBLIC_GATEWAY_WS_URL=ws://localhost:8082/ws" >> .env.local

# 開発サーバー起動
npm run dev
```

## 🎮 起動方法

### Docker Compose（推奨）

```bash
# 全サービス起動
docker-compose up -d

# 特定のサービスのみ起動
docker-compose up -d postgres redis mosquitto  # インフラのみ
docker-compose up -d backend                    # バックエンドのみ

# サービス停止
docker-compose down

# データを含めて完全削除
docker-compose down -v
```

### 起動確認

| サービス | URL | 説明 |
|---------|-----|------|
| Frontend | http://localhost:3000 | Web UI |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Gateway (WebSocket) | ws://localhost:8082/ws | リアルタイム操作 |
| Gateway (gRPC) | localhost:50051 | 内部通信 |
| Backend (gRPC) | localhost:50052 | データ記録受信 |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache |
| Mosquitto | localhost:1883 | MQTT Broker |

## 📱 操作方法

### 1. 初期セットアップ

#### ユーザー登録

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123"
  }'
```

#### ログイン

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=password123"
```

レスポンス例:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 2. ロボット管理

#### ロボット登録

```bash
TOKEN="your-access-token"

curl -X POST http://localhost:8000/api/v1/robots \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "AMR-001",
    "serial_number": "SN-2024-001",
    "model": "Navigator X1",
    "vendor": "RobotCorp"
  }'
```

#### ロボット一覧取得

```bash
curl -X GET http://localhost:8000/api/v1/robots \
  -H "Authorization: Bearer $TOKEN"
```

#### ロボットにコマンド送信

```bash
curl -X POST http://localhost:8000/api/v1/robots/1/command \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "command": "navigate",
    "payload": {
      "destination": {"x": 10.0, "y": 5.0},
      "speed": 0.5
    }
  }'
```

### 3. ミッション管理

#### ミッション作成

```bash
curl -X POST http://localhost:8000/api/v1/missions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "配送タスク #1",
    "description": "A地点からB地点への荷物配送",
    "robot_id": 1,
    "priority": 1,
    "waypoints": [
      {"x": 0, "y": 0, "action": "pickup"},
      {"x": 10, "y": 5, "action": "dropoff"}
    ]
  }'
```

#### ミッション一覧取得

```bash
curl -X GET http://localhost:8000/api/v1/missions \
  -H "Authorization: Bearer $TOKEN"
```

### 4. Web UIでの操作

1. ブラウザで http://localhost:3000 にアクセス
2. ログイン画面でメールアドレスとパスワードを入力
3. ダッシュボードでシステム全体の状態を確認
4. 「Robots」メニューでロボットの追加・管理
5. 「Missions」メニューでミッションの作成・監視

## 📚 API仕様

### 認証エンドポイント

| Method | Endpoint | 説明 |
|--------|----------|------|
| POST | /api/v1/auth/register | ユーザー登録 |
| POST | /api/v1/auth/login | ログイン（トークン取得） |
| GET | /api/v1/auth/me | 現在のユーザー情報 |

### ロボットエンドポイント

| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | /api/v1/robots | ロボット一覧 |
| POST | /api/v1/robots | ロボット登録 |
| GET | /api/v1/robots/{id} | ロボット詳細 |
| PUT | /api/v1/robots/{id} | ロボット更新 |
| DELETE | /api/v1/robots/{id} | ロボット削除 |
| POST | /api/v1/robots/{id}/command | コマンド送信 |

### ミッションエンドポイント

| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | /api/v1/missions | ミッション一覧 |
| POST | /api/v1/missions | ミッション作成 |
| GET | /api/v1/missions/{id} | ミッション詳細 |
| PUT | /api/v1/missions/{id} | ミッション更新 |
| DELETE | /api/v1/missions/{id} | ミッション削除 |

### センサデータエンドポイント

| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | /api/v1/sensor-data | センサデータ取得（フィルタ対応） |
| GET | /api/v1/sensor-data/stats | ロボット別統計 |
| DELETE | /api/v1/sensor-data/{robot_id} | センサデータ削除 |

### コマンドデータエンドポイント

| Method | Endpoint | 説明 |
|--------|----------|------|
| GET | /api/v1/command-data | コマンドデータ取得（フィルタ対応） |
| GET | /api/v1/command-data/stats | ロボット別統計 |
| GET | /api/v1/command-data/command-types | コマンド種別別集計 |
| GET | /api/v1/command-data/training-pairs | ML学習用 (state, action) ペア取得 |
| DELETE | /api/v1/command-data/{robot_id} | コマンドデータ削除 |

### Gateway WebSocket API

接続先: `ws://localhost:8082/ws?token={JWT_TOKEN}`

| メッセージタイプ | 方向 | 説明 |
|----------------|------|------|
| subscribe | Client → GW | ロボット状態購読 |
| unsubscribe | Client → GW | 購読解除 |
| command | Client → GW | ロボットコマンド送信 |
| set_recording | Client → GW | データ記録ON/OFF |
| robot_status | GW → Client | ロボット状態プッシュ |
| command_response | GW → Client | コマンド結果 |
| recording_status | GW → Client | 記録状態変更通知 |

詳細なAPI仕様は http://localhost:8000/docs (Swagger UI) で確認できます。

## 🛠️ 開発ガイド

### プロジェクト構造

```
amr-saas-platform/
├── proto/                   # Protocol Buffers定義（正本）
│   └── fleet.proto          # FleetGateway + DataRecordingService
├── backend/                 # FastAPI バックエンド
│   ├── proto/              # fleet.proto コピー（Docker build用）
│   ├── app/
│   │   ├── auth/           # 認証モジュール
│   │   ├── models/         # SQLAlchemy モデル
│   │   │   ├── models.py   # Robot, Mission, User
│   │   │   ├── sensor_data.py  # SensorDataRecord
│   │   │   └── command_data.py # CommandDataRecord
│   │   ├── routers/        # APIエンドポイント
│   │   │   ├── sensor_data.py  # センサデータ REST API
│   │   │   └── command_data.py # コマンドデータ REST API
│   │   ├── schemas/        # Pydantic スキーマ
│   │   ├── grpc_client/    # Gateway向けgRPCクライアント（proto自動生成）
│   │   ├── grpc_server/    # データ記録受信gRPCサーバー
│   │   ├── config.py       # 設定
│   │   ├── database.py     # DB接続
│   │   └── main.py         # アプリケーション
│   ├── requirements.txt
│   └── Dockerfile
├── gateway/                 # Go Fleet Gateway
│   ├── proto/              # fleet.proto コピー（Docker build用）
│   ├── cmd/gateway/        # エントリーポイント
│   ├── internal/
│   │   ├── adapter/        # ベンダーアダプター (Adapter Pattern)
│   │   ├── grpc/           # FleetGateway gRPCサーバー
│   │   ├── websocket/      # WebSocketサーバー（Frontend直接通信）
│   │   ├── forwarder/      # Backend転送（Generic Buffer Pattern）
│   │   ├── config/         # 設定
│   │   ├── mqtt/           # MQTTクライアント
│   │   └── robot/          # ロボット管理・FSM
│   ├── go.mod
│   └── Dockerfile
├── frontend/                # Next.js フロントエンド
│   ├── src/
│   │   ├── app/            # App Router ページ
│   │   ├── components/     # UIコンポーネント
│   │   ├── hooks/          # カスタムフック (useGatewayWS等)
│   │   ├── lib/            # APIクライアント
│   │   └── types/          # TypeScript型定義
│   ├── package.json
│   └── Dockerfile
├── docker/                  # Docker設定
│   └── mosquitto/          # MQTT Broker設定
├── scripts/
│   └── sync-proto.sh       # Proto定義の同期スクリプト
├── .github/workflows/       # CI/CD
├── docker-compose.yml
├── .env / .env.example
└── README.md
```

### テスト実行

```bash
# Backend テスト
cd backend
pytest

# Gateway テスト
cd gateway
go test ./...

# Frontend テスト
cd frontend
npm test
```

### コード品質

```bash
# Backend リンター
cd backend
ruff check .
mypy .

# Gateway リンター
cd gateway
golangci-lint run

# Frontend リンター
cd frontend
npm run lint
```

## 🔧 トラブルシューティング

### よくある問題

#### Docker Composeが起動しない

```bash
# Docker デーモンが起動しているか確認
sudo systemctl status docker

# 古いコンテナを削除
docker-compose down -v
docker system prune -f
```

#### データベース接続エラー

```bash
# PostgreSQLコンテナのログを確認
docker-compose logs postgres

# データベースを再作成
docker-compose down -v
docker-compose up -d postgres
```

#### MQTTブローカーに接続できない

```bash
# Mosquittoのログを確認
docker-compose logs mosquitto

# ポートが使用されていないか確認
netstat -tlnp | grep 1883
```

## 📄 ライセンス

MIT License

## 👥 コントリビューション

1. このリポジトリをフォーク
2. フィーチャーブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成
