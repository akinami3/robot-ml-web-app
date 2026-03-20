# Robot AI Web Application — 段階的学習カリキュラム

> **対象**: プログラミング初心者 → 中級者  
> **最終到達点**: 現在の `main` ブランチ（フルスタック構成）  
> **管理方法**: ブランチ方式（`step/01-hello-websocket`, `step/02-...`）

---

## カリキュラム全体像

```
Step  1  ──→  2  ──→  3  ──→  4  ──→  5  ──→  6  ──→  7
HTML+JS      Protocol  Adapter   Canvas    Safety   FastAPI  PostgreSQL
+ Go WS      + MsgPack Pattern   Sensors   Pipeline REST API + Alembic

Step  8  ──→  9  ──→  10  ──→  11  ──→  12  ──→  13
JWT Auth     React     React+WS   Redis     RAG      Production
RBAC         Migration Dashboard  Streams   LLM      Hardening
```

---

## 技術ロードマップ

| Step | ブランチ名 | フロントエンド | バックエンド | Gateway | インフラ |
|:----:|---|---|---|---|---|
| 1 | `step/01-hello-websocket` | Vanilla JS (1ファイル) | — | Go (最小WS) | — |
| 2 | `step/02-protocol-messages` | Vanilla JS | — | Go + Protocol層 | — |
| 3 | `step/03-adapter-pattern` | Vanilla JS (ES Modules) | — | Go + Adapter/Registry | Docker Compose (2) |
| 4 | `step/04-sensor-visualization` | Vanilla JS + Canvas | — | Go + Mock Adapter | Docker Compose (2) |
| 5 | `step/05-safety-pipeline` | Vanilla JS + E-Stop | — | Go + Safety全機能 | Docker Compose (2) |
| 6 | `step/06-rest-api` | Vanilla JS + fetch | FastAPI (in-memory) | Go | Docker Compose (3) |
| 7 | `step/07-database` | Vanilla JS | FastAPI + SQLAlchemy | Go | Docker Compose (4: +PG) |
| 8 | `step/08-authentication` | Vanilla JS + Login画面 | FastAPI + JWT | Go + Auth連携 | Docker Compose (4) |
| 9 | `step/09-react-migration` | **React + TypeScript** | FastAPI | Go | Docker Compose (4) |
| 10 | `step/10-realtime-dashboard` | React + WebSocket Hook | FastAPI | Go | Docker Compose (4) |
| 11 | `step/11-data-recording` | React + Recording UI | FastAPI + Worker | Go + Redis Pub | Docker Compose (5: +Redis) |
| 12 | `step/12-rag-system` | React + Chat UI | FastAPI + RAG | Go | Docker Compose (6: +Ollama) |
| 13 | `step/13-production` | React (Nginx) | FastAPI (Gunicorn) | Go (distroless) | Full Prod Stack |

---

## Step 1: Hello WebSocket（ブランチ: `step/01-hello-websocket`）

### 学習目標
- WebSocket の基本概念（HTTP との違い、双方向通信）
- Go 言語の基礎（main関数、パッケージ、net/http）
- HTML/JavaScript の基礎（DOM操作、イベントリスナー）

### 構成
```
step1/
├── gateway/
│   └── main.go              # 最小限のWebSocketサーバー（1ファイル）
├── frontend/
│   └── index.html            # WebSocket接続 + テキストコマンド送受信
└── README.md
```

### 作るもの
- Go: WebSocket エコーサーバー（受信メッセージに応答 + 定期的にモックデータ送信）
- HTML: テキスト入力でコマンド送信、受信メッセージをリスト表示
- **Docker不要** — `go run` と `ブラウザで直接開く` だけ

### 学ぶこと
- `gorilla/websocket` の Upgrader
- `ReadMessage` / `WriteMessage` ループ
- JavaScript の `new WebSocket()`, `onmessage`, `send()`
- ブラウザの DevTools → Network → WS タブの使い方

---

## Step 2: 構造化メッセージ（ブランチ: `step/02-protocol-messages`）

### 学習目標
- JSON によるメッセージプロトコル設計
- Go の構造体と JSON マーシャリング
- MessagePack のバイナリシリアライゼーション

