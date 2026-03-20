// =============================================================================
// Step 4: センサー可視化 — app.js（メインアプリケーション）
// =============================================================================
//
// 【Step 3 からの変更点】
// 1. WebSocketClient クラスを使って接続管理を抽象化
// 2. センサービューアクラスを import してデータをルーティング
// 3. Hz（更新頻度）の計測と表示
// 4. Canvas ベースのセンサー描画
//
// 【アーキテクチャ: Observer パターン風のデータフロー】
//
//   WebSocket → WebSocketClient.onMessage(callback)
//                       ↓
//                handleMessage(msg)
//                       ↓
//           ┌──── switch(msg.type) ────┐
//           │                          │
//     sensor_data                command_ack / adapter_info / error
//           ↓
//  handleSensorData(msg)
//           ↓
//  ┌── payload 判定 ──────┐
//  │ "ranges" → LiDAR     │
//  │ "accel_x" → IMU      │
//  │ "pos_x" → Odom       │
//  │ "percentage" → Batt   │
//  └───────────────────────┘
//
// =============================================================================
import {
  MessageType,
  KeyBindings,
  createVelocityCmd,
  createEStopCmd,
  createConnectCmd,
  createDisconnectCmd,
  encodeMessage,
  decodeMessage,
} from "./protocol.js";

import { WebSocketClient } from "./websocket-client.js";
import { LidarViewer } from "./sensors/lidar-viewer.js";
import { ImuChart } from "./sensors/imu-chart.js";
import { BatteryGauge } from "./sensors/battery-gauge.js";
import { OdometryViewer } from "./sensors/odometry.js";

// =============================================================================
// センサービューアの初期化
// =============================================================================
//
// 【各ビューアの責務】
// - LidarViewer: Canvas に極座標プロット（360点の距離データ）
// - ImuChart: Canvas にリングバッファ式ラインチャート（6軸）
// - BatteryGauge: SVG で円形ゲージを描画
// - OdometryViewer: Canvas にミニマップ + HTML で数値表示
const lidarViewer = new LidarViewer("lidarCanvas");
const imuChart = new ImuChart("imuCanvas", "imuLegend");
const batteryGauge = new BatteryGauge("batteryGauge");
const odomViewer = new OdometryViewer("odomCanvas", "odomValues");

// =============================================================================
// Hz カウンター — センサーの更新頻度を計測
// =============================================================================
//
// 【Hz（ヘルツ）とは？】
// 1秒あたりの更新回数。LiDAR は ~10Hz（100ms間隔）、IMU は ~50Hz（20ms間隔）。
// 実際のロボット開発でも、センサーの Hz は重要な性能指標。
//
// 【計測方法】
// 1秒間に受信したカウントを保持し、1秒ごとにリセット。
// requestAnimationFrame ではなく setInterval で 1 秒ごとに更新。
const hzCounters = {
  lidar: { count: 0, element: null },
  imu: { count: 0, element: null },
  odom: { count: 0, element: null },
  battery: { count: 0, element: null },
};

// 1 秒ごとに Hz 表示を更新
setInterval(() => {
  for (const [key, counter] of Object.entries(hzCounters)) {
    if (counter.element) {
      counter.element.textContent = `${counter.count} Hz`;
    }
    counter.count = 0;
  }
}, 1000);

// =============================================================================
// アプリケーション状態
// =============================================================================
let wsClient = null;
let keyboardEnabled = false;

// Docker 環境対応: ブラウザのホスト名から WS 接続先を決定
const WS_HOST = window.location.hostname || "localhost";
const WS_URL = `ws://${WS_HOST}:8080/ws`;

