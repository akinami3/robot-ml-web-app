# Robot AI Web Application

ロボットのリアルタイム操作・センサ情報可視化・データ収集・RAG機能を提供するプロダクションレベルのWebアプリケーション。

## アーキテクチャ概要

```
┌─────────────┐   WebSocket(WSS)  ┌──────────────┐   Adapter I/F    ┌──────────┐
│  Frontend   │◄─────────────────►│   Gateway    │◄────────────────►│  Robots  │
│  (React)    │                   │   (Go)       │  Plugin System   │          │
└──────┬──────┘                   └──────┬───────┘                  └──────────┘
       │ REST API (HTTPS)                │ Redis Streams / gRPC
       ▼                                 ▼
┌──────────────┐              ┌──────────────┐
│   Backend    │◄─────────────│    Redis     │
│  (FastAPI)   │  Subscribe   │  (Streams)   │
└──────┬───────┘              └──────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│  PostgreSQL (TimescaleDB + pgvector) │
└──────────────────────────────────────┘
       ▲
       │ HTTP API
┌──────┴───────┐
│   Ollama     │
│  (Llama 3)   │
└──────────────┘
```

![](./docs/system-architecture.drawio.svg)

## 技術スタック

| 領域 | 技術 |
|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS + shadcn/ui |
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2.0 + Alembic |
| Gateway | Go 1.23 + gorilla/websocket + MessagePack |
| Database | PostgreSQL 16 + TimescaleDB + pgvector |
| Cache/Broker | Redis 7 (Streams) |
| LLM | Ollama + Llama 3 |
| CI/CD | GitHub Actions |
| Container | Docker + Docker Compose |
| Docs | MkDocs (Material for MkDocs) |

## 前提条件

- **Docker** >= 24.0 & **Docker Compose** >= 2.20
- **Git** >= 2.40
- (開発時のみ) Node.js >= 20, Python >= 3.12, Go >= 1.23

## クイックスタート

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd robot-ml-web-app
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# .env を編集して必要な値を設定（特にパスワード類）
```

### 3. JWT用RSA鍵の生成

```bash
mkdir -p keys
openssl genrsa -out keys/private.pem 2048
openssl rsa -in keys/private.pem -pubout -out keys/public.pem
```

### 4. 起動（開発モード）

```bash
# 全サービス起動
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# docker compose (V2 plugin) が使えない場合は docker-compose (standalone) を使用
# docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# ログ確認
docker compose logs -f

# DBマイグレーション（初回のみ）
docker compose exec backend alembic upgrade head

# Ollama に Llama 3 モデルをダウンロード（初回のみ）
docker compose exec ollama ollama pull llama3
docker compose exec ollama ollama pull nomic-embed-text
```

### 5. アクセス

| サービス | 本番 URL | 開発 URL |
|---|---|---|
| Frontend | http://localhost:3000 | http://localhost:5173 |
| Backend API | http://localhost:8000/api/v1 | http://localhost:8000/api/v1 |
| Backend Docs (Swagger) | http://localhost:8000/docs | http://localhost:8000/docs |
| Gateway WebSocket | ws://localhost:8080/ws | ws://localhost:8080/ws |
| PostgreSQL | - | localhost:15432 |
| Redis | - | localhost:16379 |
| MkDocs (設計書) | http://localhost:8888 | (要 `mkdocs serve`) |

### 6. 初期ユーザー登録・ログイン

1. ブラウザで Frontend URL にアクセス
2. ログイン画面の "Sign up" リンクをクリック
3. ユーザー名、メールアドレス、パスワードを入力してアカウント作成
4. 登録後、自動的にログインされます

または、APIで直接ユーザー登録も可能です：

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "email": "admin@example.com", "password": "changeme123"}'
```

## 開発ガイド

### ディレクトリ構成

```
robot-ml-web-app/
├── frontend/          # React + TypeScript (Vite)
├── backend/           # FastAPI (Python)
├── gateway/           # Go WebSocket Gateway
├── proto/             # 共通 Protocol Buffers 定義
├── docs/              # MkDocs 設計書
├── scripts/           # ユーティリティスクリプト
├── deploy/            # デプロイ設定 (k8s, nginx)
├── docker-compose.yml         # 基本構成
├── docker-compose.dev.yml     # 開発用オーバーライド
├── docker-compose.prod.yml    # 本番用オーバーライド
└── .github/workflows/         # CI/CD
```