### 新規追加
```
gateway/
├── main.go
└── protocol/
    ├── messages.go           # メッセージ型定義（Type, RobotID, Payload）
    └── codec.go              # JSON/MessagePack エンコード・デコード
frontend/
├── index.html
└── js/
    ├── protocol.js           # メッセージの組み立て・解析
    └── app.js                # メインロジック分離
```

### 作るもの
- 型付きメッセージ: `{ type: "velocity_cmd", payload: { linear_x: 0.5 } }`
- WASD キーボード入力 → velocity_cmd メッセージ送信
- サーバーから sensor_data メッセージ受信・表示

### 学ぶこと
- メッセージプロトコルの設計（type + payload パターン）
- Go の `json.Marshal` / `json.Unmarshal`
- JavaScript の `JSON.parse` / `JSON.stringify`
- バイナリ vs テキストプロトコルのトレードオフ

---

## Step 3: Adapter パターン（ブランチ: `step/03-adapter-pattern`）

### 学習目標
- Go のインターフェースと多態性
- デザインパターン: Adapter, Factory, Registry
- Docker Compose の基礎

### 新規追加
```
gateway/
├── cmd/gateway/main.go       # エントリーポイント分離
├── internal/
│   ├── adapter/
│   │   ├── interface.go      # RobotAdapter インターフェース
│   │   ├── registry.go       # アダプター管理
│   │   └── mock/
│   │       └── mock.go       # モックロボット
│   ├── protocol/             # Step2 から継続
│   └── server/
│       └── websocket.go      # WS サーバー分離
docker-compose.yml             # gateway + frontend(nginx)
```

### 学ぶこと
- Go インターフェースの暗黙的実装
- `cmd/` + `internal/` プロジェクトレイアウト
- `docker compose up` によるサービス起動
- ロボットを追加する拡張ポイントの理解

---

## Step 4: センサー可視化（ブランチ: `step/04-sensor-visualization`）

### 学習目標
- Canvas 2D API によるリアルタイム描画
- 複数センサーの並行表示
- ES Modules によるフロントエンド構造化

### 新規追加
```
frontend/
├── index.html
├── css/
│   └── style.css
└── js/
    ├── app.js                # メインアプリ
    ├── protocol.js
    ├── websocket-client.js   # WS接続管理クラス
    └── sensors/
        ├── lidar-viewer.js   # Canvas LiDAR描画
        ├── imu-chart.js      # IMU 簡易グラフ
        ├── battery-gauge.js  # バッテリー表示
        └── odometry.js       # 位置表示
```

### 作るもの
- Mock Adapter が 20-50Hz でセンサーデータ生成
- LiDAR: Canvas で極座標点群をリアルタイム描画
- IMU: 簡易折れ線グラフ（直近 N 件のデータ）
- バッテリー: SVG ゲージ

### 学ぶこと
- `<canvas>` の `getContext('2d')`, `requestAnimationFrame`
- 極座標 → 直交座標変換
- ES Modules (`import`/`export`)
- CSS Grid/Flexbox によるダッシュボードレイアウト

---

## Step 5: 安全パイプライン（ブランチ: `step/05-safety-pipeline`）

### 学習目標
- Go の並行処理（goroutine, channel, sync.Mutex）
- 安全設計の基本原則（フェイルセーフ）
- Hub パターン（Pub/Sub）

### 新規追加
```
gateway/internal/
├── safety/
│   ├── estop.go              # 緊急停止マネージャー
│   ├── velocity_limiter.go   # 速度制限
│   ├── timeout_watchdog.go   # タイムアウト監視
│   └── operation_lock.go     # 操作排他ロック
└── server/
    ├── hub.go                # Hub + Client 管理
    ├── handler.go            # メッセージハンドラー（安全パイプライン統合）
    └── websocket.go          # readPump / writePump 分離
```

### フロントエンド追加
- E-Stop ボタン（大きな赤いボタン、常時表示）
- 接続状態インジケーター
- 速度制限のフィードバック表示

### 学ぶこと
- `sync.RWMutex` の使い分け（読み取りロックと書き込みロック）
- Channel ベースのイベントループ（`select` 文）
- Goroutine のライフサイクル管理（`context.WithCancel`）
- ガード節パターンによる多段階バリデーション

