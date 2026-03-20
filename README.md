# Step 2: 構造化メッセージ 📡

## 学習目標

このステップで学ぶこと:

1. **JSON メッセージプロトコル設計** — type + payload パターン
2. **Go の構造体と JSON マーシャリング** — `json.Marshal` / `json.Unmarshal`
3. **Go のパッケージ分割** — `protocol/` ディレクトリの追加
4. **Go のインターフェース** — `Codec` インターフェースで差し替え可能な設計
5. **ES Modules** — `import` / `export` によるファイル分割
6. **WASD キーボード入力** — `keydown` / `keyup` イベントの処理
7. **リアルタイムダッシュボード** — CSS Grid + DOM 操作でセンサー表示

## アーキテクチャ

```
┌─────────────────────────────────────────────────┐
│ ブラウザ (frontend/)                              │
│                                                   │
│  index.html ─── js/app.js ─── js/protocol.js     │
│                                                   │
│  [WASD キーボード] → velocity_cmd JSON             │
│  [センサーパネル]  ← sensor_data JSON              │
│  [メッセージログ]  ← command_ack / error JSON      │
└──────────────────┬──────────────────────────────┘
                   │ WebSocket (JSON)
┌──────────────────┴──────────────────────────────┐
│ Go サーバー (gateway/)                            │
│                                                   │
│  main.go ─── protocol/messages.go                 │
│              protocol/codec.go                    │
│                                                   │
│  [readPump]   ← velocity_cmd をデコード・処理     │
│  [writePump]  → sensor_data を定期送信            │
│  [sendMessage] → command_ack/error を返信         │
└─────────────────────────────────────────────────┘
```

## ファイル構成

```
step2/
├── gateway/
│   ├── main.go                 # WebSocketサーバー（protocol利用版）
│   ├── go.mod                  # Goモジュール定義
│   ├── go.sum                  # 依存関係チェックサム
│   └── protocol/
│       ├── messages.go         # メッセージ型定義（Type, Payload構造体）
│       └── codec.go            # JSON コーデック（Encode/Decode）
├── frontend/
│   ├── index.html              # UI（センサーダッシュボード + WASDキー表示）
│   └── js/
│       ├── protocol.js         # メッセージ組み立て・解析（ES Module）
│       └── app.js              # メインロジック（接続管理・キーボード入力）
└── README.md                   # このファイル
```

## メッセージプロトコル

### 共通構造（エンベロープ）

すべてのメッセージは以下の共通構造を持ちます:

```json
{
  "type": "velocity_cmd",
  "robot_id": "robot-01",
  "timestamp": "2024-01-01T00:00:00.000Z",
  "payload": { ... }
}
```

| フィールド   | 型       | 説明 |
|-------------|----------|------|
| `type`      | string   | メッセージの種類（後述） |
| `robot_id`  | string   | ロボットの識別子 |
| `timestamp` | string   | ISO 8601 形式の時刻 |
| `payload`   | object   | メッセージ本体（type によって構造が異なる） |

### メッセージタイプ一覧

| type           | 方向                 | payload の内容 |
|----------------|---------------------|---------------|
| `velocity_cmd` | クライアント → サーバー | `{ linear_x, linear_y, angular_z }` |
| `sensor_data`  | サーバー → クライアント | `{ temperature, battery, speed, distance }` |
| `command_ack`  | サーバー → クライアント | `{ status, description }` |
| `error`        | サーバー → クライアント | `{ code, message }` |

### velocity_cmd の例

```json
{
  "type": "velocity_cmd",
  "robot_id": "robot-01",
  "timestamp": "2024-01-01T10:30:00.000Z",
  "payload": {
    "linear_x": 0.5,
    "linear_y": 0.0,
    "angular_z": 0.0
  }
}
```

### WASD キーマッピング

| キー    | linear_x | linear_y | angular_z | 動作 |
|---------|----------|----------|-----------|------|
| W       | 0.5      | 0        | 0         | 前進 |
| S       | -0.5     | 0        | 0         | 後退 |
| A       | 0        | 0        | 0.5       | 左旋回 |
| D       | 0        | 0        | -0.5      | 右旋回 |
| Space   | 0        | 0        | 0         | 停止 |

## セットアップと実行

### 1. サーバー起動

```bash
cd gateway
go run main.go
```

