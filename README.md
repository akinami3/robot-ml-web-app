# Step 5: 安全パイプライン 🛡️

> **ブランチ**: `step/05-safety-pipeline`
> **前のステップ**: `step/04-sensor-visualization`
> **次のステップ**: `step/06-rest-api`

---

## このステップで学ぶこと

1. **Go の並行処理** — goroutine, channel, `sync.RWMutex` による排他制御
2. **安全設計の基本原則** — フェイルセーフ、多段階バリデーション
3. **Hub パターン** — チャネルベースの Pub/Sub（register / unregister / broadcast）
4. **Watchdog タイマー** — タイムアウト監視と自動安全停止

---

## 概要

ロボット操作における安全機能を Gateway に実装するステップ。
緊急停止（E-Stop）、速度リミッター、通信タイムアウト監視（Watchdog）、
操作排他ロック（OperationLock）の 4 つの安全コンポーネントを組み込み、
Hub パターンで複数クライアントへのメッセージ配信を管理する。

---

## 学習ポイント

### 緊急停止（E-Stop）マネージャー
- `sync.RWMutex` による読み取り/書き込みロックの使い分け
- Observer パターン（`OnStateChange` リスナー）
- E-Stop 発動時にすべてのコマンドをブロック

### 速度リミッター（VelocityLimiter）
- `clamp` 関数による値の安全な範囲制限
- NaN / Inf チェック（ガード節パターン）
- 設定可能な最大線速度・角速度

### タイムアウト Watchdog
- `context.WithCancel` による goroutine ライフサイクル管理
- `time.Ticker` で定期的な死活監視
- タイムアウト検出時の自動安全停止

### 操作排他ロック（OperationLock）
- 同時に 1 クライアントだけが操作可能
- ロック取得・解放・強制解放
- デッドロック防止の設計

### Hub パターン（Pub/Sub）
- チャネルベースの `register` / `unregister` / `broadcast`
- `select` 文によるイベントループ
- Ping/Pong ハートビートによる WebSocket 死活監視
- `atomic` カウンターによるクライアント ID 生成

---

## ファイル構成

```
gateway/
  cmd/gateway/
    main.go                   ← 全安全コンポーネントの配線
  internal/
    adapter/
      interface.go            ← RobotAdapter インターフェース
      registry.go             ← アダプター管理
      mock/
        mock_adapter.go       ← モックロボット（センサー生成）
    protocol/
      messages.go             ← メッセージ型定義
      codec.go                ← エンコード・デコード
    safety/
      estop.go                ← 🆕 緊急停止マネージャー
      velocity_limiter.go     ← 🆕 速度制限
      timeout_watchdog.go     ← 🆕 タイムアウト監視
      operation_lock.go       ← 🆕 操作排他ロック
    server/
      websocket.go            ← readPump / writePump 分離
      hub.go                  ← 🆕 Hub + Client 管理
      handler.go              ← 🆕 安全パイプライン統合ハンドラー

frontend/
  index.html                  ← 安全ステータスパネル + E-Stop UI 追加
  css/
    style.css                 ← ブリンクアニメーション追加
  js/
    app.js                    ← 安全状態の表示連携
    sensors/                  ← Step 4 から継続

docker-compose.yml            ← 2サービス（frontend + gateway）
```

---

## 起動方法

```bash
docker compose up --build
```

ブラウザで http://localhost:3000 を開く。

### 安全機能を試す

1. 「WS接続」→「ロボット接続」でセンサーデータが流れ始める
2. **E-Stop ボタン**（赤い大きなボタン）をクリック → 全コマンドがブロックされる
3. E-Stop を解除するとコマンドが再び有効になる
4. 接続を切断して数秒待つ → Watchdog がタイムアウトを検出

---

## 安全パイプラインの流れ

```
ユーザー入力
    │
    ▼
┌──────────────┐    NG
│  E-Stop 確認  │──────────► コマンド拒否
└──────┬───────┘
       │ OK
       ▼
┌──────────────┐    NG
│  ロック確認    │──────────► 他ユーザーが操作中
└──────┬───────┘
       │ OK
       ▼
┌──────────────┐
│ 速度リミッター │──────────► 値をクランプして通過
└──────┬───────┘
       │
       ▼
  ロボットへ送信
```

---

## Step 4 からの主な変更

| カテゴリ | 変更内容 |
|----------|----------|
| 安全機能 | E-Stop、速度リミッター、Watchdog、操作ロックを新規追加 |
| サーバー設計 | Hub パターンで複数クライアント管理に対応 |
| WebSocket | readPump / writePump 分離、Ping/Pong ハートビート |
| フロント | 安全ステータスパネル、E-Stop ボタン UI |
| ファイル数 | 12 files changed, +1,847 / -621 |

---

## 🏋️ チャレンジ課題

1. **速度制限値を変えてみよう**: `velocity_limiter.go` の最大速度を変更して挙動を確認
2. **Watchdog タイムアウトを短くしてみよう**: 何秒で安全停止が発動するか観察
3. **複数タブで接続**: 操作ロックが正しく機能するか確認
4. **E-Stop 中にコマンド送信**: サーバーログでブロックされていることを確認

---

## 次のステップへ

Step 6 では **FastAPI** を使った REST API バックエンドを追加し、3サービス構成にします:

```bash
git checkout step/06-rest-api
```
       Wall (y=-4)
```

## Step 3 からの変更差分

| 変更 | 詳細 |
|------|------|
| MockAdapter 拡張 | LiDAR (10Hz) + IMU (50Hz) センサー追加 |
| 外部 CSS | `<style>` → `css/style.css` に分離 |
| WebSocketClient | 生 WebSocket → クラスで抽象化 |
| LidarViewer | Canvas: 極座標 → 直交座標変換で点群描画 |
| ImuChart | Canvas: リングバッファ式 6 軸ラインチャート |
| BatteryGauge | CSS バー → SVG 円形ゲージ |
| OdometryViewer | 数値のみ → Canvas ミニマップ + 軌跡描画 |
