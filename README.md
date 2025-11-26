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

### Frontend (3つの実装を提供)

#### Vue.js版 (`frontend/`)
- **Framework**: Vue 3.3.10 (Composition API + TypeScript)
- **Build Tool**: Vite 5.0.8
- **State Management**: Pinia 2.1.7
- **HTTP Client**: Axios 1.6.2
- **Visualization**: Chart.js 4.4.0
- **Joystick**: nipplejs 0.10.1
- **Routing**: Vue Router 4.2.5

#### React版 (`frontend-react/`) ⚛️ NEW!
- **Framework**: React 18.2 + TypeScript 5.2
- **Build Tool**: Vite 5.0
- **State Management**: Zustand 4.4
- **HTTP Client**: Axios 1.6
- **Visualization**: Chart.js 4.4 + react-chartjs-2
- **Joystick**: nipplejs 0.10
- **Routing**: React Router 6.20
- 📦 **中サイズ** (~220KB)
- ⚡ **高速HMR** (開発体験優秀)
- 🔒 **完全な型安全性** (TypeScript)

#### Vanilla JS版 (`frontend-vanilla/`) ⭐
- **Framework**: なし（純粋なJavaScript）
- **Build Tool**: 不要
- **State Management**: カスタムストア
- **HTTP Client**: Fetch API
- **Visualization**: Chart.js 4.4.0
- **Joystick**: nipplejs 0.10.1
- **Routing**: カスタムハッシュルーター
- 📦 **最軽量** (~180KB)
- ⚡ **最速** (ビルド不要、初回ロード ~300ms)

### Backend
- **Framework**: FastAPI 0.104+ (Python 3.10+)
- **Database**: PostgreSQL 15 with SQLAlchemy 2.0 (async)
- **ORM**: SQLAlchemy 2.0 (async engine)
- **Migration**: Alembic
- **ML**: PyTorch 2.1+
- **LLM**: OpenAI API / LangChain
- **WebSocket**: Native FastAPI WebSocket support
- **Task Queue**: (Optional) Celery with Redis

### Infrastructure
- **Database**: PostgreSQL 15
- **Message Broker**: Eclipse Mosquitto (MQTT)
- **Containerization**: Docker & Docker Compose
- **Communication**: WebSocket, MQTT, REST API

## 📁 Project Structure

```
robot-ml-web-app/
├── frontend/          # Vue.js frontend (オリジナル)
├── frontend-react/    # React + TypeScript frontend (NEW!)
├── frontend-vanilla/  # Vanilla JS frontend (フレームワークレス)
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

### 📌 フロントエンド選択ガイド

**Vanilla JS版を選ぶ場合** (`frontend-vanilla/`):
- ✅ 軽量・高速な実装が必要
- ✅ ビルドツールを使いたくない
- ✅ Web開発の基礎を学びたい
- ✅ 依存関係を最小限にしたい

**React版を選ぶ場合** (`frontend-react/`):
- ✅ TypeScriptによる型安全性が必要
- ✅ 大規模アプリケーション
- ✅ Reactエコシステムを活用したい
- ✅ 最高の開発体験（HMR、DevTools）
- ✅ 就職・転職で有利なスキル

**Vue.js版を選ぶ場合** (`frontend/`):
- ✅ 学習曲線が緩やかなフレームワーク
- ✅ テンプレート構文が好み
- ✅ Vueエコシステムを活用したい
- ✅ 日本語ドキュメントが豊富

詳細な比較: 
- [frontend-vanilla/COMPARISON.md](./frontend-vanilla/COMPARISON.md)
- [frontend-react/COMPARISON.md](./frontend-react/COMPARISON.md) (3つの実装を比較)

詳細なディレクトリ構成は [SYSTEM_DESIGN.md](./SYSTEM_DESIGN.md) を参照してください.

## 🛠️ Setup & Installation

### Prerequisites

- Docker & Docker Compose (for full stack)
- **Vanilla JS版**: Python 3.x のみ (超シンプル!)
- **Vue.js版**: Node.js 18+ 
- Python 3.10+ (for backend development)

### Quick Start

#### 🚀 最速スタート (Vanilla JS版)

1. **バックエンドを起動**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **フロントエンドを起動**
   ```bash
   cd frontend-vanilla
   ./serve.sh
   ```

3. **ブラウザで開く**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

詳細: [frontend-vanilla/QUICK_START.md](./frontend-vanilla/QUICK_START.md)

#### ⚛️ React版スタート

1. **バックエンドを起動**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **フロントエンドを起動**
   ```bash
   cd frontend-react
   npm install  # 初回のみ
   npm run dev
   ```

3. **ブラウザで開く**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/docs

詳細: [frontend-react/QUICK_START.md](./frontend-react/QUICK_START.md)

#### 🎨 Vue.js版スタート

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

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your configuration:
# - DATABASE_URL (PostgreSQL connection string)
# - MQTT_BROKER_HOST and MQTT_BROKER_PORT
# - OPENAI_API_KEY (for chatbot functionality)
# - CORS_ORIGINS (allowed frontend URLs)

# Run database migrations (if applicable)
# alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The backend API will be available at `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

#### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env
# Edit .env if needed:
# - VITE_API_URL=http://localhost:8000
# - VITE_WS_URL=ws://localhost:8000
# - VITE_APP_TITLE=Robot ML Control System

# Start development server with hot reload
npm run dev
```

The frontend will be available at `http://localhost:5173`

#### Frontend Commands

```bash
# Type checking
npm run type-check

# Build for production
npm run build

# Preview production build
npm run preview
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
