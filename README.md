# robot-ml-web-app


# シーケンス図

## 初期接続

backend <-> robot間の初期接続時の流れを示します。

```mermaid
sequenceDiagram
  participant backend
  participant mqtt_broker
  participant robot as robot (real or sim)

  backend ->> mqtt_broker: broker接続確立
  robot ->> mqtt_broker: broker接続確立
  loop
    alt　速度指令受信時
      backend ->> mqtt_broker: AMR速度（並進速度、回転速度）<br>トピック名：/amr/<AMR_ID>/velocity
      mqtt_broker ->> robot: AMR速度（並進速度、回転速度）<br>トピック名：/amr/<AMR_ID>/velocity
      robot ->> robot: 速度情報に従って、AMRが移動
    end
  end

  par
    loop 定周期
      robot ->> robot: 現在位置を取得
      robot ->> mqtt_broker: AMR状態（位置、姿勢など）<br>トピック名：/amr/<AMR_ID>/status
      mqtt_broker ->> backend: AMR状態（位置、姿勢など）<br>トピック名：/amr/<AMR_ID>/status
    end
  end
```

## トピック仕様

```
<AMR_ID> は各AMRを識別するためのユニークなIDに置き換えてください。
```

### トピック一覧

| No | 概要 | トピック名 | 方向 | QOS | レテンション | 備考 |
|----|------|------------|------|-----|--------------|------|
| 1 | [AMR速度指令](#amr速度指令) | /amr/<AMR_ID>/velocity | Backend → Robot | 1 | なし | - |
| 2 | [AMR状態情報](#amr状態) | /amr/<AMR_ID>/status | Robot → Backend | 1 | なし | - |

### 各トピック詳細

```
各payloadは説明用にJSONC形式（コメント付きJSON）で記述していますが、実際の実装では、JSON形式で記述する必要があることに注意してください。
```

#### AMR速度指令

AMRはこのトピックを購読し、受信した速度指令に従って走行します。

- **トピック名**: /amr/<AMR_ID>/velocity
- **方向**: Backend → Robot
- **QOS**: 1
- **レテンション**: なし

Payload

```json
{
  "linear": 1.0,   // 並進速度 (m/s)
  "angular": 0.5   // 回転速度 (rad/s)
}
```

#### AMR状態

AMRの現在の状態情報を送信します。  
Backendはこのトピックを購読し、AMRの位置やバッテリ状態を把握します。

- **トピック名**: /amr/<AMR_ID>/status
- **方向**: Robot → Backend
- **QOS**: 1
- **レテンション**: なし

Payload

```json
{
  "position": {
    "x": 0.0,      // X座標 (m)
    "y": 0.0,      // Y座標 (m)
    "theta": 0.0   // 姿勢角 (rad)
  },
  "timestamp": 0       // Unixタイムスタンプ (ms)
}
```

以下、copilot生成による仮の設計書

## 目次
- [robot-ml-web-app](#robot-ml-web-app)
- [シーケンス図](#シーケンス図)
  - [初期接続](#初期接続)
  - [トピック仕様](#トピック仕様)
    - [トピック一覧](#トピック一覧)
    - [各トピック詳細](#各トピック詳細)
      - [AMR速度指令](#amr速度指令)
      - [AMR状態](#amr状態)
  - [目次](#目次)
  - [1. ゴールとスコープ](#1-ゴールとスコープ)
  - [2. ユースケース概要](#2-ユースケース概要)
  - [3. 全体アーキテクチャ](#3-全体アーキテクチャ)
    - [3.1 コンポーネント構成図](#31-コンポーネント構成図)
    - [3.2 デプロイ・ネットワーク構成](#32-デプロイネットワーク構成)
  - [4. フロントエンド設計](#4-フロントエンド設計)
    - [4.1 ディレクトリ構成案](#41-ディレクトリ構成案)
    - [4.2 共通 UI / ヘッダー設計](#42-共通-ui--ヘッダー設計)
    - [4.3 状態管理と通信レイヤ](#43-状態管理と通信レイヤ)
  - [5. バックエンド設計](#5-バックエンド設計)
    - [5.1 アプリケーションレイヤ構成](#51-アプリケーションレイヤ構成)
    - [5.2 クラス図](#52-クラス図)
    - [5.3 API 一覧](#53-api-一覧)
  - [6. データ管理](#6-データ管理)
    - [6.1 データベーススキーマ](#61-データベーススキーマ)
    - [6.2 ファイルストレージ戦略](#62-ファイルストレージ戦略)
    - [6.3 メッセージ / トピック設計](#63-メッセージ--トピック設計)
  - [7. シーケンス図](#7-シーケンス図)
    - [7.1 ロボット速度制御 (ジョイスティック)](#71-ロボット速度制御-ジョイスティック)
    - [7.2 カメラ映像ストリーミング](#72-カメラ映像ストリーミング)
    - [7.3 状態監視とデータロギング](#73-状態監視とデータロギング)
    - [7.4 ナビゲーション指示](#74-ナビゲーション指示)
    - [7.5 機械学習トレーニング](#75-機械学習トレーニング)
    - [7.6 Chatbot (RAG 質問応答)](#76-chatbot-rag-質問応答)
  - [8. 非機能要件](#8-非機能要件)
  - [9. セキュリティと監視](#9-セキュリティと監視)
  - [10. 将来的な拡張ポイント](#10-将来的な拡張ポイント)

## 1. ゴールとスコープ
- React + FastAPI を基盤としたロボット運用統合 Web アプリを構築する。
- ロボット制御、データ収集/蓄積、機械学習、チャットボット (RAG + LLM) をタブ切り替えで提供する。
- Unity シミュレーション/実機切替機能、MQTT/WebSocket の接続確認 UI を備える。
- Web フロントエンドとバックエンドのディレクトリ構成をタブ毎に分離し、疎結合・保守性を高める。

## 2. ユースケース概要
| タブ | 主機能 | 主な通信 | 補足 |
| ---- | ------ | -------- | ---- |
| ロボット制御 | ジョイスティック操作、リアルタイム映像、状態監視、ナビゲーション指示 | WebSocket / MQTT / REST | シミュレーション切替、通信ステータス表示 |
| データベース画面 | 状態・速度・画像メタデータの蓄積、選択保存、フェイルセーフな保存フロー | REST / WebSocket | 5 ボタン制御 (開始/一時停止/保存/破棄/終了) |
| 機械学習画面 | 保存データを用いた PyTorch トレーニング、学習曲線リアルタイム可視化 | REST / WebSocket | ML パイプラインはバックエンドジョブ + ストリーミング更新 |
| Chatbot | RAG + LLM による FAQ / オペレーション支援 | REST / WebSocket | Vector DB + Document Store |

## 3. 全体アーキテクチャ
### 3.1 コンポーネント構成図
```mermaid
flowchart LR
  subgraph Client ["Web Frontend (React)"]
    direction TB
    ClientHub(("Client Layer"))
    Header["Header & Status Indicators"]
    Tabs["Tab Router"]
    RC["Robot Control Module"]
    DBTab["Database Module"]
    MLTab["ML Module"]
    ChatTab["Chatbot Module"]
    ClientHub --> Header
    Header --> Tabs
    Tabs --> RC
    Tabs --> DBTab
    Tabs --> MLTab
    Tabs --> ChatTab
  end

  subgraph Backend ["FastAPI Backend"]
    direction TB
    BackendHub(("Backend Core"))
    APIRouter["REST Routers"]
    WS["WebSocket Gateway"]
    ServiceLayer["Service Layer"]
    Tasks["Async Task Queue"]
    BackendHub --> APIRouter
    BackendHub --> WS
    APIRouter --> ServiceLayer
    WS --> ServiceLayer
    ServiceLayer --> Tasks
  end

  subgraph Integration ["Integration Services"]
    direction TB
    IntegrationHub(("Integration Layer"))
    MQTT["MQTT Broker"]
    SimCtrl["Simulation Orchestrator"]
    Robot["Robot / Unity Sim"]
    Storage[("Object Storage for Images")]
    DB[("SQL Database")]
    VectorDB[("Vector DB")]
    LLM["LLM Provider"]
    IntegrationHub --> MQTT
    IntegrationHub --> Storage
    IntegrationHub --> DB
    IntegrationHub --> VectorDB
    IntegrationHub --> LLM
    MQTT --> Robot
    IntegrationHub --> SimCtrl
  end

  ClientHub <--> WS
  ClientHub --> APIRouter
  RC <--> WS
  DBTab --> APIRouter
  MLTab --> APIRouter
  ChatTab --> APIRouter
  ServiceLayer --> IntegrationHub
  Tasks --> IntegrationHub
  SimCtrl --> Robot
```

### 3.2 デプロイ・ネットワーク構成
- **フロントエンド**: React + Vite/Next.js, Nginx でホスト。
- **バックエンド**: FastAPI (Uvicorn/Gunicorn) + Celery (Redis/ RabbitMQ) for ML jobs。
- **MQTT ブローカ**: Mosquitto (Docker コンテナ)。
- **データベース**: PostgreSQL + SQLAlchemy。画像用オブジェクトストレージ (MinIO / S3 互換)。
- **Vector DB**: Qdrant or Weaviate。
- **メッセージング**: WebSocket (FastAPI) + MQTT (ロボット) + REST API。
- **監視**: Prometheus + Grafana, Loki でロギング。

## 4. フロントエンド設計
### 4.1 ディレクトリ構成案
```
frontend/
  src/
    app/
      Router.tsx
      store/
      hooks/
      api/
    modules/
      robot-control/
        components/
        hooks/
        services/
      database/
        ...
      ml/
        ...
      chatbot/
        ...
    shared/
      components/
      icons/
      layouts/
      utils/
  public/
```
- 各タブは `modules/<tab>/` 配下で独立管理。
- 共通 Header と WebSocket フックは `shared/` に配置。

### 4.2 共通 UI / ヘッダー設計
- **要素**: タイトル、タブナビゲーション、`シミュレーション起動/終了` ボタン、MQTT/WebSocket ステータスアイコン。
- **接続インジケータ**: `useConnectionStatus` フックが backend REST (`/health`) と WS ping を監視。
- **シミュレーション操作**: API 呼び出し (POST `/simulation/start|stop`) で Unity/実機切替。

### 4.3 状態管理と通信レイヤ
- **状態管理**: Redux Toolkit / Zustand + React Query。
- **リアルタイム**: `useWebSocket` カスタムフックでロボット制御/ML進捗/ログを購読。
- **フォーム管理**: React Hook Form を採用。

## 5. バックエンド設計
### 5.1 アプリケーションレイヤ構成
```
backend/
  app/
    main.py
    core/
      config.py
      logging.py
      dependencies.py
    api/
      router.py
      robot_control/
      database/
      ml/
      chatbot/
    services/
      robot.py
      telemetry.py
      datalogger.py
      ml_pipeline.py
      chatbot.py
    repositories/
      robot_state.py
      datasets.py
      training_runs.py
      rag_documents.py
    schemas/
      robot.py
      telemetry.py
      datasets.py
      ml.py
      chatbot.py
    workers/
      tasks.py
    adapters/
      mqtt_client.py
      websocket_manager.py
      storage_client.py
      vector_store.py
      llm_client.py
```
- `services/` がビジネスロジックを集約。
- `repositories/` はデータアクセス層 (SQLAlchemy)。
- `adapters/` で外部システムと疎結合化。

### 5.2 クラス図
```mermaid
classDiagram
    class RobotControlService {
        +set_velocity(cmd: VelocityCommand)
        +send_navigation(goal: NavGoal)
        +toggle_simulation(mode: SimulationMode)
    }

    class TelemetryService {
        +subscribe_topics(topics)
        +handle_telemetry(message)
        +persist_state(snapshot)
    }

    class DataLoggerService {
        +start_session(config)
        +pause_session(id)
        +resume_session(id)
        +save_session(id, options)
        +discard_session(id)
        +export_image(path, metadata)
    }

    class MLPipelineService {
        +launch_training(runConfig)
        +stream_metrics(runId)
        +stop_training(runId)
    }

    class ChatbotService {
        +ingest_documents(docs)
        +retrieve_context(query)
        +generate_response(context)
    }

    class MQTTClientAdapter {
        +publish(topic, payload)
        +subscribe(topic, callback)
    }

    class WebSocketHub {
        +broadcast(channel, payload)
        +register_client(client)
    }

    RobotControlService --> MQTTClientAdapter
    RobotControlService --> WebSocketHub
    TelemetryService --> MQTTClientAdapter
    TelemetryService --> DataLoggerService
    DataLoggerService --> StorageClient
    DataLoggerService --> DatasetRepository
    MLPipelineService --> DatasetRepository
    MLPipelineService --> TrainingRunRepository
    MLPipelineService --> TaskQueue
    ChatbotService --> VectorStoreAdapter
    ChatbotService --> LLMClient
```

### 5.3 API 一覧
| メソッド | エンドポイント | 概要 |
| -------- | -------------- | ---- |
| GET | `/health` | MQTT/WS ステータス含むシステムヘルスチェック |
| WS | `/ws/robot` | ロボット制御/状態ストリーミング |
| WS | `/ws/ml` | 学習進捗ストリーミング |
| WS | `/ws/chat` | 双方向チャット更新 |
| POST | `/robot/velocity` | 速度指令 |
| POST | `/robot/navigation` | 目標地点指示 |
| POST | `/simulation/start` | シミュレーション起動 |
| POST | `/simulation/stop` | シミュレーション終了 |
| POST | `/datalogger/session` | セッション開始 |
| PATCH | `/datalogger/session/{id}` | 一時停止/再開 |
| POST | `/datalogger/session/{id}/save` | 保存して終了 |
| POST | `/datalogger/session/{id}/discard` | 保存せず終了 |
| GET | `/datasets` | 保存データ一覧 |
| POST | `/ml/train` | トレーニング開始 |
| GET | `/ml/runs/{id}` | 学習メトリクス取得 |
| POST | `/chat/query` | 質問受付 |

## 6. データ管理
### 6.1 データベーススキーマ
```mermaid
erDiagram
    ROBOT_STATE ||--o{ TELEMETRY_LOG : captures
    ROBOT_STATE {
        uuid id PK
        string robot_id
        timestamp recorded_at
        jsonb pose
        jsonb status
    }

    TELEMETRY_LOG {
        uuid id PK
        uuid session_id FK
        float linear_vel
        float angular_vel
        jsonb battery
        jsonb diagnostics
        string image_path
        boolean saved
        timestamp created_at
    }

    DATASET_SESSION ||--o{ TELEMETRY_LOG : contains
    DATASET_SESSION {
        uuid id PK
        string name
        jsonb config
        string status
        timestamp started_at
        timestamp ended_at
    }

    TRAINING_RUN ||--o{ TRAINING_METRIC : logs
    TRAINING_RUN {
        uuid id PK
        uuid dataset_session_id FK
        jsonb hyperparams
        string status
        timestamp started_at
        timestamp completed_at
    }

    TRAINING_METRIC {
        uuid id PK
        uuid run_id FK
        int epoch
        float train_loss
        float val_loss
        float train_acc
        float val_acc
        timestamp logged_at
    }

    RAG_DOCUMENT {
        uuid id PK
        string source
        text content
        string vector_id
        timestamp indexed_at
    }
```

### 6.2 ファイルストレージ戦略
- 画像は `/data/uploads/images/{session_id}/{timestamp}.jpg` に保存。
- DB には `image_path` とメタ情報のみ保持。
- 大容量動画は将来のため別バケットを想定。

### 6.3 メッセージ / トピック設計
| チャネル | 用途 | 方向 |
| -------- | ---- | ---- |
| `robot/cmd/velocity` | 速度コマンド | Backend → Robot |
| `robot/cmd/navigation` | ナビゲーション指示 | Backend → Robot |
| `robot/state` | 状態情報 (位置, バッテリ) | Robot → Backend |
| `robot/camera` | カメラフレーム (バイナリ/URI) | Robot → Backend |
| `sim/control` | シミュレーション起動/停止 | Backend → Unity |
| WebSocket `/ws/robot` | 状態ブロードキャスト, joystick フィードバック | Backend ↔ Frontend |
| WebSocket `/ws/ml` | 学習メトリクス push | Backend ↔ Frontend |
| WebSocket `/ws/chat` | ストリーミング回答 | Backend ↔ Frontend |

## 7. シーケンス図



### 7.1 ロボット速度制御 (ジョイスティック)
```mermaid
sequenceDiagram
    participant User
    participant UI as React (RobotControl)
    participant WS as WebSocket Gateway
    participant MQTT as MQTT Broker
    participant Robot

    User->>UI: 操作 (ジョイスティック更新)
    UI->>WS: send VelocityCommand
    WS->>MQTT: publish robot/cmd/velocity
    MQTT-->>Robot: deliver VelocityCommand
    Robot-->>MQTT: publish new state
    MQTT-->>WS: forward state topic
    WS-->>UI: push robot state update
    UI-->>User: 更新された速度/状態を表示
```

### 7.2 カメラ映像ストリーミング
```mermaid
sequenceDiagram
    participant RobotCam as Robot Camera
    participant MQTT
    participant Backend as Backend Adapter
    participant WS as WebSocket Gateway
    participant UI as React Video Player

    loop フレーム毎
        RobotCam->>MQTT: publish frame (JPEG/URI)
        MQTT->>Backend: forward frame topic
        Backend->>Storage: store frame (async)
        Backend->>WS: emit frame metadata/URL
        WS-->>UI: push frame payload
        UI-->>UI: 更新された映像を表示
    end
```

### 7.3 状態監視とデータロギング
```mermaid
sequenceDiagram
    participant User
    participant UI as Database Tab
    participant API as FastAPI Datalogger
    participant Repo as DatasetRepository
    participant Storage as Image Storage

    User->>UI: 開始ボタン
    UI->>API: POST /datalogger/session
    API->>Repo: create session(status=running)
    loop 収集中
        MQTT->>API: push telemetry
        API->>Storage: store image (if any)
        API->>Repo: persist telemetry (selected fields)
    end
    User->>UI: 終了ボタン
    alt 保存して終了
        UI->>API: POST /datalogger/session/{id}/save
        API->>Repo: mark session saved
    else 保存せず終了
        UI->>API: POST /datalogger/session/{id}/discard
        API->>Repo: delete session + files
    end
```

### 7.4 ナビゲーション指示
```mermaid
sequenceDiagram
    participant User
    participant UI as React Nav Panel
    participant API as FastAPI Router
    participant MQTT
    participant Robot

    User->>UI: 目的地選択
    UI->>API: POST /robot/navigation
    API->>MQTT: publish robot/cmd/navigation
    MQTT-->>Robot: send goal
    Robot-->>MQTT: publish progress + state
    MQTT-->>API: forward status
    API-->>UI: REST/WS update
```

### 7.5 機械学習トレーニング
```mermaid
sequenceDiagram
    participant User
    participant UI as ML Tab
    participant API as FastAPI ML Router
    participant Tasks as Task Queue
    participant Trainer as PyTorch Worker
    participant WS as WS Gateway

    User->>UI: トレーニング開始
    UI->>API: POST /ml/train
    API->>Tasks: enqueue training job
    Tasks->>Trainer: start run
    loop 各エポック
        Trainer->>WS: emit metrics(epoch, loss)
        WS-->>UI: stream metrics
        UI-->>User: グラフ更新
    end
    Trainer->>API: mark run completed
    API-->>UI: 更新完了通知
```

### 7.6 Chatbot (RAG 質問応答)
```mermaid
sequenceDiagram
    participant User
    participant UI as Chatbot Tab
    participant API as Chatbot Router
    participant Vector as Vector DB
    participant LLM

    User->>UI: 質問入力
    UI->>API: POST /chat/query
    API->>Vector: similarity search (top-k)
    Vector-->>API: relevant documents
    API->>LLM: prompt with context
    LLM-->>API: streaming answer tokens
    API-->>UI: WS/HTTP chunk push
    UI-->>User: レスポンス表示 + 参照リンク
```

## 8. 非機能要件
- **リアルタイム性**: 制御系は <100ms 以内の往復を目標。
- **耐障害性**: MQTT 再接続ロジック、WS バックオフ、データ保存時の ACID 保証。
- **スケーラビリティ**: フロントエンドは CDN, バックエンドはコンテナスケール、MQTT ブローカはクラスタリング。
- **セキュリティ**: JWT/OAuth2, ロールベースアクセス制御, TLS 終端。
- **観測性**: OpenTelemetry 対応、構成変更の監査ログ。

## 9. セキュリティと監視
- **認証/認可**: Keycloak or Cognito, Role (Operator, Analyst, Admin)。
- **ネットワーク**: MQTT over TLS, WebSocket w/ Secure cookies, CORS ホワイトリスト。
- **監視**: Prometheus exporter, Grafana ダッシュボード (通信状態, ML job metrics)。
- **ログ**: 構造化 JSON, Loki 集約。

## 10. 将来的な拡張ポイント
- マルチロボット管理 (Robot ID 切替)。
- オフラインバッチ解析 (ETL pipeline)。
- Edge 推論向け Federated Learning。
- 音声インタフェースによる Chatbot 拡張。
- モバイルクライアント (React Native)。
