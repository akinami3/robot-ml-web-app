# robot-ml-web-app


# シーケンス図

backend <-> robot間の初期接続時の流れを示します。

```
「backend <-> robot間」はMQTT brokerを介してMQTT通信を行いますが、以下シーケンス図では、brokerを省略しています。
```

```mermaid
sequenceDiagram
  actor user as user
  participant frontend
  participant backend as AMR_API_Bridge<br>(backend)
  participant robot as robot (real or sim)

  alt　速度指令受信時
    backend ->> robot: AMR速度（並進速度、回転速度）<br>トピック名：/amr/<AMR_ID>/velocity
    robot ->> robot: 速度情報に従って、AMRが移動
  end

  par
    loop 定周期
      robot ->> robot: 現在位置を取得
      robot ->> backend: AMR状態（位置、姿勢など）<br>トピック名：/amr/<AMR_ID>/status
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
| 2 | [AMR状態](#amr状態) | /amr/<AMR_ID>/status | Robot → Backend | 1 | なし | - |

### 各トピック詳細

```
各payloadは説明用にJSONC形式（コメント付きJSON）で記述していますが、実際の実装では、JSON形式で記述する必要があることに注意してください。
```

#### AMR速度指令

AMRに対する速度指令を送信します。

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

AMRの現在の状態を送信します。  

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
  - [トピック仕様](#トピック仕様)
    - [トピック一覧](#トピック一覧)
    - [各トピック詳細](#各トピック詳細)
      - [AMR速度指令](#amr速度指令)
      - [AMR状態](#amr状態)
  - [目次](#目次)
  - [0. ディレクトリ構成](#0-ディレクトリ構成)
    - [0.1 全体構成](#01-全体構成)
    - [0.2 フロントエンド詳細](#02-フロントエンド詳細)
    - [0.3 バックエンド詳細](#03-バックエンド詳細)
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
  - [7.7 バックエンド内 - Robot API 変換フロー](#77-バックエンド内---robot-api-変換フロー)
  - [7.8 バックエンド内 - センサデータ取得・保存フロー](#78-バックエンド内---センサデータ取得保存フロー)
  - [7.9 バックエンド内 - ML トレーニングと データ連携](#79-バックエンド内---ml-トレーニングと-データ連携)
  - [7.10 バックエンド内 - Chatbot 質問応答フロー](#710-バックエンド内---chatbot-質問応答フロー)
  - [7.11 バックエンド内 - データ層 統合ビュー](#711-バックエンド内---データ層-統合ビュー)
  - [8. 非機能要件](#8-非機能要件)
  - [9. セキュリティと監視](#9-セキュリティと監視)
  - [10. 将来的な拡張ポイント](#10-将来的な拡張ポイント)

## 0. ディレクトリ構成

### 0.1 全体構成

```
robot-ml-web-app/
├── frontend/                       # React フロントエンド
│   ├── public/
│   ├── src/
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/                        # FastAPI バックエンド
│   ├── app/
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── Dockerfile
├── mqtt-broker/                    # Mosquitto MQTT ブローカー
│   └── mosquitto.conf
├── docker-compose.yml              # 全サービス統合起動
├── README.md                       # このファイル
└── docs/                          # ドキュメント
    ├── API_SPEC.md
    ├── DEPLOYMENT.md
    └── TROUBLESHOOTING.md
