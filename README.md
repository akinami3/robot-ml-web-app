# Step 1: Hello WebSocket 🌐

> **ブランチ**: `step/01-hello-websocket`  
> **前のステップ**: —（最初のステップ）  
> **次のステップ**: `step/02-protocol-messages`

---

## このステップで学ぶこと

1. **WebSocket** — HTTP との違い、双方向リアルタイム通信の仕組み
2. **Go 言語の基礎** — `main` 関数、パッケージ、`net/http`、gorilla/websocket
3. **HTML / JavaScript の基礎** — DOM操作、イベントリスナー、`WebSocket` API
4. **ブラウザ DevTools** — Network タブで WebSocket 通信を観察

---

## 構成図

```
┌──────────────────┐     WebSocket (ws://)     ┌──────────────────┐
│   ブラウザ        │◄──────────────────────────►│  Go サーバー      │
│   index.html     │    双方向リアルタイム通信     │  main.go         │
│                  │                            │                  │
│  テキスト入力     │  ── "forward" ──────────►  │  メッセージ受信    │
│  で送信ボタン     │                            │  → ログ出力       │
│                  │  ◄── "speed: 0.5 m/s" ──  │  → レスポンス返送  │
│                  │                            │                  │
│  受信メッセージ   │  ◄── "sensor: 23.5°C" ──  │  定期的に          │
│  をリスト表示     │     （1秒ごと）              │  モックデータ送信  │
└──────────────────┘                            └──────────────────┘
```

## ファイル構成

```
robot-ml-web-app/
├── gateway/
│   ├── main.go         ← Go WebSocket サーバー（1ファイル！）
│   └── go.mod          ← Go の依存関係定義
├── frontend/
│   └── index.html      ← フロントエンド（1ファイル！）
├── CURRICULUM.md        ← 全ステップの学習カリキュラム
└── README.md            ← このファイル
```

**たった3ファイルです。** Docker 不要、ビルドツール不要。

---

## 起動方法

### 前提条件

- **Go** >= 1.22（[インストール方法](https://go.dev/doc/install)）
- **Webブラウザ**（Chrome / Firefox / Edge）

### 1. Go サーバーを起動

```bash
cd gateway
go run main.go
```

以下のように表示されればOK:
```
🚀 WebSocket サーバー起動: http://localhost:8080
   WebSocket エンドポイント: ws://localhost:8080/ws
   Ctrl+C で停止
```

### 2. ブラウザで開く

`frontend/index.html` をブラウザで直接開きます:
```bash
# macOS
open frontend/index.html

# Linux
xdg-open frontend/index.html

# または、ブラウザのアドレスバーにファイルパスを入力
```

### 3. 試してみる

1. 「接続」ボタンをクリック → WebSocket 接続が確立
2. テキスト入力に `forward` と入力して「送信」 → サーバーに送信される
3. サーバーからのレスポンスと定期データがリストに表示される
4. **DevTools を開く**: `F12` → Network タブ → WS フィルター → メッセージを観察!

---

## 💡 WebSocket とは？

### HTTP との違い

```
【HTTP — リクエスト・レスポンス方式】
ブラウザ: 「データください」 → サーバー: 「はいどうぞ」
ブラウザ: 「また欲しいです」 → サーバー: 「はいどうぞ」
（毎回聞かないとデータがもらえない）

【WebSocket — 双方向通信】
ブラウザ: 「接続したいです」
サーバー: 「OK、繋がったよ」
  ↕  以降、どちらからでもいつでも送信可能  ↕
サーバー: 「新しいデータだよ」（ブラウザが聞いてなくても送れる）
ブラウザ: 「コマンド送るよ」
サーバー: 「了解」「また新しいデータだよ」
```

### なぜロボット操作に WebSocket が必要？

- ロボットのセンサーデータは **毎秒20〜50回** 更新される
- HTTP だと毎回リクエストが必要（遅い、サーバー負荷高い）
- WebSocket なら一度つなげば、サーバーから勝手にデータが流れてくる

---

## 📝 コードの読み方ガイド

### gateway/main.go を読む順序

1. `import` — 使っているパッケージを確認
2. `main()` — プログラムの起動処理
3. `handleWebSocket()` — WebSocket 接続時の処理
4. `readPump()` — クライアントからメッセージを受信するループ
5. `writePump()` — クライアントにデータを送信するループ

### frontend/index.html を読む順序

1. `<body>` — HTML の構造（ボタン、入力欄、メッセージリスト）
2. `<script>` — JavaScript のロジック
3. `connectWebSocket()` — WebSocket 接続を確立
4. `ws.onmessage` — サーバーからメッセージを受信した時の処理
5. `sendMessage()` — テキストをサーバーに送信

---

## 🏋️ チャレンジ課題

Step 2 に進む前に、以下を試してみましょう:

1. **送信メッセージを変えてみよう**: `forward` 以外に `backward`, `left`, `right` を送ってみる。サーバーの応答はどう変わる？
2. **送信間隔を変えてみよう**: `main.go` の `time.Second` を `500 * time.Millisecond` に変えたらどうなる？
3. **複数タブで接続**: ブラウザの別タブでも `index.html` を開いて接続してみよう。両方にデータが届く？
4. **DevTools で観察**: Network → WS タブで、メッセージのサイズとタイミングを確認しよう
5. **サーバーを止めてみよう**: `Ctrl+C` でサーバーを止めたら、ブラウザ側はどうなる？

---

## 次のステップへ

Step 2 では、テキストベースの通信を **構造化メッセージ（JSON / MessagePack）** に進化させます:

```bash
git checkout step/02-protocol-messages
```
