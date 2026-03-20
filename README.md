# Step 10: リアルタイムダッシュボード 📊

> **ブランチ**: `step/10-realtime-dashboard`
> **前のステップ**: `step/09-react-migration`
> **次のステップ**: `step/11-data-recording`

---

## このステップで学ぶこと

1. **React カスタムフック** — `useWebSocket`, `useKeyboardControl` の設計
2. **WebSocket + React 統合** — 接続管理、自動再接続、ハートビート
3. **リアルタイム UI 更新** — `useRef` vs `useState` の使い分け
4. **Canvas + React** — `useEffect` ライフサイクルとの統合
5. **nipplejs** — 仮想ジョイスティックライブラリ
6. **recharts** — React 用グラフライブラリ

---

## 概要

Step 9 の React フロントエンドに WebSocket カスタムフックを組み込み、
センサーデータのリアルタイム表示、ロボットの手動操作（キーボード + ジョイスティック）、
緊急停止ボタンなど、ロボット操作に必要な全ての UI コンポーネントを React で実装するステップ。

Step 4（Vanilla JS Canvas）で作ったセンサー可視化を React コンポーネントとして再構築する。

---

## 学習ポイント

### useWebSocket カスタムフック

```typescript
const { isConnected, sensorData, sendCommand } = useWebSocket({
  url: 'ws://localhost:8080/ws',
  reconnectInterval: 3000,   // 自動再接続
  heartbeatInterval: 30000,  // Ping/Pong
});
```

- WebSocket 接続の抽象化（接続・切断・再接続）
- `useRef` で WebSocket インスタンスを保持（再レンダリング防止）
- `useCallback` でコールバック関数をメモ化
- ハートビート（Ping/Pong）で接続死活監視

### useRef vs useState の使い分け

| 用途 | Hook | 理由 |
|------|------|------|
| センサーデータ（50Hz） | `useRef` | 高頻度更新で再レンダリングを避ける |
| 接続状態 | `useState` | UI に反映する必要がある |
| Canvas 要素 | `useRef` | DOM 要素への直接アクセス |
| タイマー ID | `useRef` | クリーンアップ時に参照 |

### React + Canvas パターン

```tsx
const canvasRef = useRef<HTMLCanvasElement>(null);

useEffect(() => {
  const canvas = canvasRef.current;
  const ctx = canvas?.getContext('2d');
  // Canvas 描画ロジック
}, [sensorData]); // データ更新時に再描画
```

---

## 新規ページ

| ページ | パス | 内容 |
|--------|------|------|
| 手動操作 | `/control` | ジョイスティック + キーボード + E-Stop |
| センサー | `/sensors` | LiDAR, IMU, バッテリー, オドメトリの 4 パネル |
| ナビゲーション | `/navigation` | ナビゲーション目標設定 |

---

## ファイル構成

```
frontend/src/
  hooks/
    useWebSocket.ts              ← 🆕 WS 接続管理（再接続、ハートビート）
    useKeyboardControl.ts        ← 🆕 WASD / 矢印キーによるロボット操縦
  components/
    robot/
      EStopButton.tsx            ← 🆕 緊急停止ボタン（安全機能）
      JoystickController.tsx     ← 🆕 nipplejs 仮想ジョイスティック
      StatusBar.tsx              ← 🆕 接続状態・バッテリー・ロボット情報
    sensors/
      LiDARViewer.tsx            ← 🆕 Canvas LiDAR 点群表示（React 版）
      IMUChart.tsx               ← 🆕 IMU リアルタイムグラフ（recharts）
      BatteryGauge.tsx           ← 🆕 バッテリー残量表示
      OdometryDisplay.tsx        ← 🆕 オドメトリデータ表示
    layout/
      AppLayout.tsx              ← StatusBar 統合、useWebSocket 接続
      Sidebar.tsx                ← 操作・ナビ・センサーのナビ項目追加
  pages/
    ManualControlPage.tsx        ← 🆕 手動操作画面
    SensorViewPage.tsx           ← 🆕 センサー一覧グリッド
    NavigationPage.tsx           ← 🆕 ナビゲーション目標設定
  stores/
    robotStore.ts                ← latestSensorData, isEStopActive 追加
  App.tsx                        ← /control, /navigation, /sensors ルート追加
  package.json                   ← recharts, nipplejs 依存追加
```

---

## 起動方法

```bash
docker compose up --build
```

### 試してみる

1. http://localhost:3000 でログイン
2. サイドバー「手動操作」→ ジョイスティックや WASD キーでロボットを操作
3. サイドバー「センサー」→ 4 種類のセンサーがリアルタイムに更新
4. **StatusBar** で接続状態とバッテリー残量を確認
5. **E-Stop ボタン** で緊急停止 → 全コマンドがブロック

---

## Step 9 からの主な変更

| カテゴリ | 変更内容 |
|----------|----------|
| WebSocket | `useWebSocket` カスタムフックで React に統合 |
| ロボット操作 | ジョイスティック + キーボードの手動操作 UI |
| センサー表示 | LiDAR（Canvas）, IMU（recharts）, バッテリー, オドメトリ |
| 安全機能 | E-Stop ボタン + StatusBar |
| ページ | 3 ページ追加（操作・センサー・ナビゲーション） |
| 依存関係 | recharts, nipplejs 追加 |
| ファイル数 | 17 files changed, +3,847 / -56 |

---

## 🏋️ チャレンジ課題

1. **センサーの更新頻度を変えてみよう**: Gateway の MockAdapter で Hz を変更し、UI の挙動を観察
2. **useRef と useState を入れ替えてみよう**: 高頻度データに `useState` を使うとどうなる？
3. **グラフの種類を変えよう**: recharts の AreaChart や BarChart に変更してみよう
4. **キーバインドを追加**: スペースキーで E-Stop をトグルする機能を追加

---

## 次のステップへ

Step 11 では **Redis Streams** でセンサーデータのリアルタイム記録基盤を構築します:

```bash
git checkout step/11-data-recording
```