```

### 0.2 フロントエンド詳細

```
frontend/src/
├── app/
│   ├── App.tsx                     # メインアプリケーションコンポーネント
│   ├── Router.tsx                  # タブナビゲーション
│   ├── store/                      # Redux/Zustand 状態管理
│   │   ├── slices/
│   │   │   ├── robotSlice.ts
│   │   │   ├── mlSlice.ts
│   │   │   ├── telemetrySlice.ts
│   │   │   └── chatSlice.ts
│   │   └── index.ts
│   ├── hooks/
│   │   ├── useWebSocket.ts         # WebSocket カスタムフック
│   │   ├── useConnectionStatus.ts  # 接続状態監視
│   │   └── useAsync.ts
│   └── api/
│       ├── axiosConfig.ts          # axios インスタンス
│       ├── robotApi.ts
│       ├── mlApi.ts
│       ├── telemetryApi.ts
│       └── chatbotApi.ts
│
├── modules/                        # タブ毎の独立モジュール
│   │
│   ├── robot-control/
│   │   ├── components/
│   │   │   ├── JoystickPanel.tsx
│   │   │   ├── RobotStatus.tsx
│   │   │   ├── VideoStream.tsx
│   │   │   ├── NavigationMap.tsx
│   │   │   └── SimulationToggle.tsx
│   │   ├── hooks/
│   │   │   └── useRobotControl.ts
│   │   ├── services/
│   │   │   └── robotService.ts
│   │   └── index.tsx               # タブのエントリポイント
│   │
│   ├── database/
│   │   ├── components/
│   │   │   ├── DataLoggerControl.tsx
│   │   │   ├── SessionList.tsx
│   │   │   ├── DataPreview.tsx
│   │   │   └── SessionStatus.tsx
│   │   ├── hooks/
│   │   │   └── useDataLogger.ts
│   │   ├── services/
│   │   │   └── dataloggerService.ts
│   │   └── index.tsx
│   │
│   ├── ml/
│   │   ├── components/
│   │   │   ├── TrainingControl.tsx
│   │   │   ├── HyperparameterForm.tsx
│   │   │   ├── MetricsChart.tsx
│   │   │   ├── TrainingHistory.tsx
│   │   │   └── ModelComparison.tsx
│   │   ├── hooks/
│   │   │   └── useMLTraining.ts
│   │   ├── services/
│   │   │   └── mlService.ts
│   │   └── index.tsx
│   │
│   └── chatbot/
│       ├── components/
│       │   ├── ChatWindow.tsx
│       │   ├── MessageList.tsx
│       │   ├── QueryInput.tsx
│       │   ├── DocumentPreview.tsx
│       │   └── ChatHistory.tsx
│       ├── hooks/
│       │   └── useChatbot.ts
│       ├── services/
│       │   └── chatbotService.ts
│       └── index.tsx
│
├── shared/
│   ├── components/
│   │   ├── Header.tsx              # ヘッダー（共通）
│   │   ├── TabNav.tsx              # タブナビゲーション
│   │   ├── ConnectionStatus.tsx    # 接続ステータスインジケータ
│   │   ├── LoadingSpinner.tsx
│   │   └── ErrorBoundary.tsx
│   ├── icons/                      # SVG アイコン
│   │   ├── RobotIcon.tsx
│   │   ├── DatabaseIcon.tsx
│   │   ├── MLIcon.tsx
│   │   ├── ChatIcon.tsx
│   │   ├── WifiIcon.tsx
│   │   └── MqttIcon.tsx
│   ├── layouts/
│   │   ├── AppLayout.tsx           # 全体レイアウト
│   │   └── TabLayout.tsx           # タブ内レイアウト
│   ├── utils/
│   │   ├── formatters.ts           # データフォーマット関数
│   │   ├── validators.ts           # 入力検証
│   │   ├── constants.ts            # 定数
│   │   └── logger.ts               # クライアント側ログ
│   ├── types/
│   │   ├── robot.ts                # ロボット制御型定義
│   │   ├── telemetry.ts            # センサデータ型定義
│   │   ├── ml.ts                   # ML型定義
│   │   ├── chat.ts                 # チャット型定義
│   │   └── api.ts                  # API通信型定義
│   └── styles/
│       ├── globals.css
│       └── theme.css
│
├── index.tsx                       # エントリポイント
└── vite-env.d.ts
```

### 0.3 バックエンド詳細

```
backend/app/
├── main.py                         # FastAPI アプリケーション初期化
├── core/
│   ├── __init__.py
│   ├── config.py                   # 環境変数、設定管理
│   ├── logging.py                  # ロギング設定
│   ├── dependencies.py             # 依存性注入
│   ├── exceptions.py               # カスタム例外
│   └── security.py                 # JWT, OAuth2 設定
│
├── api/
│   ├── __init__.py
│   ├── router.py                   # API 統一ルーター
│   │
│   ├── robot_api/                  # 1️⃣ Robot API 変換
│   │   ├── __init__.py
│   │   ├── router.py               # POST /robot/velocity, /navigation
│   │   ├── schemas.py              # VelocityCommand, NavigationGoal
│   │   └── models.py               # (オプション) ローカルモデル
│   │
│   ├── telemetry/                  # 3️⃣ センサデータ取得・保存
│   │   ├── __init__.py
│   │   ├── router.py               # POST /datalogger/session, GET /sessions
│   │   ├── schemas.py              # TelemetryLog, SessionConfig
│   │   └── models.py
│   │
│   ├── ml/                         # 2️⃣ 機械学習
│   │   ├── __init__.py
│   │   ├── router.py               # POST /ml/train, GET /ml/runs/{id}
│   │   ├── schemas.py              # TrainingConfig, MetricSnapshot
│   │   └── models.py
│   │
│   └── chatbot/                    # 4️⃣ Chatbot
│       ├── __init__.py
│       ├── router.py               # POST /chat/query, GET /chat/history
│       ├── schemas.py              # QueryRequest, ChatResponse
│       └── models.py
│
├── services/                       # ビジネスロジック層（役割別分離）
│   ├── __init__.py
│   ├── robot_control.py            # RobotControlService
│   │                               # - set_velocity()
│   │                               # - send_navigation()
│   │                               # - toggle_simulation()
│   │
│   ├── telemetry_processor.py      # TelemetryProcessorService
│   │                               # - handle_mqtt_message()
│   │                               # - preprocess_data()
│   │
│   ├── datalogger.py               # DataLoggerService
│   │                               # - start_session()
│   │                               # - save_session()
│   │                               # - discard_session()
│   │
│   ├── ml_pipeline.py              # MLPipelineService
│   │                               # - launch_training()
│   │                               # - stream_metrics()
│   │                               # - stop_training()
│   │
│   └── chatbot_engine.py           # ChatbotService
│                                   # - retrieve_context()
│                                   # - generate_response()
│
├── repositories/                   # データアクセス層（DB/Storage操作）
│   ├── __init__.py
│   ├── base.py                     # BaseRepository
│   ├── robot_state.py              # RobotStateRepository
│   ├── sensor_data.py              # SensorDataRepository
│   │                               # - create(), list_by_session()
│   │                               # - export_for_training()
│   │
│   ├── training_runs.py            # TrainingRunRepository
│   │                               # - create_run(), update_metrics()
│   │
│   ├── training_metrics.py         # TrainingMetricRepository
│   │
│   └── rag_documents.py            # RAGDocumentRepository
│                                   # - index_document(), search()
│
├── models/                         # SQLAlchemy ORM モデル
│   ├── __init__.py
│   ├── robot_state.py              # RobotState テーブル
│   ├── sensor_data.py              # SensorData テーブル
│   ├── dataset_session.py          # DatasetSession テーブル
│   ├── training_run.py             # TrainingRun テーブル
│   ├── training_metric.py          # TrainingMetric テーブル
│   └── rag_document.py             # RAGDocument テーブル
│
├── adapters/                       # 外部システム統合（プロトコル、SDK抽象化）
│   ├── __init__.py
│   ├── mqtt_client.py              # MQTTClientAdapter
│   │                               # - publish(), subscribe_with_callback()
│   │
│   ├── websocket_manager.py        # WebSocketHub
│   │                               # - broadcast_to_channel()
│   │                               # - send_to_client()
│   │
│   ├── storage_client.py           # StorageClient
│   │                               # - upload_image(), download_file()
│   │
│   ├── vector_store.py             # VectorStoreAdapter
│   │                               # - index_document(), similarity_search()
│   │
│   └── llm_client.py               # LLMClientAdapter
│                                   # - generate(), stream_response()
│
├── workers/                        # 非同期タスク（Celery/RQ）
│   ├── __init__.py
│   ├── tasks.py                    # @celery.task デコレータタスク
│   │                               # - train_model_task()
│   │                               # - process_batch_telemetry()
│   │
│   └── celery_app.py               # Celery アプリ初期化
│
├── schemas/                        # Pydantic スキーマ（集約）
│   ├── __init__.py
│   ├── robot.py                    # VelocityCommand など
│   ├── telemetry.py                # TelemetryLog など
│   ├── ml.py                       # TrainingConfig など
│   └── chat.py                     # QueryRequest など
│
├── utils/
│   ├── __init__.py
│   ├── validators.py               # 入力検証関数
│   ├── formatters.py               # データフォーマット
│   ├── logger.py                   # ログ設定
│   ├── constants.py                # 定数
│   └── helpers.py                  # ヘルパー関数
│
├── database/
│   ├── __init__.py
│   ├── session.py                  # SQLAlchemy セッション管理
│   ├── engine.py                   # DB エンジン初期化
│   └── migrations/                 # Alembic マイグレーション
│       ├── versions/
│       └── env.py
│
├── websocket/
│   ├── __init__.py
│   ├── manager.py                  # WebSocket接続管理
│   ├── handlers.py                 # メッセージハンドラ
│   └── subscriptions.py            # チャネル購読管理
│
├── jobs/                           # 長時間実行ジョブ
│   ├── __init__.py
│   ├── training_job.py             # PyTorch学習実行
│   ├── data_export_job.py          # データ抽出
│   └── rag_indexing_job.py         # Vector DB インデックス
│
├── config/
│   ├── __init__.py
│   ├── settings.py                 # Pydantic Settings
│   └── secrets.py                  # シークレット管理
│
└── tests/
    ├── __init__.py
    ├── conftest.py                 # pytest フィクスチャ
    ├── test_robot_api.py
    ├── test_ml_service.py
    ├── test_telemetry.py
    ├── test_chatbot.py
    └── integration/
        └── test_end_to_end.py
