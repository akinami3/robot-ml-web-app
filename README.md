# Step 7: データベース導入 🗄️

> **ブランチ**: `step/07-database`
> **前のステップ**: `step/06-rest-api`
> **次のステップ**: `step/08-authentication`

---

## このステップで学ぶこと

1. **リレーショナルデータベース** — PostgreSQL の基礎、SQL
2. **ORM（Object-Relational Mapping）** — SQLAlchemy 2.0 の非同期モード
3. **Clean Architecture** — ドメイン層（Entity / Repository Interface）とインフラ層の分離
4. **マイグレーション** — Alembic によるスキーマバージョン管理
5. **依存性注入（DI）** — FastAPI の `Depends()` チェーン

---

## 概要

Step 6 のインメモリ CRUD を **PostgreSQL + SQLAlchemy** で永続化するステップ。
Clean Architecture に基づき、ドメイン層（Entity + Repository Interface）と
インフラ層（SQLAlchemy ORM 実装）を明確に分離する。
Alembic でデータベーススキーマのバージョン管理を行い、
Docker Compose に PostgreSQL を追加して 4 サービス構成にする。

---

## 学習ポイント

### Clean Architecture の層構造

```
┌─────────────────────────────────┐
│  API 層         (robots.py)     │  ← HTTP リクエスト受付
├─────────────────────────────────┤
│  ドメイン層                      │
│    Entity       (robot.py)      │  ← ビジネスオブジェクト（dataclass）
│    Repository   (robot_repo.py) │  ← 抽象インターフェース（ABC）
├─────────────────────────────────┤
│  インフラ層                      │
│    ORM Model    (models.py)     │  ← SQLAlchemy マッピング
│    Repository   (robot_repo.py) │  ← 具象実装（SQL 発行）
│    Connection   (connection.py) │  ← DB接続管理
└─────────────────────────────────┘
```

### SQLAlchemy 2.0 の特徴
- `AsyncSession` による非同期 DB アクセス
- `select()` 関数スタイルのクエリ構築
- `mapped_column()` による型安全なカラム定義
- `relationship()` でリレーション定義

### Alembic マイグレーション
- `alembic revision --autogenerate` — モデル変更からマイグレーション自動生成
- `alembic upgrade head` — 最新スキーマに更新
- `alembic downgrade -1` — 1 つ前に戻す
- バージョン管理でチーム開発のスキーマ変更を安全に管理

### 依存性注入チェーン
```python
# FastAPI の Depends() で DB セッション → リポジトリ → エンドポイントに注入
async def get_db() -> AsyncSession: ...
async def get_robot_repo(db = Depends(get_db)) -> RobotRepository: ...
async def list_robots(repo = Depends(get_robot_repo)): ...
```

---

## ファイル構成

```
backend/
  app/
    config.py                              ← 🆕 設定管理（DATABASE_URL 等）
    main.py                                ← lifespan + DB 接続管理
    domain/
      __init__.py
      entities/
        __init__.py
        robot.py                           ← 🆕 Robot エンティティ（dataclass）
        user.py                            ← 🆕 User エンティティ
      repositories/
        __init__.py
        base.py                            ← 🆕 BaseRepository[T] 抽象基底
        robot_repo.py                      ← 🆕 RobotRepository インターフェース
    infrastructure/
      __init__.py
      database/
        __init__.py
        connection.py                      ← 🆕 AsyncEngine + セッション管理
        models.py                          ← 🆕 SQLAlchemy ORM モデル
        repositories/
          __init__.py
          robot_repo.py                    ← 🆕 SQLAlchemy 具象実装
    api/v1/
      dependencies.py                      ← 🆕 依存性注入
      robots.py                            ← インメモリ → Repository パターン
      schemas.py
  alembic/                                 ← 🆕 マイグレーション
    env.py
    versions/
  alembic.ini                              ← 🆕 Alembic 設定
  pyproject.toml                           ← sqlalchemy, asyncpg, alembic 追加

scripts/
  init-db.sql                              ← 🆕 DB 初期化スクリプト

docker-compose.yml                         ← 4 サービス構成（+PostgreSQL）
```

---

## 起動方法

```bash
docker compose up --build
```

4つのサービスが起動する:

| サービス | ポート | 説明 |
|----------|--------|------|
| frontend | 3000 | Nginx |
| backend | 8000 | FastAPI + SQLAlchemy |
| gateway | 8080 | WebSocket |
| postgres | 5432 | PostgreSQL |

### マイグレーション実行

```bash
# コンテナ内でマイグレーション
docker compose exec backend alembic upgrade head
```

---

## Step 6 からの主な変更

| カテゴリ | 変更内容 |
|----------|----------|
| DB | PostgreSQL サービス追加 |
| ORM | SQLAlchemy 2.0（async）導入 |
| 設計 | Clean Architecture（Entity / Repository / ORM 分離） |
| DI | FastAPI Depends() チェーン |
| マイグレーション | Alembic によるスキーマ管理 |
| ストレージ | インメモリ → PostgreSQL 永続化 |
| ファイル数 | 24 files changed, +1,609 / -330 |

---

## 🏋️ チャレンジ課題

1. **新しいエンティティを追加**: `Command` エンティティを作り、ロボットへの操作履歴を記録してみよう
2. **マイグレーションを試そう**: モデルにカラムを追加 → `alembic revision --autogenerate` → `alembic upgrade head`
3. **リレーションを追加**: Robot に `commands` リレーションを設定し、操作履歴を取得できるようにしよう
4. **psql で確認**: `docker compose exec postgres psql -U robot_user -d robot_db` でデータを直接確認

---

## 次のステップへ

Step 8 では **JWT 認証** と **RBAC（ロールベースアクセス制御）** を追加します:

```bash
git checkout step/08-authentication
```
