# Step 4: センサー可視化ダッシュボード 📡

## 概要

4種類のセンサーデータをリアルタイムに Canvas / SVG で可視化するステップ。
MockAdapter を拡張してLiDAR・IMU データを生成し、ブラウザ上で描画する。

## 学習ポイント

### Canvas 2D API
- `<canvas>` 要素と `getContext('2d')` による描画
- 座標変換（translate, rotate）
- requestAnimationFrame ではなく WebSocket メッセージ駆動の更新

### SVG（Scalable Vector Graphics）
- `<circle>` と `stroke-dasharray` / `stroke-dashoffset` による円形ゲージ
- Canvas との使い分け: UIパーツ → SVG、高頻度更新 → Canvas

### ES Classes とプライベートフィールド
- `class` 構文による OOP
- `#field` でプライベートフィールドを宣言（ES2022）
- コンストラクタでの依存性注入パターン

### センサーデータの基礎
| センサー | 周波数 | データ内容 |
|----------|--------|------------|
| LiDAR | 10 Hz | 360点の距離データ（極座標） |
| IMU | 50 Hz | 加速度 3軸 + ジャイロ 3軸 |
| Odometry | 10 Hz | 位置 (x,y)、向き θ、速度 |
| Battery | 1 Hz | 残量 %、電圧、温度 |

### 外部 CSS
- `<style>` タグからの分離
- CSSファイルのキャッシュメリット
- BEM 風のクラス命名

## ファイル構成

```
gateway/
  internal/
    adapter/mock/
      mock_adapter.go  ← LiDAR + IMU 生成を追加

frontend/
  index.html           ← 外部CSS参照 + ダッシュボードレイアウト
  css/
    style.css          ← 外部CSS（auto-fill グリッド）
  js/
    protocol-base.js   ← Step 2 から継続
    protocol.js        ← Step 3 から継続
    websocket-client.js ← WebSocket をクラスで管理
    app.js             ← センサーデータのルーティング
    sensors/
      lidar-viewer.js  ← LiDAR 極座標プロット
      imu-chart.js     ← IMU 6軸リアルタイムチャート
      battery-gauge.js ← SVG 円形バッテリーゲージ
      odometry.js      ← 軌跡付きミニマップ
```

## 起動方法

```bash
docker compose up --build
```

ブラウザで http://localhost:3000 を開き、「WS接続」→「ロボット接続」。

## MockAdapter の LiDAR シミュレーション

MockAdapter は仮想的な部屋（10m × 8m）を定義し、ロボットの位置から
各角度方向にレイキャスト（光線追跡）を行って壁までの距離を計算する。

```
       Wall (y=4)
  ┌─────────────────────┐
  │                     │
  │     Robot (0,0) →   │    360点のスキャン
  │                     │
  └─────────────────────┘
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
