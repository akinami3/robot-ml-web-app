# Step 11: データ記録・管理 📼

> **ブランチ**: `step/11-data-recording`
> **前のステップ**: `step/10-realtime-dashboard`
> **次のステップ**: `step/12-rag-system`

---

## このステップで学ぶこと

1. **Redis Streams** — `XADD` / `XREADGROUP` / `XACK` によるメッセージキューイング
2. **Consumer Group パターン** — 並列データ処理の基礎
3. **バックグラウンドワーカー** — asyncio ライフサイクル管理
4. **TimescaleDB** — 時系列データの hypertable と `time_bucket()`
5. **JSONB / ARRAY カラム** — 柔軟なスキーマ設計

---

## 概要

センサーデータの記録・管理基盤を構築するステップ。
Gateway が WebSocket で受信したセンサーデータを **Redis Streams** に XADD し、
バックエンドの **バックグラウンドワーカー** が Consumer Group で読み取り、
PostgreSQL（TimescaleDB）に永続化する。
記録セッション（Recording）の開始/停止とデータセット（Dataset）の管理機能も実装する。

---

## アーキテクチャ

```
┌──────────┐    WebSocket    ┌──────────┐    XADD     ┌──────────┐
│ ブラウザ   │◄──────────────►│ Gateway  │────────────►│  Redis   │
│           │                │ (Go)     │             │ Streams  │
└──────────┘                └──────────┘             └────┬─────┘
                                                          │ XREADGROUP
┌──────────┐    REST API     ┌──────────┐                 │
│ フロント   │───────────────►│ Backend  │◄────────────────┘
│ React     │◄───────────────│ (Python) │
└──────────┘                │          │    INSERT
                             │ Worker   │──────────►┌────────────┐
                             └──────────┘           │ PostgreSQL │
                                                    │ TimescaleDB│
                                                    └────────────┘
```

---

## 学習ポイント

### Redis Streams

```
# Gateway → Redis（データ送信）
XADD sensor:data * robot_id "mock-001" type "lidar" data "{...}"

# Worker → Redis（データ受信、Consumer Group）
XREADGROUP GROUP sensor-workers worker-1 COUNT 100 BLOCK 5000 STREAMS sensor:data >
XACK sensor:data sensor-workers <message-id>
```

- **XADD**: ストリームにメッセージを追加
- **XREADGROUP**: Consumer Group でメッセージを読み取り
- **XACK**: 処理完了の確認応答

### Recording セッションの状態遷移

```
  ┌───── POST /start ──────┐
  │                        ▼
[idle] ─────────────► [recording] ─── POST /{id}/stop ──► [completed]
```

### エンドポイント一覧

| メソッド | エンドポイント | 役割 |
|----------|--------------|------|
| POST | `/api/v1/recordings/start` | 記録開始 |
| POST | `/api/v1/recordings/{id}/stop` | 記録停止 |
| GET | `/api/v1/recordings` | 記録セッション一覧 |
| GET | `/api/v1/datasets` | データセット一覧 |
| POST | `/api/v1/datasets` | データセット作成 |
| DELETE | `/api/v1/datasets/{id}` | データセット削除 |
| GET | `/api/v1/sensors/latest` | 最新センサーデータ |

---

## ファイル構成

```
gateway/
  internal/
    bridge/
      redis_publisher.go              ← 🆕 Redis Streams XADD パブリッシャー
    server/
      websocket.go                    ← Redis publish 連携追加
  cmd/gateway/
    main.go                           ← RedisPublisher 初期化
  go.mod                              ← go-redis/v9 依存追加

backend/
  app/
    main.py                           ← api_router 統合、Worker ライフサイクル
    domain/
      entities/
        sensor_data.py                ← 🆕 SensorData エンティティ
        recording.py                  ← 🆕 RecordingSession エンティティ
        dataset.py                    ← 🆕 Dataset エンティティ
        audit_log.py                  ← 🆕 AuditLog エンティティ
      repositories/
        sensor_data_repo.py           ← 🆕 SensorDataRepository
        recording_repo.py             ← 🆕 RecordingRepository
        dataset_repo.py               ← 🆕 DatasetRepository
        audit_log_repo.py             ← 🆕 AuditLogRepository
      services/
        recording_service.py          ← 🆕 記録セッション管理
        dataset_service.py            ← 🆕 データセット管理
        audit_service.py              ← 🆕 監査ログ記録
    infrastructure/
      redis/
        connection.py                 ← 🆕 Redis 接続管理
        recording_worker.py           ← 🆕 Stream Consumer ワーカー
      database/
        models.py                     ← SensorData, Recording, Dataset モデル追加
        repositories/
          sensor_data_repo.py         ← 🆕 TimescaleDB time_bucket
          recording_repo.py           ← 🆕 SQLAlchemy 実装
          dataset_repo.py             ← 🆕 SQLAlchemy 実装
          audit_log_repo.py           ← 🆕 SQLAlchemy 実装
    api/v1/
      router.py                       ← 🆕 統合ルーター
      recordings.py                   ← 🆕 記録エンドポイント
      datasets.py                     ← 🆕 データセットエンドポイント
      sensors.py                      ← 🆕 センサーエンドポイント
    core/
      logging.py                      ← 🆕 structlog 構造化ログ
  pyproject.toml                      ← redis, structlog 依存追加

frontend/src/
  pages/
    DataManagementPage.tsx            ← 🆕 データ管理 UI
  services/
    api.ts                            ← recordingApi, datasetApi, sensorApi 追加
  types/
    index.ts                          ← Recording, Dataset 型定義追加
  App.tsx                             ← /data ルート追加
  components/layout/Sidebar.tsx       ← Data Management ナビ追加

docker-compose.yml                    ← 5 サービス構成（+Redis）
```

---

## 起動方法

```bash
docker compose up --build
```

| サービス | ポート | 説明 |
|----------|--------|------|
| frontend | 3000 | Vite 開発サーバー |
| backend | 8000 | FastAPI + Worker |
| gateway | 8080 | WebSocket + Redis Publisher |
| postgres | 5432 | PostgreSQL |
| redis | 6379 | Redis Streams |

### 試してみる

1. ログイン後、サイドバー「データ管理」を開く
2. 「記録開始」をクリック → センサーデータの記録が開始
3. しばらく待って「記録停止」→ セッションが保存される
4. データセットを作成して記録データをグループ化

---

## Step 10 からの主な変更

| カテゴリ | 変更内容 |
|----------|----------|
| Gateway | Redis Streams へのセンサーデータ XADD |
| Backend | バックグラウンドワーカー（Consumer Group） |
| DB | SensorData, Recording, Dataset テーブル追加 |
| API | 記録・データセット・センサーの REST エンドポイント |
| フロント | DataManagementPage 追加 |
| インフラ | Redis サービス追加（5 サービス構成） |
| ファイル数 | 50 files changed, +7,231 / -150 |

---

## 🏋️ チャレンジ課題

1. **Redis CLI で確認**: `docker compose exec redis redis-cli XLEN sensor:data` でストリーム長を確認
2. **Consumer Group を観察**: `XINFO GROUPS sensor:data` でグループ情報を確認
3. **データのエクスポート**: CSV 形式でセンサーデータをダウンロードする API を追加
4. **データの可視化**: 記録データから時系列グラフを描画するページを追加

---

## 次のステップへ

Step 12 では **RAG（検索拡張生成）** システムを構築し、ドキュメントに基づいた LLM 回答を実現します:

```bash
git checkout step/12-rag-system
```
