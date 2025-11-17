# Robot ML Web App

FastAPI + Vue を用いたロボット遠隔操作・テレメトリ収集・学習パイプライン・RAG チャットボットを統合する Web アプリケーションのモノレポ土台です。

## 構成

- `backend/` – FastAPI ベースの API / WebSocket サーバー、MQTT ブリッジ、PyTorch トレーニングワーカー
- `frontend/` – Vue 3 + Vite による SPA。タブごとの分離構造
- `docs/` – 設計ドキュメント
- `docker/` – 開発用コンテナ定義
- `data/` – メディア・モデル・シードデータの保管場所
- `tests/` – E2E / 負荷テストの雛形
- `scripts/` – 起動補助スクリプト

## 必要要件

- Python 3.11+
- Node.js 20+
- Docker (任意: コンテナで動かす場合)

## 開発手順 (概要)

1. 依存関係をインストール
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -e .[dev]
   cd frontend && npm install
   ```
2. 環境変数を設定 `.env` を `.env.example` からコピー
3. バックエンドを起動
   ```bash
   uvicorn app.main:app --reload --app-dir backend
   ```
4. フロントエンドを起動
   ```bash
   cd frontend
   npm run dev
   ```

## 今後の TODO

- MQTT 実装を実ブローカー接続に置き換え
- PyTorch トレーニングジョブの本実装
- RAG チャットボットのベクターストア連携
- CI/CD と自動テストの整備