---

## Step 6: REST API 導入（ブランチ: `step/06-rest-api`）

### 学習目標
- REST API の設計原則
- FastAPI の基礎（エンドポイント、Pydantic スキーマ）
- Docker Compose のマルチサービス構成

### 新規追加
```
backend/
├── app/
│   ├── main.py               # FastAPI アプリ
│   └── api/
│       └── v1/
│           ├── schemas.py    # Pydantic リクエスト/レスポンス
│           └── robots.py     # ロボット CRUD（in-memory）
├── pyproject.toml
└── Dockerfile.dev
docker-compose.yml             # 3サービス: frontend, backend, gateway
```

### フロントエンド追加
- ロボット一覧画面（`fetch()` API）
- ロボット登録フォーム
- 複数ページ構成（URLハッシュルーティング）

### 学ぶこと
- HTTP メソッド（GET, POST, PUT, DELETE）
- FastAPI の自動ドキュメント（/docs）
- `fetch()` API と async/await
- CORS の仕組みと設定

---

## Step 7: データベース導入（ブランチ: `step/07-database`）

### 学習目標
- リレーショナルデータベースの基礎
- SQLAlchemy 2.0 (async) ORM
- Alembic マイグレーション

### 新規追加
```
backend/app/
├── domain/
│   ├── entities/
│   │   ├── robot.py          # Robot データクラス
│   │   └── user.py           # User データクラス
│   └── repositories/
│       ├── base.py           # BaseRepository[T] ABC
│       └── robot_repo.py     # ロボットリポジトリ I/F
├── infrastructure/
│   └── database/
│       ├── connection.py     # DB接続管理
│       ├── models.py         # ORM モデル
│       └── repositories/
│           └── robot_repo.py # SQLAlchemy 実装
alembic/                       # マイグレーション
scripts/
└── init-db.sql               # DB初期化
```

### フロントエンド追加
- テーブル表示（ロボット一覧）
- 編集・削除機能

### 学ぶこと
- Clean Architecture（Entity → Repository Interface → ORM 実装）
- SQLAlchemy の `AsyncSession`, `select()`, `relationship()`
- `alembic upgrade head` / `alembic revision --autogenerate`
- UUID 主キーと TimescaleDB の概要

---

## Step 8: 認証・認可（ブランチ: `step/08-authentication`）

### 学習目標
- JWT (JSON Web Token) 認証
- パスワードハッシュ（bcrypt）
- RBAC（ロールベースアクセス制御）

### 新規追加
```
backend/app/
├── core/
│   └── security.py           # JWT生成・検証、パスワードハッシュ
├── domain/entities/
│   └── user.py               # UserRole 列挙型追加
├── api/v1/
│   ├── auth.py               # ログイン・登録・トークンリフレッシュ
│   ├── dependencies.py       # DI チェーン（認証・認可）
│   └── users.py              # ユーザー管理
keys/                          # RSA鍵ペア
```

### フロントエンド追加
- ログインページ（フォーム + fetch POST）
- サインアップページ
- localStorage でのトークン保存
- 認証ヘッダー付き API リクエスト
- ロール別メニュー表示/非表示

### 学ぶこと
- JWT の構造（Header.Payload.Signature）
- RS256 と HS256 の違い
- bcrypt のソルティング
- FastAPI `Depends()` による DI チェーン
- `require_role()` 高階関数

---

## Step 9: React 移行（ブランチ: `step/09-react-migration`）

### 学習目標
- React + TypeScript の基礎
- Vite ビルドツール
- コンポーネント設計と状態管理

