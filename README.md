# Step 13: プロダクション品質 🚀

> **ブランチ**: `step/13-production`
> **前のステップ**: `step/12-rag-system`
> **次のステップ**: — （最終ステップ → `main` にマージ）

---

## このステップで学ぶこと

1. **Multi-stage Docker ビルド** — ビルド環境と実行環境の分離でイメージ軽量化
2. **Nginx リバースプロキシ** — SPA + API + WebSocket を統合配信
3. **Docker Compose オーバーレイ** — 開発用・本番用の構成切り替え
4. **CI/CD パイプライン** — GitHub Actions による自動テスト・ビルド・デプロイ
5. **Protocol Buffers** — 言語に依存しないメッセージフォーマット定義
6. **運用スクリプト** — バックアップ、マイグレーション、セットアップの自動化
7. **設計文書** — ADR（Architecture Decision Records）による技術選定の記録

---

## 概要

全 12 ステップで構築したアプリケーションを本番運用可能な品質に仕上げる最終ステップ。
Docker イメージの最適化、Nginx リバースプロキシ、CI/CD パイプライン、
運用スクリプト、設計文書、Protocol Buffers 定義など、
プロダクション環境に必要なインフラ・運用コードを一通り追加する。

---

## 学習ポイント

### Multi-stage Docker ビルド

```dockerfile
# Stage 1: ビルド（大きい）
FROM golang:1.22 AS builder
RUN go build -o /app

# Stage 2: 実行（小さい）
FROM gcr.io/distroless/static
COPY --from=builder /app /app
```

| サービス | ビルドイメージ | 実行イメージ | 効果 |
|----------|-------------|-------------|------|
| Frontend | node:20 | nginx:alpine | ~900MB → ~30MB |
| Backend | python:3.12 | python:3.12-slim | ~1.2GB → ~200MB |
| Gateway | golang:1.22 | distroless/static | ~800MB → ~10MB |

### Nginx リバースプロキシ

```
ブラウザ → Nginx (:80)
              ├── /            → SPA (静的ファイル)
              ├── /api/        → Backend (:8000)
              └── /ws          → Gateway (:8080) ← WebSocket Upgrade
```

- SPA フォールバック（全パス → index.html）
- gzip 圧縮（テキスト系ファイル）
- セキュリティヘッダー（X-Frame-Options, CSP 等）

### Docker Compose オーバーレイ

```bash
# 開発環境（HMR、デバッグポート、ボリュームマウント）
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# 本番環境（リソース制限、ログローテーション、Gunicorn）
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### CI/CD パイプライン（GitHub Actions）

```
Push / PR
    │
    ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│  Lint   │───►│  Test   │───►│  Build  │
│ (各言語) │    │ (単体)   │    │ (Docker)│
└─────────┘    └─────────┘    └────┬────┘
                                    │
                              ┌─────▼─────┐
                              │  Deploy    │
                              │ (Staging/  │
                              │  Prod)     │
                              └───────────┘
```

---

## ファイル構成

```
# Docker 最適化
frontend/Dockerfile            ← Multi-stage: Node → Nginx:alpine
frontend/nginx.conf            ← リバースプロキシ + SPA + gzip + セキュリティ
backend/Dockerfile             ← Multi-stage: Python → Python:slim
gateway/Dockerfile             ← Multi-stage: Go → distroless

# Docker Compose
docker-compose.yml             ← ベース構成（6 サービス）
docker-compose.dev.yml         ← 🆕 開発用オーバーレイ
docker-compose.prod.yml        ← 🆕 本番用オーバーレイ

# CI/CD
.github/workflows/
  ci.yml                       ← lint → test → build
  cd-staging.yml               ← ステージングデプロイ
  cd-production.yml            ← 本番デプロイ

# Protocol Buffers
proto/
  command.proto                ← 🆕 速度・ナビ・ロボットコマンド定義
  gateway_service.proto        ← 🆕 gRPC サービス定義
  sensor.proto                 ← 🆕 センサーデータメッセージ定義

# 運用スクリプト
scripts/
  setup.sh                    ← 🆕 初期セットアップ
  dev.sh                      ← 🆕 開発環境起動
  test.sh                     ← 🆕 全サービステスト
  migrate.sh                  ← 🆕 Alembic マイグレーション管理
  backup-db.sh                ← 🆕 PostgreSQL バックアップ + ローテーション
  generate-proto.sh           ← 🆕 Protobuf コード生成
  generate-licenses.sh        ← 🆕 OSS ライセンススキャン

# 設計文書（MkDocs）
docs/
  mkdocs.yml                  ← ドキュメントサイト設定
  docs/
    index.md                  ← トップページ
    adr/                      ← 技術選定記録（ADR）
      001-frontend-framework.md
      002-backend-framework.md
      003-gateway-language.md
      004-database.md
      005-local-llm.md
    api/                      ← API ドキュメント
      rest-api.md
      grpc.md
      websocket.md
    architecture/             ← アーキテクチャ概要
      overview.md
      data-flow.md
      safety.md
    deployment/               ← デプロイメントガイド
      docker.md
      production.md

# Backend 更新
backend/
  app/main.py                 ← v1.0.0
  pyproject.toml              ← gunicorn 依存追加、v1.0.0
  alembic/                    ← マイグレーションテンプレート + 初期スキーマ
  app/infrastructure/grpc/    ← 🆕 gRPC クライアントプレースホルダー
  app/core/logging.py         ← structlog 構造化ログ

# Gateway 更新
gateway/.air.toml             ← 🆕 Go ホットリロード設定
```

---

## 起動方法

### 開発環境

```bash
# スクリプトを使う場合
./scripts/dev.sh

# 直接起動する場合
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### 本番環境

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

| 項目 | 開発環境 | 本番環境 |
|------|---------|---------|
| フロントエンド | Vite HMR (3000) | Nginx (80) |
| バックエンド | uvicorn --reload | Gunicorn + Uvicorn Workers |
| ホットリロード | ✅ | ❌ |
| デバッグポート | ✅ 公開 | ❌ 非公開 |
| リソース制限 | なし | メモリ・CPU 制限あり |
| ログ | コンソール出力 | ログローテーション |

---

## Step 12 からの主な変更

| カテゴリ | 変更内容 |
|----------|----------|
| Docker | Multi-stage ビルド（3 サービス全て） |
| Nginx | リバースプロキシ + SPA + gzip + セキュリティ |
| Compose | 開発用・本番用オーバーレイ |
| CI/CD | GitHub Actions（lint, test, build, deploy） |
| Proto | Protocol Buffers メッセージ・サービス定義 |
| 運用 | 7 つの運用スクリプト |
| 文書 | MkDocs + ADR + API ドキュメント |
| ファイル数 | 45 files changed, +17,505 / -35 |

---

## 🎉 カリキュラム完了！

13 ステップを通じて、以下の技術スタックを段階的に学習しました:

| レイヤー | 技術 |
|----------|------|
| フロントエンド | HTML → Canvas → React + TypeScript + Tailwind |
| バックエンド | — → FastAPI + SQLAlchemy + JWT + RAG |
| Gateway | Go WebSocket → Adapter → Safety → Redis Pub |
| データベース | — → PostgreSQL + pgvector + TimescaleDB |
| キャッシュ | — → Redis Streams |
| AI/ML | — → Ollama + Embedding + RAG |
| インフラ | go run → Docker Compose → CI/CD + Nginx |

### 次のステップ（発展課題）

- 本物のロボット（ROS 2）との接続
- Kubernetes へのデプロイ
- 負荷テスト（k6 / locust）
- E2E テスト（Playwright）
- モニタリング（Prometheus + Grafana）