// =============================================================================
// DOM 要素の取得
// =============================================================================
const elements = {
  statusDot: document.getElementById("statusDot"),
  statusText: document.getElementById("statusText"),
  btnConnect: document.getElementById("btnConnect"),
  btnDisconnect: document.getElementById("btnDisconnect"),
  btnKeyboard: document.getElementById("btnKeyboard"),
  messagesDiv: document.getElementById("messages"),
  counterDiv: document.getElementById("counter"),
  // ロボット関連
  btnRobotConnect: document.getElementById("btnRobotConnect"),
  btnRobotDisconnect: document.getElementById("btnRobotDisconnect"),
  btnEStop: document.getElementById("btnEStop"),
  robotStatus: document.getElementById("robotStatus"),
  adapterName: document.getElementById("adapterName"),
  // WASD キー表示
  keyW: document.getElementById("keyW"),
  keyA: document.getElementById("keyA"),
  keyS: document.getElementById("keyS"),
  keyD: document.getElementById("keyD"),
  keySpace: document.getElementById("keySpace"),
  lastCommand: document.getElementById("lastCommand"),
};

// Hz バッジの取得
hzCounters.lidar.element = document.getElementById("lidarHz");
hzCounters.imu.element = document.getElementById("imuHz");
hzCounters.odom.element = document.getElementById("odomHz");
hzCounters.battery.element = document.getElementById("batteryHz");

// =============================================================================
// connectWebSocket — WebSocketClient で接続
// =============================================================================
//
// 【Step 3 との違い】
// Step 3: 生の WebSocket API を直接使用（ws = new WebSocket(url)）
// Step 4: WebSocketClient クラスで接続管理を抽象化
//
// WebSocketClient は以下を内部で管理する:
//   - 接続/切断の状態
//   - 送受信カウント
//   - コールバック（onMessage, onStateChange）
export function connectWebSocket() {
  wsClient = new WebSocketClient(WS_URL, {
    // メッセージ受信コールバック
    onMessage: (rawData) => {
      const msg = decodeMessage(rawData);
      if (!msg) {
        addMessage("⚠️ 不正なメッセージを受信", "system");
        return;
      }
      handleMessage(msg);
      updateCounter();
    },

    // 接続状態変更コールバック
    onStateChange: (connected) => {
      if (connected) {
        addMessage("✅ サーバーに接続しました", "system");
      } else {
        addMessage("❌ 接続が閉じました", "system");
      }
      setConnectedState(connected);
    },
  });

  wsClient.connect();
}

// =============================================================================
// disconnectWebSocket — 切断
// =============================================================================
export function disconnectWebSocket() {
  if (wsClient) {
    wsClient.disconnect();
  }
}

// =============================================================================
// handleMessage — 受信メッセージをタイプ別に処理
// =============================================================================
function handleMessage(msg) {
  switch (msg.type) {
    case MessageType.SENSOR_DATA:
      handleSensorData(msg);
      break;
    case MessageType.COMMAND_ACK:
      handleCommandAck(msg);
      break;
    case MessageType.ERROR:
      handleError(msg);
      break;
    case MessageType.ADAPTER_INFO:
      handleAdapterInfo(msg);
      break;
    default:
      addMessage(`⚠️ 不明なメッセージタイプ: ${msg.type}`, "system");
  }
}

// =============================================================================
// handleSensorData — センサーデータを適切なビューアに振り分け
// =============================================================================
//
// 【ルーティングの仕組み】
// MockAdapter は SensorData の Data（= map[string]any）を payload に入れて送る。
// payload のキーを見て、どのセンサーのデータかを判別する。
//
// これは簡易的な方法。プロダクションでは topic フィールドや
// data_type フィールドで明示的にルーティングする。
//
// 【各センサーのデータ形式】
// LiDAR:    { ranges: number[], angles: number[], num_points, min_range, max_range }
// IMU:      { accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z }
// Odom:     { pos_x, pos_y, theta, linear_x, angular_z, speed }
// Battery:  { percentage, voltage, temperature }
function handleSensorData(msg) {
  const data = msg.payload;
  if (!data) return;

  // LiDAR: ranges 配列を持っている
  if ("ranges" in data) {
    lidarViewer.update(data);
    hzCounters.lidar.count++;
    return;
  }

  // IMU: accel_x を持っている
  if ("accel_x" in data) {
    imuChart.update(data);
    hzCounters.imu.count++;
    return;
  }

  // Odom: pos_x を持っている
  if ("pos_x" in data) {
    odomViewer.update(data);
    hzCounters.odom.count++;
    return;
  }

  // Battery: percentage を持っている
  if ("percentage" in data) {
    batteryGauge.update(data);
    hzCounters.battery.count++;
    return;
  }
}

