# Robot ML Web Application

ロボット制御、データ収集、機械学習、チャットボットを統合したWebアプリケーション

## 🚀 Features

### 🤖 ロボット制御
- リアルタイムジョイスティック制御
- カメラフィード表示
- ロボットステータス監視
- ナビゲーション機能
- Unity/実機の切り替え対応

### 💾 データベース画面
- ロボットデータのリアルタイム記録
- 選択的データ保存（チェックボックス）
- 画像の効率的な保存（ファイルシステム）
- 記録制御（開始/一時停止/保存/破棄/終了）

### 🧠 機械学習
- PyTorchによる学習パイプライン
- リアルタイム学習曲線表示
- データセット管理
- モデル評価機能

### 💬 チャットボット
- RAG（Retrieval-Augmented Generation）
- LLM統合
- Webアプリに関するQA機能

## 🏗️ Technology Stack

### Frontend
- **Framework**: Vue.js 3 (Composition API + TypeScript)
- **Build Tool**: Vite
- **State Management**: Pinia
- **UI Library**: TailwindCSS (optional)
- **Charts**: Chart.js / ECharts

### Backend
- **Framework**: FastAPI (Python 3.10+)
- **ORM**: SQLAlchemy
- **Migration**: Alembic
- **Async**: asyncio, asyncpg
- **ML**: PyTorch
- **LLM**: OpenAI API / LangChain

### Infrastructure
- **Database**: PostgreSQL 15
- **Message Broker**: Eclipse Mosquitto (MQTT)
- **Containerization**: Docker & Docker Compose
- **Communication**: WebSocket, MQTT, REST API

## 📁 Project Structure

```
robot-ml-web-app/
├── frontend/          # Vue.js frontend
├── backend/           # FastAPI backend
├── database/          # Database migrations & init scripts
├── mqtt-broker/       # MQTT broker configuration
├── unity-simulator/   # Unity simulator (optional)
├── data/              # Data storage
├── logs/              # Application logs
├── docs/              # Documentation
├── tests/             # Tests
└── scripts/           # Utility scripts
```

詳細なディレクトリ構成は [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md) を参照してください。

## 🛠️ Setup & Installation

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.10+ (for local backend development)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/akinami3/robot-ml-web-app.git
   cd robot-ml-web-app
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Development Setup

#### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

#### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

## 🎮 Usage

### Starting the Simulator

1. ヘッダーの「シミュレーション起動」ボタンをクリック
2. Unity シミュレータが起動します
3. MQTT接続状態がヘッダーアイコンで確認できます

### Recording Robot Data

1. **データベース**タブに移動
2. 記録するデータ種別を選択（チェックボックス）
3. 「開始」ボタンで記録開始
4. 「一時停止」で中断、「保存」で確定

### Training ML Models

1. **機械学習**タブに移動
2. データセットを選択
3. モデル設定を調整
4. 「トレーニング開始」
5. リアルタイムで学習曲線が表示されます

### Using Chatbot

1. **Chatbot**タブに移動
2. 質問を入力
3. RAGベースのAIが回答します

## 🔌 API Documentation

FastAPI の自動生成ドキュメントが利用可能です：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

詳細な API 仕様は [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md#8-api-エンドポイント設計) を参照してください。

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
pytest --cov=app tests/  # with coverage
```

### Frontend Tests
```bash
cd frontend
npm run test:unit
npm run test:e2e
```

## 📊 Architecture

システムアーキテクチャの詳細は [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md) を参照してください。

主要な通信フロー:
```
Frontend ←→ WebSocket ←→ Backend ←→ MQTT ←→ Robot/Unity
                                  ↓
                              PostgreSQL
```

## 🔒 Security

- CORS設定
- 環境変数による機密情報管理
- SQLインジェクション対策（ORM使用）
- XSS対策（Vue.jsの自動エスケープ）

本番環境では以下を実装してください：
- JWT認証
- HTTPS/WSS
- MQTT over TLS
- API Rate Limiting

## 📝 License

MIT License

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📧 Contact

Project Link: https://github.com/akinami3/robot-ml-web-app

## 🙏 Acknowledgments

- FastAPI
- Vue.js
- PyTorch
- Eclipse Mosquitto