### 個別サービスの開発

#### Frontend

```bash
cd frontend
npm install
npm run dev          # 開発サーバー起動 (http://localhost:5173)
npm run test         # ユニットテスト
npm run lint         # リント
npm run build        # ビルド
```

#### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest                # テスト
ruff check .         # リント
mypy .               # 型チェック
```

#### Gateway

```bash
cd gateway
go mod download
go run cmd/gateway/main.go
go test ./...          # テスト
golangci-lint run      # リント
```

### DBマイグレーション

```bash
# マイグレーション作成
docker compose exec backend alembic revision --autogenerate -m "description"

# マイグレーション実行
docker compose exec backend alembic upgrade head

# ロールバック
docker compose exec backend alembic downgrade -1
```

### Proto定義の更新

```bash
./scripts/generate-proto.sh
```

### テスト

```bash
# 全テスト実行
./scripts/test.sh

# 個別
./scripts/test.sh frontend
./scripts/test.sh backend
./scripts/test.sh gateway
```

### DBバックアップ

```bash
./scripts/backup-db.sh
```

### OSSライセンス一覧生成

```bash
./scripts/generate-licenses.sh
```

## 主要機能

### 🕹️ 手動操作
- 仮想ジョイスティック / WASDキーボード操作
- リアルタイム速度指令送信 (WebSocket)
- 操作排他制御 (1ロボット1ユーザー)

### 🗺️ ナビゲーション操作
- 地図上でのゴール位置指定
- パス表示・ナビステータス
- ウェイポイント設定

### 📊 センサ情報可視化
- LiDAR点群 (Three.js 3D表示)
- カメラストリーム
- IMU 3D可視化
- 時系列グラフ (Recharts)

### 💾 データ収集・ML
- センサ種別単位で保存対象を選択
- 記録開始/停止制御
- データセットエクスポート (CSV/Parquet)

### 🤖 RAG (Retrieval-Augmented Generation)
- ドキュメントアップロード (PDF/MD/TXT)
- Local LLM (Llama 3) による回答生成
- センサデータメタデータの自動RAGソース化

### 🛡️ 安全機能
- 緊急停止 (E-Stop) — 全画面常時表示、WebSocket+REST二重経路
- 操作タイムアウト — 無操作時自動停止
- 速度制限 — 設定値超過時の自動クランプ
- 監査ログ — 全操作の改ざん不可能な記録

## 新しいロボットの追加方法

Gateway の Adapter インターフェースを実装することで新しいロボットプロトコルを追加できます。
詳細は [新ロボット追加ガイド](docs/docs/guides/adding-robot.md) を参照してください。

## 設計書

```bash
cd docs
pip install mkdocs-material mkdocs-mermaid2-plugin
mkdocs serve -a 0.0.0.0:8888
```

http://localhost:8888 で設計書を閲覧できます。

## トラブルシューティング

### Docker Compose が起動しない

```bash
# Docker デーモンの確認
sudo systemctl status docker

# ポート競合の確認
sudo lsof -i :3000
sudo lsof -i :8000
sudo lsof -i :8080

# クリーンスタート
docker compose down -v
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

### Ollama モデルのダウンロードが遅い

```bash
# 直接Ollamaコンテナ内で確認
docker compose exec ollama ollama list
docker compose exec ollama ollama pull llama3 --verbose
```

### DBマイグレーションエラー

```bash
# 現在のリビジョン確認
docker compose exec backend alembic current

# 全リセット（開発環境のみ）
docker compose exec backend alembic downgrade base
docker compose exec backend alembic upgrade head
```

### WebSocket 接続が切れる

- ブラウザのDevTools → Network → WS で接続状態を確認
- Gateway のログを確認: `docker compose logs gateway -f`
- StatusBar の接続状態表示で Gateway/Robot の状態を確認

## ライセンス

MIT License - 詳細は [LICENSE](LICENSE) を参照