// =============================================================================
// handleAdapterInfo — アダプター情報の受信処理
// =============================================================================
function handleAdapterInfo(msg) {
  const info = msg.payload;
  addMessage(`🤖 アダプター: ${info.adapter_name} (接続: ${info.connected})`, "received");

  if (elements.adapterName) {
    elements.adapterName.textContent = info.adapter_name;
  }
  setRobotConnected(info.connected);

  if (info.capabilities) {
    const caps = info.capabilities;
    addMessage(
      `  速度制御: ${caps.velocity_control ? "✅" : "❌"} | ` +
      `E-Stop: ${caps.estop ? "✅" : "❌"} | ` +
      `ナビ: ${caps.navigation ? "✅" : "❌"}`,
      "system"
    );
    if (caps.sensor_topics) {
      addMessage(
        `  センサートピック: ${caps.sensor_topics.join(", ")}`,
        "system"
      );
    }
  }
}

// =============================================================================
// handleCommandAck — コマンド応答の処理
// =============================================================================
function handleCommandAck(msg) {
  const { status, description } = msg.payload;
  addMessage(`🤖 [${status}] ${description}`, "received");

  if (status === "connected") {
    setRobotConnected(true);
  } else if (status === "disconnected") {
    setRobotConnected(false);
  } else if (status === "stopped") {
    addMessage("🚨 緊急停止が実行されました", "system");
  }
}

// =============================================================================
// handleError — エラーメッセージの表示
// =============================================================================
function handleError(msg) {
  const { code, message } = msg.payload;
  addMessage(`❌ エラー (${code}): ${message}`, "system");
}

// =============================================================================
// コマンド送信関数
// =============================================================================

function sendMessage(msgObj) {
  if (!wsClient || !wsClient.isConnected) return;
  wsClient.send(encodeMessage(msgObj));
}

export function sendVelocityCmd(linearX, linearY, angularZ) {
  sendMessage(createVelocityCmd(linearX, linearY, angularZ));
}

export function sendEStop() {
  if (!wsClient || !wsClient.isConnected) {
    addMessage("⚠️ サーバー未接続です", "system");
    return;
  }
  sendMessage(createEStopCmd());
  addMessage("🚨 緊急停止コマンドを送信しました", "sent");
}

export function sendRobotConnect() {
  sendMessage(createConnectCmd());
}

export function sendRobotDisconnect() {
  sendMessage(createDisconnectCmd());
}

// =============================================================================
// キーボード入力の処理
// =============================================================================

export function toggleKeyboardControl() {
  keyboardEnabled = !keyboardEnabled;

  if (elements.btnKeyboard) {
    elements.btnKeyboard.textContent = keyboardEnabled
      ? "🎮 キーボード ON"
      : "🎮 キーボード OFF";
    elements.btnKeyboard.classList.toggle("active", keyboardEnabled);
  }

  addMessage(
    keyboardEnabled
      ? "🎮 キーボード操作を有効にしました（WASD + Space）"
      : "🎮 キーボード操作を無効にしました",
    "system"
  );
}

function handleKeyDown(event) {
  if (!keyboardEnabled) return;
  if (event.repeat) return;

  const key = event.key.toLowerCase();
  const binding = KeyBindings.get(key);

  if (binding) {
    sendVelocityCmd(binding.linearX, binding.linearY, binding.angularZ);
    highlightKey(key, true);
    if (elements.lastCommand) {
      elements.lastCommand.textContent = binding.label;
    }
    event.preventDefault();
  }
}