### 変更内容
```
frontend/                      # 全面書き換え
├── src/
│   ├── main.tsx              # エントリーポイント（Provider構成）
│   ├── App.tsx               # React Router ルーティング
│   ├── components/
│   │   ├── layout/           # AppLayout, Sidebar
│   │   └── ui/               # Button, Card, Input（primitives）
│   ├── pages/
│   │   ├── LoginPage.tsx     # Step8 のログインを React 化
│   │   ├── SignupPage.tsx
│   │   ├── DashboardPage.tsx # ロボット一覧
│   │   └── SettingsPage.tsx
│   ├── services/
│   │   └── api.ts            # Axios + インターセプター
│   ├── stores/
│   │   └── authStore.ts      # Zustand 認証ストア
│   ├── types/
│   │   └── index.ts          # 型定義
│   └── lib/
│       └── utils.ts          # ユーティリティ
├── package.json
├── vite.config.ts
├── tsconfig.json
└── tailwind.config.js
```

### 学ぶこと
- JSX と仮想 DOM
- `useState`, `useEffect`, `useCallback`, `useRef`
- React Router v6（ネストルーティング、ProtectedRoute）
- Zustand（Redux との比較）
- TanStack Query（サーバー状態管理）
- Tailwind CSS + shadcn/ui パターン

### 💡 Vanilla JS → React 移行のポイント
| Vanilla JS | React |
|---|---|
| `document.getElementById()` | `useRef()` |
| `addEventListener()` | `onClick`, `onChange` |
| `innerHTML =` | JSX による宣言的 UI |
| グローバル変数 | `useState` / Zustand |
| `fetch()` 直接呼び出し | `useQuery` / Axios |
| URL ハッシュルーティング | React Router |

---

## Step 10: リアルタイムダッシュボード（ブランチ: `step/10-realtime-dashboard`）

### 学習目標
- React カスタムフック設計
- WebSocket + React の統合
- リアルタイム UI 更新パターン

### 新規追加
```
frontend/src/
├── hooks/
│   ├── useWebSocket.ts       # WS接続管理（自動再接続、ハートビート）
│   └── useKeyboardControl.ts # WASD キーボード制御
├── components/
│   ├── robot/
│   │   ├── EStopButton.tsx   # 緊急停止ボタン
│   │   ├── JoystickController.tsx # 仮想ジョイスティック
│   │   └── StatusBar.tsx     # 接続状態バー
│   └── sensors/
│       ├── LiDARViewer.tsx   # Canvas LiDAR（React版）
│       ├── IMUChart.tsx      # Recharts グラフ
│       ├── BatteryGauge.tsx  # バッテリーゲージ
│       └── OdometryDisplay.tsx
├── pages/
│   ├── ManualControlPage.tsx # ジョイスティック + キーボード
│   ├── SensorViewPage.tsx    # センサー一覧
│   └── NavigationPage.tsx    # ナビゲーション目標設定
└── stores/
    └── robotStore.ts         # ロボット状態ストア
```

### 学ぶこと
- `useWebSocket` の設計（接続、再接続、ハートビート）
- `useRef` vs `useState` の使い分け（リアルタイムデータ）
- `useCallback` によるメモ化の重要性
- Canvas コンポーネントの `useEffect` ライフサイクル

---

## Step 11: データ記録（ブランチ: `step/11-data-recording`）

### 学習目標
- Redis Streams（Pub/Sub + Consumer Group）
- バックグラウンドワーカー
- TimescaleDB 時系列データ

### 新規追加
```
gateway/internal/
└── bridge/
    └── redis_publisher.go    # Gateway → Redis Streams (XADD)

backend/app/
├── domain/
│   ├── entities/
│   │   ├── sensor_data.py
│   │   ├── recording.py
│   │   └── dataset.py
│   ├── repositories/
│   │   ├── sensor_data_repo.py
│   │   ├── recording_repo.py
│   │   └── dataset_repo.py
│   └── services/
│       ├── recording_service.py
│       └── dataset_service.py
├── infrastructure/
│   ├── redis/
│   │   ├── connection.py
│   │   └── recording_worker.py  # Redis Streams → PostgreSQL
│   └── database/repositories/
│       ├── sensor_data_repo.py  # TimescaleDB time_bucket
│       ├── recording_repo.py
│       └── dataset_repo.py
└── api/v1/
    ├── recordings.py
    ├── datasets.py
    └── sensors.py

frontend/src/pages/
└── DataManagementPage.tsx     # 記録開始/停止、データセット管理
```