```

---

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

## 7.7 バックエンド内 - Robot API 変換フロー

```mermaid
sequenceDiagram
    participant Frontend
    participant Router as API Router<br>(robot_api/)
    participant Service as RobotControlService
    participant Adapter as MQTTClientAdapter
    participant WS as WebSocketHub
    participant Robot

    Frontend->>Router: POST /robot/velocity
    Router->>Router: バリデーション
    Router->>Service: set_velocity(VelocityCommand)
    Service->>Adapter: publish(/amr/*/velocity)
    Adapter->>Robot: MQTT送信
    Robot-->>Adapter: /amr/*/status応答
    Adapter-->>Service: telemetry callback
    Service->>WS: broadcast(robot_state)
    WS-->>Frontend: WebSocket更新
```

**役割:**
- **Router**: HTTP リクエスト受け取り、スキーマチェック
- **Service**: ビジネスロジック（速度制限、割り込み判定など）
- **Adapter**: MQTT プロトコル操作、再接続管理

---

## 7.8 バックエンド内 - センサデータ取得・保存フロー

```mermaid
sequenceDiagram
    participant MQTT as MQTT Broker
    participant Listener as MQTTClientAdapter
    participant Service as TelemetryProcessorService
    participant Logger as DataLoggerService
    participant Storage as ImageStorage
    participant DB as SQLDatabase
    participant Repo as SensorDataRepository

    loop 定周期 (10Hz)
        MQTT->>Listener: /amr/*/status
        Listener->>Service: handle_telemetry(message)
        alt セッション進行中
            Service->>Logger: append_to_session(id, data)
            Logger->>Storage: save_image_async(image_path)
            Logger->>Repo: persist_telemetry(session_id, fields)
            Repo->>DB: INSERT INTO sensor_data
        else セッション未開始
            Service-->>Service: drop message
        end
    end
```

**役割:**
- **MQTTClientAdapter**: リアルタイム購読、コールバック呼び出し
- **TelemetryProcessorService**: データ前処理（フィルタ、型変換）
- **DataLoggerService**: セッション単位での蓄積管理
- **SensorDataRepository**: DB 永続化ロジック

---

## 7.9 バックエンド内 - ML トレーニングと データ連携

```mermaid
sequenceDiagram
    participant Frontend
    participant Router as API Router<br>(ml/)
    participant Service as MLPipelineService
    participant TaskQueue as Celery Task Queue
    participant Worker as PyTorch Worker
    participant Repo as DatasetRepository<br>+TrainingRunRepository
    participant DB as SQLDatabase
    participant WS as WebSocketHub

    Frontend->>Router: POST /ml/train
    Router->>Service: launch_training(config)
    Service->>Repo: get_dataset(session_id)
    Repo->>DB: SELECT * FROM sensor_data
    DB-->>Repo: telemetry rows + image paths
    Repo-->>Service: Dataset object
    Service->>TaskQueue: enqueue(training_job)
    TaskQueue-->>Service: job_id
    Service-->>Frontend: ✅ Training started
    
    par 非同期実行
        loop 各エポック
            Worker->>Worker: 学習ステップ実行
            Worker->>Repo: update_metrics(run_id, epoch, loss, acc)
            Repo->>DB: INSERT INTO training_metric
            DB-->>Repo: ✅
            Worker->>WS: emit_metric(run_id, epoch, loss)
            WS-->>Frontend: WebSocket配信
        end
        Worker->>Repo: finalize_run(run_id, status=completed)
    end
```

**役割:**
- **MLPipelineService**: トレーニング設定、キューイング、進捗監視
- **DatasetRepository**: 保存済みセンサデータを Dataset に変換
- **Worker (Celery)**: GPU/CPU 上で実際の学習実行
- **TrainingRunRepository**: メトリクス記録、ハイパーパラメータ管理

---

## 7.10 バックエンド内 - Chatbot 質問応答フロー

```mermaid
sequenceDiagram
    participant Frontend
    participant Router as API Router<br>(chatbot/)
    participant Service as ChatbotService
    participant VectorStore as VectorStoreAdapter<br>(Qdrant)
    participant Repo as RAGDocumentRepository
    participant LLMClient as LLMClientAdapter
    participant DB as SQLDatabase

    Frontend->>Router: POST /chat/query
    Router->>Service: generate_response(query)
    
    Service->>VectorStore: similarity_search(query, k=5)
    VectorStore->>DB: vector search
    DB-->>VectorStore: top-k documents
    VectorStore-->>Service: relevant_docs
    
    Service->>Repo: get_document_context(doc_ids)
    Repo->>DB: SELECT content FROM rag_document
    DB-->>Repo: full content
    Repo-->>Service: context
    
    Service->>LLMClient: generate(prompt + context)
    LLMClient-->>Service: streaming tokens
    
    par ストリーミング配信
        loop 各トークン
            Service->>Frontend: WebSocket配信
            Frontend-->>Frontend: incremental表示
        end
    end
```

**役割:**
- **ChatbotService**: クエリ解釈、コンテキスト構築、LLM オーケストレーション
- **VectorStoreAdapter**: 意味的検索、Vector DB 操作
- **RAGDocumentRepository**: 検索結果のメタデータ・内容取得
- **LLMClientAdapter**: OpenAI/Anthropic API 呼び出し、ストリーミング管理

---

## 7.11 バックエンド内 - データ層 統合ビュー

```mermaid
graph TB
    subgraph API["API/Router層"]
        RobotRouter["robot_api/router"]
        MLRouter["ml/router"]
        TelemetryRouter["telemetry/router"]
        ChatRouter["chatbot/router"]
    end
    
    subgraph Service["Service層 (ビジネスロジック)"]
        RobotService["RobotControlService"]
        MLService["MLPipelineService"]
        TelemetryService["TelemetryProcessorService"]
        LoggerService["DataLoggerService"]
        ChatService["ChatbotService"]
    end
    
    subgraph Repository["Repository層 (データアクセス)"]
        SensorRepo["SensorDataRepository"]
        TrainingRepo["TrainingRunRepository"]
        RAGRepo["RAGDocumentRepository"]
    end
    
    subgraph Adapter["Adapter層 (外部統合)"]
        MQTT["MQTTClientAdapter"]
        WS["WebSocketHub"]
        Storage["StorageClient"]
        VectorDB["VectorStoreAdapter"]
        LLM["LLMClientAdapter"]
    end
    
    subgraph DB["Persistence"]
        SQL["SQL Database"]
        ObjectStorage["Image/Video Storage"]
        Vector["Vector DB"]
    end
    
    RobotRouter-->RobotService
    MLRouter-->MLService
    TelemetryRouter-->TelemetryService
    TelemetryService-->LoggerService
    ChatRouter-->ChatService
    
    RobotService-->MQTT
    RobotService-->WS
    TelemetryService-->MQTT
    LoggerService-->SensorRepo
    LoggerService-->Storage
    MLService-->SensorRepo
    MLService-->TrainingRepo
    ChatService-->VectorDB
    ChatService-->LLM
    
    SensorRepo-->SQL
    TrainingRepo-->SQL
    RAGRepo-->SQL
    Storage-->ObjectStorage
    VectorDB-->Vector
    LLM-->LLM
```

**層の責任分離:**
- **API層**: HTTP 受け取り、入力チェック
- **Service層**: ビジネスロジック、複数 Repository/Adapter の調整
- **Repository層**: SQL 操作、SQL-ORM マッピング
- **Adapter層**: プロトコル/SDK 操作の抽象化
- **Persistence層**: 実データ保存先

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
