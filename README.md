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
- **リアルタイム監視**: WebSocket/MQTTによる状態更新
- **マルチベンダー対応**: Adapterパターンによる異なるメーカーのロボット統合
- **認証・認可**: JWT認証とRBACによるアクセス制御

### 技術スタック

| コンポーネント | 技術 |
|--------------|------|
| Backend | Python 3.11, FastAPI 0.109, SQLAlchemy 2.0, gRPC |
| Gateway | Go 1.21, gRPC, MQTT |
| Frontend | Next.js 14, React 18, TypeScript, TanStack Query |
| Database | PostgreSQL 15, Redis 7 |
| Message Broker | Eclipse Mosquitto (MQTT) |
| Container | Docker, Docker Compose |

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│                   (Next.js + React)                          │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST API / WebSocket
┌─────────────────────────▼───────────────────────────────────┐
│                        Backend                               │
│                       (FastAPI)                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │   Auth   │  │  Robots  │  │ Missions │  │   Logs   │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────┬───────────────────────────────────┘
                          │ gRPC
┌─────────────────────────▼───────────────────────────────────┐
│                     Fleet Gateway                            │
│                     (Go + gRPC)                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │   FSM    │  │ Adapters │  │   MQTT   │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────┬───────────────────────────────────┘
                          │ MQTT
┌─────────────────────────▼───────────────────────────────────┐
│                        Robots                                │
│           (Various Vendors via Adapter Pattern)              │
└─────────────────────────────────────────────────────────────┘
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

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
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
| Gateway (gRPC) | localhost:50051 | Fleet Gateway gRPC |
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

詳細なAPI仕様は http://localhost:8000/docs (Swagger UI) で確認できます。

## 🛠️ 開発ガイド

### プロジェクト構造

```
amr-saas-platform/
├── backend/                 # FastAPI バックエンド
│   ├── app/
│   │   ├── auth/           # 認証モジュール
│   │   ├── models/         # SQLAlchemy モデル
│   │   ├── routers/        # APIエンドポイント
│   │   ├── schemas/        # Pydantic スキーマ
│   │   ├── services/       # ビジネスロジック
│   │   ├── config.py       # 設定
│   │   ├── database.py     # DB接続
│   │   └── main.py         # アプリケーション
│   ├── requirements.txt
│   └── Dockerfile
├── gateway/                 # Go Fleet Gateway
│   ├── cmd/gateway/        # エントリーポイント
│   ├── proto/              # Protocol Buffers定義
│   ├── internal/
│   │   ├── adapter/        # ベンダーアダプター
│   │   ├── grpc/           # gRPCサーバー
│   │   ├── config/         # 設定
│   │   ├── mqtt/           # MQTTクライアント
│   │   └── robot/          # ロボット管理・FSM
│   ├── go.mod
│   └── Dockerfile
├── frontend/                # Next.js フロントエンド
│   ├── src/
│   │   ├── app/            # App Router ページ
│   │   ├── components/     # UIコンポーネント
│   │   ├── hooks/          # カスタムフック
│   │   ├── lib/            # ユーティリティ
│   │   └── types/          # TypeScript型定義
│   ├── package.json
│   └── Dockerfile
├── docker/                  # Docker設定
├── scripts/                 # ユーティリティスクリプト
├── .github/workflows/       # CI/CD
├── docker-compose.yml
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