出力:
```
🚀 WebSocket サーバー起動 (Step 2: 構造化メッセージ)
   エンドポイント: ws://localhost:8080/ws
   プロトコル: JSON
   Ctrl+C で停止
```

### 2. フロントエンド表示

`frontend/index.html` をブラウザで直接開きます。

> ⚠️ **ES Modules の注意点**: `file://` プロトコルでは ES Modules の import が
> CORS エラーになるブラウザがあります。その場合は以下のいずれかの方法を使います:
>
> ```bash
> # 方法1: Python の簡易サーバー
> cd frontend
> python3 -m http.server 3000
> # → http://localhost:3000 でアクセス
>
> # 方法2: Node.js の npx serve
> cd frontend
> npx serve -p 3000
> ```

### 3. 操作方法

1. 「🔌 接続」ボタンをクリック
2. 「🎮 キーボード OFF」ボタンをクリックして ON に切り替え
3. **WASD** キーでロボットを操作、**Space** で停止
4. センサーパネルにリアルタイムでデータが表示される
5. DevTools（F12）→ Network → WS タブで JSON メッセージを確認

## Step 1 → Step 2 の変更点まとめ

### Go (gateway)

| 変更 | Step 1 | Step 2 |
|------|--------|--------|
| メッセージ形式 | テキスト文字列 | 構造化 JSON |
| パッケージ構成 | `main` パッケージのみ | `main` + `protocol` パッケージ |
| メッセージ処理 | `switch cmd` (文字列) | `switch msg.Type` (型付き) |
| レスポンス | テキスト文字列 | `command_ack` / `error` メッセージ |
| センサーデータ | `fmt.Sprintf` で文字列生成 | `SensorPayload` 構造体 |

### JavaScript (frontend)

| 変更 | Step 1 | Step 2 |
|------|--------|--------|
| ファイル構成 | 全て `index.html` 内 | `js/protocol.js` + `js/app.js` |
| モジュールシステム | なし | ES Modules (`import`/`export`) |
| 送信データ | テキスト (`"forward"`) | JSON (`{"type":"velocity_cmd",...}`) |
| 操作方法 | テキスト入力 + ボタン | WASD キーボード |
| 表示形式 | テキストログ | センサーダッシュボード + ログ |

## コードリーディングガイド

### 初心者の方へ: 読む順番

1. **`protocol/messages.go`** — メッセージの型定義を理解する
   - `Message` 構造体（エンベロープ）
   - `VelocityPayload`, `SensorPayload` etc.
   - `New〇〇` ファクトリ関数

2. **`protocol/codec.go`** — JSON のエンコード/デコードを理解する
   - `Codec` インターフェース
   - `JSONCodec.Encode()` — 構造体 → JSON
   - `JSONCodec.Decode()` — JSON → 構造体（2段階デコード）

3. **`main.go`** — サーバーのメッセージ処理を理解する
   - `readPump()` — 受信 → デコード → ハンドラー呼び出し
   - `handleVelocityCmd()` — 型アサーション
   - `writePump()` — 構造化センサーデータの定期送信

4. **`js/protocol.js`** — JavaScript 側のメッセージ操作
   - `MessageType` 定数
   - `createVelocityCmd()` — メッセージ生成
   - `KeyBindings` — WASD キーマッピング

5. **`js/app.js`** — UI とキーボード操作
   - `handleMessage()` — Type ベースのディスパッチ
   - `handleKeyDown()` — キーボード入力処理
   - `sendVelocityCmd()` — コマンド送信フロー

## チャレンジ課題

### 🟢 初級
1. 新しいキーバインドを追加してみよう（例: Q/E で左右移動）
2. `sensor_data` の受信回数をカウントして表示してみよう

### 🟡 中級
3. キーを離した時（keyup）に自動で停止コマンドを送信しよう
4. Go 側に新しいメッセージタイプ `status_request` を追加して、クライアントからロボットの状態を問い合わせられるようにしよう

### 🔴 上級
5. `protocol/codec.go` に `MsgPackCodec` を追加して、同じ `Codec` インターフェースで MessagePack エンコード/デコードを実装しよう
6. 複数のクライアントが同時に接続できるよう、接続管理の仕組み（Hub）を `main.go` に追加しよう（→ Step 4 で本格的に実装）

## 次のステップ

**Step 3: Adapter パターン** (`step/03-adapter-pattern`)
- Go のインターフェースによる多態性
- デザインパターン: Adapter, Factory, Registry
- Docker Compose の導入
