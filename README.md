# Step 3: Adapter パターン 🤖

## 学習目標
- Go のインターフェースと暗黙的実装
- デザインパターン: **Adapter**, **Factory**, **Registry**
- `cmd/` + `internal/` プロジェクトレイアウト
- Docker Compose の基礎

## Step 2 からの変更点

### Gateway（Go）
| 変更 | 内容 |
|------|------|
| `main.go` → `cmd/gateway/main.go` | エントリーポイントを `cmd/` に分離 |
| `internal/adapter/interface.go` | RobotAdapter インターフェース定義 |
| `internal/adapter/registry.go` | ファクトリパターンでアダプター管理 |
| `internal/adapter/mock/mock_adapter.go` | モックロボット（センサーデータ生成） |
| `internal/server/websocket.go` | WebSocket サーバーを server パッケージに分離 |

### フロントエンド
| 変更 | 内容 |
|------|------|
| `index.html` | オドメトリ + バッテリー表示、E-Stop ボタン追加 |
| `js/protocol.js` | adapter_info, estop, connect, disconnect メッセージ追加 |
| `js/app.js` | ロボット接続管理、E-Stop、Adapter 形式センサー対応 |

### インフラ
| 変更 | 内容 |
|------|------|
| `docker-compose.yml` | Gateway + Frontend(nginx) のサービス定義 |
| `gateway/Dockerfile` | マルチステージビルド |

## プロジェクト構造

```
gateway/
├── cmd/gateway/main.go           # エントリーポイント（配線のみ）
├── internal/
│   ├── adapter/
│   │   ├── interface.go          # RobotAdapter インターフェース
│   │   ├── registry.go           # アダプター管理（Factory + Registry）
│   │   └── mock/
│   │       └── mock_adapter.go   # モックロボット
│   ├── protocol/                 # Step 2 から継続
│   │   ├── messages.go
│   │   └── codec.go
│   └── server/
│       └── websocket.go          # WebSocket サーバー
├── go.mod
├── go.sum
└── Dockerfile

frontend/
├── index.html                    # ダッシュボード UI
└── js/
    ├── protocol-base.js          # Step 2 の protocol.js
    ├── protocol.js               # Step 3 拡張版
    └── app.js                    # メインアプリ

docker-compose.yml                # サービス定義
```

## 起動方法

### ローカル開発（Docker なし）

```bash
# Gateway を起動
cd gateway
go run cmd/gateway/main.go

# 別のターミナルでフロントエンドを起動
cd frontend
python3 -m http.server 3000
# → http://localhost:3000 でアクセス
```

### Docker Compose

```bash
docker compose up --build
# → http://localhost:3000 でフロントエンド
# → ws://localhost:8080/ws で WebSocket
```

## キーコンセプト

### 1. インターフェースの暗黙的実装

```go
// interface.go: インターフェース定義
type RobotAdapter interface {
    Name() string
    Connect(ctx context.Context, config map[string]any) error
    SendCommand(ctx context.Context, cmd Command) error
    // ...
}

// mock_adapter.go: 実装（"implements" キーワード不要）
type MockAdapter struct { ... }
func (m *MockAdapter) Name() string { return "mock" }
func (m *MockAdapter) Connect(...) error { ... }

// コンパイル時チェック
var _ RobotAdapter = (*MockAdapter)(nil)
```

### 2. Factory + Registry パターン

```go
// ファクトリ関数を登録
registry := adapter.NewRegistry()
registry.RegisterFactory("mock", mock.Factory)

// 名前からアダプターを生成
adapter, err := registry.CreateAdapter("mock")
```

### 3. 依存性注入（DI）

```go
// main.go が各パーツを「注入」する
srv := server.NewServer(robotAdapter, ":8080")
```

## 通信フロー

```
Browser                Server (Go)               MockAdapter
  │                       │                          │
  │── WS接続 ──────────►│                          │
  │◄── adapter_info ────│                          │
  │                       │                          │
  │── "connect" ────────►│── Connect() ──────────►│
  │◄── command_ack ─────│                          │
  │                       │◄── SensorData (20Hz) ──│
  │◄── sensor_data ─────│                          │
  │◄── sensor_data ─────│                          │
  │                       │                          │
  │── velocity_cmd ────►│── SendCommand() ───────►│
  │◄── command_ack ─────│                          │
  │                       │   (位置更新 → センサーに反映)
  │                       │                          │
  │── "estop" ──────────►│── EmergencyStop() ────►│
  │◄── command_ack ─────│                          │
```

## 次のステップ
→ **Step 4: センサー可視化** — Canvas 2D でリアルタイム描画
