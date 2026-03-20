# Step 6: REST API 導入 🌐

> **ブランチ**: `step/06-rest-api`
> **前のステップ**: `step/05-safety-pipeline`
> **次のステップ**: `step/07-database`

---

## このステップで学ぶこと

1. **REST API 設計原則** — リソース指向 + HTTP メソッド（GET / POST / PUT / DELETE）
2. **FastAPI の基礎** — エンドポイント、Pydantic スキーマ、自動ドキュメント（/docs）
3. **CORS** — 異なるオリジン間のリクエスト許可の仕組み
4. **fetch() API** — ブラウザ組み込みの HTTP クライアントと async/await
5. **SPA ルーティング** — ハッシュ（#）による擬似ページ遷移
6. **Docker Compose 3 サービス構成** — frontend + backend + gateway

---

## 概要

Python FastAPI によるバックエンド API サーバーを新たに追加し、
ロボット情報の CRUD（作成・取得・更新・削除）をインメモリで実装するステップ。
フロントエンドにはページルーターと `fetch()` API クライアントを組み込み、
ロボット一覧・登録フォーム・リアルタイム制御の 3 ページ構成にする。

---

## 学習ポイント

### REST API 設計
| メソッド | エンドポイント | 役割 |
|----------|--------------|------|
| GET | `/api/v1/robots` | ロボット一覧取得 |
| GET | `/api/v1/robots/{id}` | ロボット詳細取得 |
| POST | `/api/v1/robots` | ロボット登録 |
| PATCH | `/api/v1/robots/{id}` | ロボット更新 |
| DELETE | `/api/v1/robots/{id}` | ロボット削除 |

### FastAPI の特徴
- **型ヒント** → リクエスト/レスポンスの自動バリデーション
- **Pydantic スキーマ** → `RobotCreate`, `RobotUpdate`, `RobotResponse`
- **自動ドキュメント** → http://localhost:8000/docs でインタラクティブに動作確認
- **CORS ミドルウェア** → フロントエンド（:3000）からの API 呼び出しを許可

### フロントエンドの進化
- **ハッシュルーター**: `#/robots`, `#/robots/new`, `#/control` でページ切り替え
- **fetch() ラッパー**: 共通ヘッダー、エラーハンドリング、JSON パース
- **宣言的なページ**: robot-list.js, robot-form.js, control.js にロジック分離

---

## ファイル構成

```
backend/                          ← 🆕 新規サービス
  app/
    __init__.py
    main.py                       ← FastAPI アプリ（CORS, ルーター, ヘルスチェック）
    api/
      __init__.py
      v1/
        __init__.py
        schemas.py                ← Pydantic スキーマ
        robots.py                 ← Robot CRUD エンドポイント（インメモリ）
  pyproject.toml                  ← Python プロジェクト設定
  Dockerfile.dev                  ← 開発用 Dockerfile（uvicorn --reload）

frontend/
  index.html                      ← ナビバー + ルーターコンテナ
  css/
    style.css                     ← テーブル、フォーム、ナビバーのスタイル追加
  js/
    app.js                        ← ルーター統合 + センサー遅延初期化
    api.js                        ← 🆕 REST API クライアント（fetch ラッパー）
    router.js                     ← 🆕 ハッシュルーター（SPA ページ切り替え）
    pages/
      robot-list.js               ← 🆕 ロボット一覧ページ
      robot-form.js               ← 🆕 ロボット登録/編集フォーム
      control.js                  ← 🆕 リアルタイム制御ページ（Step 5 内容を分離）
    sensors/                      ← Step 4 から継続
    protocol.js
    protocol-base.js
    websocket-client.js

gateway/                          ← Step 5 から継続
docker-compose.yml                ← 3 サービス構成に変更
```

---

## 起動方法

```bash
docker compose up --build
```

3つのサービスが起動する:

| サービス | URL | 説明 |
|----------|-----|------|
| frontend | http://localhost:3000 | Nginx で配信 |
| backend | http://localhost:8000 | FastAPI（自動ドキュメント: /docs） |
| gateway | ws://localhost:8080 | WebSocket サーバー |

### 試してみる

1. http://localhost:3000 を開く → ロボット一覧（空）
2. 「新規登録」からロボットを追加
3. 一覧に戻って登録されたことを確認
4. 「制御」ページで WebSocket 経由のセンサー表示
5. http://localhost:8000/docs で API ドキュメントを確認

---

## Step 5 からの主な変更

| カテゴリ | 変更内容 |
|----------|----------|
| バックエンド | FastAPI サーバー新規追加（Python） |
| API | ロボット CRUD エンドポイント（インメモリ） |
| フロント | ハッシュルーター + 3 ページ構成 |
| Docker | 3 サービス構成（frontend + backend + gateway） |
| ファイル数 | 17 files changed, +2,203 / -404 |

---

## 🏋️ チャレンジ課題

1. **新しいフィールドを追加**: ロボットに `description` フィールドを追加してみよう
2. **/docs を使ってみよう**: FastAPI の Swagger UI から直接 API を呼んでみる
3. **エラーハンドリング**: 存在しない ID で GET するとどうなる？ 404 を返すように改良しよう
4. **検索機能**: ロボット名でフィルタリングする GET パラメータを追加してみよう

---

## 次のステップへ

Step 7 では **PostgreSQL** データベースを導入し、インメモリから永続化に移行します:

```bash
git checkout step/07-database
```