### 学ぶこと
- Redis Streams の `XADD` / `XREADGROUP` / `XACK`
- Consumer Group パターン
- TimescaleDB の hypertable と `time_bucket()`
- バックグラウンドタスクのライフサイクル管理

---

## Step 12: RAG システム（ブランチ: `step/12-rag-system`）

### 学習目標
- RAG (Retrieval-Augmented Generation) パイプライン
- ベクトル検索（pgvector + HNSW）
- SSE (Server-Sent Events) ストリーミング

### 新規追加
```
backend/app/
├── domain/
│   ├── entities/
│   │   └── document.py
│   ├── repositories/
│   │   └── rag_repo.py       # チャンク検索 I/F
│   └── services/
│       └── rag_service.py    # TextSplitter + Protocol based DI
├── infrastructure/
│   ├── llm/
│   │   ├── ollama_client.py  # Ollama HTTP API
│   │   └── embedding.py      # nomic-embed-text
│   └── database/repositories/
│       └── rag_repo.py       # pgvector cosine similarity
└── api/v1/
    └── rag.py                # Upload + Query + SSE Stream

frontend/src/pages/
└── RAGChatPage.tsx            # チャット UI + ファイルアップロード
```

### 学ぶこと
- 文書チャンキング（段落認識、オーバーラップ）
- Embedding（テキスト → ベクトル変換）
- pgvector の `<=>` (cosine distance) と HNSW インデックス
- SSE ストリーミング（Fetch API の ReadableStream）
- Python `Protocol`（構造的部分型）による DI

---

## Step 13: プロダクション品質（ブランチ: `step/13-production` → `main` にマージ）

### 学習目標
- マルチステージ Docker ビルド
- Nginx リバースプロキシ
- CI/CD パイプライン
- 本番環境のセキュリティ

### 新規追加・変更
```
# Dockerfile の本番化
frontend/Dockerfile            # Multi-stage: node → nginx:alpine
backend/Dockerfile             # Multi-stage: python → python:slim
gateway/Dockerfile             # Multi-stage: golang → distroless

# Nginx
frontend/nginx.conf            # リバースプロキシ + SPA fallback + gzip

# Docker Compose
docker-compose.prod.yml        # リソース制限、ログローテーション
docker-compose.dev.yml         # ホットリロード、ポート公開

# CI/CD
.github/workflows/
├── ci.yml                     # lint → test → build
├── cd-staging.yml             # ステージングデプロイ
└── cd-production.yml          # 本番デプロイ

# 監査・ログ
backend/app/
├── core/logging.py            # structlog 構造化ログ
├── domain/
│   ├── entities/audit.py      # 監査ログエンティティ
│   └── services/audit_service.py
└── api/v1/audit.py

# その他
scripts/                       # 運用スクリプト一式
docs/                          # MkDocs 設計文書 + ADR
proto/                         # Protocol Buffers 定義
```

### 学ぶこと
- Multi-stage ビルド（イメージサイズ削減）
- distroless コンテナ（攻撃面の最小化）
- GitHub Actions ワークフロー構文
- 構造化ログ（structlog / zap）
- 監査ログの不変性設計

---

## 各ステップの使い方

### ブランチの切り替え

```bash
# Step 1 から始める
git checkout step/01-hello-websocket

# Step 5 に進む
git checkout step/05-safety-pipeline

# 最終版（現在の main）
git checkout main
```

### 差分で学ぶ

```bash
# Step 2 で何が追加されたか確認
git diff step/01-hello-websocket..step/02-protocol-messages --stat

# Step 9 の React 移行で変わったファイルを確認
git diff step/08-authentication..step/09-react-migration -- frontend/
```

### 各ステップの起動方法

各ブランチの README.md に起動手順が記載されています。  
Step 1-2 は `go run` + ブラウザ直接、Step 3 以降は `docker compose up`。

---

## 推奨学習フロー

1. **README を読む** — そのステップの学習目標を確認
2. **前ステップとの差分を見る** — `git diff` で追加されたファイルを把握
3. **コードを読む** — 各ファイルのコメントが解説になっている
4. **動かしてみる** — サーバー起動、ブラウザで操作
5. **改造してみる** — 課題（README末尾）に取り組む
6. **次のステップへ** — ブランチを切り替え