function handleKeyUp(event) {
  if (!keyboardEnabled) return;
  const key = event.key.toLowerCase();
  if (KeyBindings.has(key)) {
    highlightKey(key, false);
  }
}

function highlightKey(key, active) {
  const keyMap = {
    w: elements.keyW,
    a: elements.keyA,
    s: elements.keyS,
    d: elements.keyD,
    " ": elements.keySpace,
  };
  const el = keyMap[key];
  if (el) {
    el.classList.toggle("active", active);
  }
}

// =============================================================================
// UI ヘルパー関数
// =============================================================================

function addMessage(text, type) {
  if (!elements.messagesDiv) return;
  const div = document.createElement("div");
  div.classList.add("message", type);
  const time = new Date().toLocaleTimeString();
  div.innerHTML = `<span class="timestamp">[${time}]</span> ${text}`;
  elements.messagesDiv.appendChild(div);
  elements.messagesDiv.scrollTop = elements.messagesDiv.scrollHeight;

  const MAX_MESSAGES = 200;
  while (elements.messagesDiv.children.length > MAX_MESSAGES) {
    elements.messagesDiv.removeChild(elements.messagesDiv.firstChild);
  }
}

function setConnectedState(connected) {
  if (connected) {
    elements.statusDot?.classList.add("connected");
    if (elements.statusText) elements.statusText.textContent = `接続中 (${WS_URL})`;
    if (elements.btnConnect) elements.btnConnect.disabled = true;
    if (elements.btnDisconnect) elements.btnDisconnect.disabled = false;
    if (elements.btnKeyboard) elements.btnKeyboard.disabled = false;
    if (elements.btnRobotConnect) elements.btnRobotConnect.disabled = false;
    if (elements.btnRobotDisconnect) elements.btnRobotDisconnect.disabled = false;
    if (elements.btnEStop) elements.btnEStop.disabled = false;
  } else {
    elements.statusDot?.classList.remove("connected");
    if (elements.statusText) elements.statusText.textContent = "未接続";
    if (elements.btnConnect) elements.btnConnect.disabled = false;
    if (elements.btnDisconnect) elements.btnDisconnect.disabled = true;
    if (elements.btnKeyboard) elements.btnKeyboard.disabled = true;
    if (elements.btnRobotConnect) elements.btnRobotConnect.disabled = true;
    if (elements.btnRobotDisconnect) elements.btnRobotDisconnect.disabled = true;
    if (elements.btnEStop) elements.btnEStop.disabled = true;
    keyboardEnabled = false;
    if (elements.btnKeyboard) {
      elements.btnKeyboard.textContent = "🎮 キーボード OFF";
      elements.btnKeyboard.classList.remove("active");
    }
  }
}

function setRobotConnected(connected) {
  if (elements.robotStatus) {
    elements.robotStatus.textContent = connected ? "🟢 接続中" : "🔴 未接続";
    elements.robotStatus.style.color = connected ? "#28a745" : "#dc3545";
  }
}

function updateCounter() {
  if (!elements.counterDiv || !wsClient) return;
  elements.counterDiv.textContent =
    `送信: ${wsClient.sentCount} | 受信: ${wsClient.receivedCount}`;
}

// =============================================================================
// イベントリスナーの登録
// =============================================================================
document.addEventListener("keydown", handleKeyDown);
document.addEventListener("keyup", handleKeyUp);

// =============================================================================
// グローバルに公開（HTML の onclick から呼び出し用）
// =============================================================================
window.connectWebSocket = connectWebSocket;
window.disconnectWebSocket = disconnectWebSocket;
window.toggleKeyboardControl = toggleKeyboardControl;
window.sendEStop = sendEStop;
window.sendRobotConnect = sendRobotConnect;
window.sendRobotDisconnect = sendRobotDisconnect;
