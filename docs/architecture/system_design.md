# Robot ML Web App – System Design

## 全体構成

```mermaid
graph TD
    FE[Vue Frontend] -- REST/WebSocket --> BE[FastAPI Backend]
    BE -- MQTT --> MQ[(Mosquitto Broker)]
    MQ -- Pub/Sub --> SIM[Unity Simulation]
    MQ -- Pub/Sub --> ROBOT[Physical Robot]
    BE -- SQLAlchemy --> DB[(PostgreSQL)]
    BE -- File I/O --> MEDIA[data/uploads/media]
    BE -- Worker --> TRAIN[PyTorch Trainer]
    BE -- Vector Store --> VS[Embeddings Store]
```

## 主要モジュール

- **フロントエンド**: Vue 3 + Vite + Pinia。タブごとのディレクトリ分割。
- **バックエンド**: FastAPI。ドメイン単位のルータ、サービス、リポジトリ層。
- **メッセージング**: MQTT ブローカーを介したロボット制御とテレメトリ。
- **データ永続化**: PostgreSQL + SQLAlchemy。画像等はファイルシステムに保存しパスのみ DB 登録。
- **機械学習**: PyTorch トレーニングワーカー (非同期キュー) と WebSocket によるメトリクス配信。
- **Chatbot**: RAG パイプライン (埋め込み + リトリーバ + LLM スタブ)。

## API レイヤ

| エンドポイント | 概要 |
| --- | --- |
| `POST /api/v1/robot/control/velocity` | ジョイスティック操作を MQTT に転送 |
| `POST /api/v1/robot/control/navigation` | ナビゲーション指示 |
| `GET /api/v1/telemetry/sessions` | テレメトリセッション一覧 |
| `POST /api/v1/telemetry/sessions` | セッション開始 |
| `PATCH /api/v1/telemetry/sessions/{id}` | ステータス更新 |
| `POST /api/v1/ml/jobs` | 学習ジョブ登録 |
| `GET /api/v1/ml/jobs` | ジョブ一覧 |
| `POST /api/v1/chatbot/query` | Chatbot への質問 |
| `POST /api/v1/simulation/start` | Unity シミュレーション起動 |
| `POST /api/v1/simulation/stop` | Unity シミュレーション停止 |

## WebSocket チャネル

- `/ws/robot`: ロボット状態・カメラストリーム通知
- `/ws/telemetry`: テレメトリイベント
- `/ws/training`: 学習メトリクス
- `/ws/chatbot`: 将来拡張用

## データベース概要

```mermaid
classDiagram
    class RobotDevice {
        UUID id
        string name
        string identifier
        enum kind
        bool is_active
    }
    class TelemetrySession {
        UUID id
        UUID device_id
        string name
        enum status
        bool capture_velocity
        bool capture_state
        bool capture_images
        json session_metadata
    }
    class TelemetryRecord {
        UUID id
        UUID session_id
        datetime timestamp
        float linear_velocity_x
        float linear_velocity_y
        float angular_velocity_z
        json state
        string notes
    }
    class MediaAsset {
        UUID id
        UUID session_id
        UUID record_id
        enum asset_type
        string file_path
        string checksum
    }
    class TrainingJob {
        UUID id
        string name
        enum status
        json config
        json dataset_session_ids
        string model_path
    }
    class TrainingMetric {
        UUID id
        UUID job_id
        int epoch
        int step
        string metric_name
        float metric_value
    }
    class ChatDocument {
        UUID id
        string source_type
        string title
        string content
        json embedding
        json metadata
    }
    RobotDevice --> TelemetrySession
    TelemetrySession --> TelemetryRecord
    TelemetrySession --> MediaAsset
    TrainingJob --> TrainingMetric
```

## シーケンス図

### ジョイスティック制御

```mermaid
sequenceDiagram
    participant FE as Vue
    participant WS as WebSocket
    participant API as FastAPI
    participant MQTT as Broker
    participant BOT as Robot
    FE->>WS: {vx, vy, omega}
    WS->>API: publish velocity
    API->>MQTT: cmd/velocity
    MQTT->>BOT: cmd/velocity
    BOT-->>MQTT: state/camera
    MQTT-->>API: telemetry
    API-->>WS: push state frames
    WS-->>FE: update UI
```

### テレメトリ保存

```mermaid
sequenceDiagram
    participant FE as Vue
    participant API as FastAPI
    participant Repo as TelemetryRepository
    participant Storage as MediaManager
    FE->>API: start session
    API->>Repo: insert session
    loop incoming data
        API->>Repo: buffer record
        API->>Storage: save media
    end
    FE->>API: stop session
    API->>Repo: update status
```

### ML 学習

```mermaid
sequenceDiagram
    participant FE as Vue
    participant API as FastAPI
    participant Worker
    participant Trainer
    participant WS as WebSocket
    FE->>API: create job
    API->>Worker: enqueue
    Worker->>Trainer: run epochs
    loop each epoch
        Trainer->>API: log metric
        API->>WS: broadcast
        WS->>FE: update chart
    end
    Trainer->>API: mark complete
```

## フォルダ構成ポリシー

- タブ別 (`robot-control`, `database`, `ml`, `chatbot`) にフロントエンドを分離
- バックエンドは `api` / `services` / `repositories` / `infrastructure` のレイヤ構成
- 追加モジュールは `infrastructure` 以下にまとめ、外部依存を隔離
- テストは `tests/unit`, `tests/integration`, `tests/e2e`

## 今後の課題

1. MQTT 実装を paho-mqtt 等で本結線
2. トレーニングワーカーを Celery/RQ や asyncio キューに統合
3. ベクターストア(Qdrant/FAISS)連携とドキュメントインジェストパイプライン
4. 認証・認可の導入
5. CI/CD と監視の整備