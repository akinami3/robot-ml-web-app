// =============================================================================
// Step 5: センサー可視化 + 安全パイプライン — app.js
// =============================================================================
//
// 【Step 4 からの変更点】
// 1. safety_status メッセージへの対応
// 2. E-Stop 解除ボタンの追加
// 3. 安全状態のリアルタイム表示（E-Stop, 速度制限）
// 4. estop_release メッセージの送信
// 5. status メッセージの送信（接続時に安全状態を問い合わせ）
//
// =============================================================================
import {
  MessageType,
  KeyBindings,
  createVelocityCmd,
  createEStopCmd,
  createEStopReleaseCmd,
  createConnectCmd,
  createDisconnectCmd,
  createStatusCmd,
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
const lidarViewer = new LidarViewer("lidarCanvas");
const imuChart = new ImuChart("imuCanvas", "imuLegend");
const batteryGauge = new BatteryGauge("batteryGauge");
const odomViewer = new OdometryViewer("odomCanvas", "odomValues");

// =============================================================================
// Hz カウンター
// =============================================================================
const hzCounters = {
  lidar: { count: 0, element: null },
  imu: { count: 0, element: null },
  odom: { count: 0, element: null },
  battery: { count: 0, element: null },
};

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
let estopActive = false; // E-Stop の状態をフロントエンドでも追跡

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
  btnRobotConnect: document.getElementById("btnRobotConnect"),
  btnRobotDisconnect: document.getElementById("btnRobotDisconnect"),
  btnEStop: document.getElementById("btnEStop"),
  btnEStopRelease: document.getElementById("btnEStopRelease"),
  robotStatus: document.getElementById("robotStatus"),
  adapterName: document.getElementById("adapterName"),
  // Step 5: 安全状態表示
  estopIndicator: document.getElementById("estopIndicator"),
  velocityLimits: document.getElementById("velocityLimits"),
  clientCount: document.getElementById("clientCount"),
  // WASD
  keyW: document.getElementById("keyW"),
  keyA: document.getElementById("keyA"),
  keyS: document.getElementById("keyS"),
  keyD: document.getElementById("keyD"),
  keySpace: document.getElementById("keySpace"),
  lastCommand: document.getElementById("lastCommand"),
};

hzCounters.lidar.element = document.getElementById("lidarHz");
hzCounters.imu.element = document.getElementById("imuHz");
hzCounters.odom.element = document.getElementById("odomHz");
hzCounters.battery.element = document.getElementById("batteryHz");

// =============================================================================
// connectWebSocket
// =============================================================================
export function connectWebSocket() {
  wsClient = new WebSocketClient(WS_URL, {
    onMessage: (rawData) => {
      const msg = decodeMessage(rawData);
      if (!msg) {
        addMessage("⚠️ 不正なメッセージを受信", "system");
        return;
      }
      handleMessage(msg);
      updateCounter();
    },
    onStateChange: (connected) => {
      if (connected) {
        addMessage("✅ サーバーに接続しました", "system");
        // 接続直後に安全状態を問い合わせ
        setTimeout(() => {
          sendMessage(createStatusCmd());
        }, 500);
      } else {
        addMessage("❌ 接続が閉じました", "system");
      }
      setConnectedState(connected);
    },
  });

  wsClient.connect();
}

export function disconnectWebSocket() {
  if (wsClient) wsClient.disconnect();
}

// =============================================================================
// handleMessage — メッセージルーティング（Step 5 拡張）
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
    // Step 5 追加
    case MessageType.SAFETY_STATUS:
      handleSafetyStatus(msg);
      break;
    default:
      addMessage(`⚠️ 不明なメッセージタイプ: ${msg.type}`, "system");
  }
}

// =============================================================================
// handleSensorData — センサーデータを各ビューアに振り分け
// =============================================================================
function handleSensorData(msg) {
  const data = msg.payload;
  if (!data) return;

  if ("ranges" in data) {
    lidarViewer.update(data);
    hzCounters.lidar.count++;
    return;
  }
  if ("accel_x" in data) {
    imuChart.update(data);
    hzCounters.imu.count++;
    return;
  }
  if ("pos_x" in data) {
    odomViewer.update(data);
    hzCounters.odom.count++;
    return;
  }
  if ("percentage" in data) {
    batteryGauge.update(data);
    hzCounters.battery.count++;
    return;
  }
}

// =============================================================================
// handleAdapterInfo — アダプター情報（Step 5 拡張）
// =============================================================================
function handleAdapterInfo(msg) {
  const info = msg.payload;
  addMessage(`🤖 アダプター: ${info.adapter_name} (接続: ${info.connected})`, "received");

  if (elements.adapterName) elements.adapterName.textContent = info.adapter_name;
  setRobotConnected(info.connected);

  // Step 5: E-Stop 状態も含まれる
  if ("estop_active" in info) {
    setEStopState(info.estop_active);
  }

  if (info.capabilities) {
    const caps = info.capabilities;
    addMessage(
      `  速度制御: ${caps.velocity_control ? "✅" : "❌"} | ` +
      `E-Stop: ${caps.estop ? "✅" : "❌"} | ` +
      `ナビ: ${caps.navigation ? "✅" : "❌"}`,
      "system"
    );
  }
}

// =============================================================================
// handleSafetyStatus — 安全状態の受信処理（Step 5 新規）
// =============================================================================
//
// 【安全状態メッセージの内容】
// {
//   estop: { active: bool, activated_at: string },
//   velocity_limits: { max_linear: number, max_angular: number },
//   operation_lock: { locked: bool, owner: string, operation: string },
//   adapter_connected: bool
// }
function handleSafetyStatus(msg) {
  const data = msg.payload;
  if (!data) return;

  // E-Stop 状態
  if (data.estop) {
    setEStopState(data.estop.active || data.estop.Active);
  }

  // 速度制限
  if (data.velocity_limits && elements.velocityLimits) {
    const lim = data.velocity_limits;
    elements.velocityLimits.textContent =
      `Lin: ${lim.max_linear?.toFixed(1) || "--"} m/s | Ang: ${lim.max_angular?.toFixed(1) || "--"} rad/s`;
  }

  addMessage("🛡️ 安全状態を更新しました", "system");
}

// =============================================================================
// handleCommandAck — コマンド応答
// =============================================================================
function handleCommandAck(msg) {
  const { status, description } = msg.payload;
  addMessage(`🤖 [${status}] ${description}`, "received");

  if (status === "connected") {
    setRobotConnected(true);
  } else if (status === "disconnected") {
    setRobotConnected(false);
  } else if (status === "stopped") {
    setEStopState(true);
    addMessage("🚨 緊急停止が実行されました", "system");
  } else if (status === "estop_released") {
    setEStopState(false);
    addMessage("✅ 緊急停止が解除されました", "system");
  }
}

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

// Step 5 新規: E-Stop 解除
export function sendEStopRelease() {
  if (!wsClient || !wsClient.isConnected) {
    addMessage("⚠️ サーバー未接続です", "system");
    return;
  }
  sendMessage(createEStopReleaseCmd());
  addMessage("✅ E-Stop 解除コマンドを送信しました", "sent");
}

export function sendRobotConnect() {
  sendMessage(createConnectCmd());
}

export function sendRobotDisconnect() {
  sendMessage(createDisconnectCmd());
}

// =============================================================================
// E-Stop 状態管理（Step 5 新規）
// =============================================================================
//
// 【E-Stop 状態の UI 反映】
// E-Stop がアクティブな場合:
//   - インジケータが赤く点灯
//   - 解除ボタンが有効になる
//   - WASD キーボードが無効化される
function setEStopState(active) {
  estopActive = active;

  if (elements.estopIndicator) {
    if (active) {
      elements.estopIndicator.textContent = "🛑 E-STOP アクティブ";
      elements.estopIndicator.className = "estop-indicator active";
    } else {
      elements.estopIndicator.textContent = "✅ 正常";
      elements.estopIndicator.className = "estop-indicator";
    }
  }

  // E-Stop 中は解除ボタンを有効に
  if (elements.btnEStopRelease) {
    elements.btnEStopRelease.disabled = !active;
  }
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
  if (estopActive) return; // E-Stop 中はキーボード無効

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
  if (el) el.classList.toggle("active", active);
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
    if (elements.btnEStopRelease) elements.btnEStopRelease.disabled = true;
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
// イベントリスナー
// =============================================================================
document.addEventListener("keydown", handleKeyDown);
document.addEventListener("keyup", handleKeyUp);

// =============================================================================
// グローバル公開
// =============================================================================
window.connectWebSocket = connectWebSocket;
window.disconnectWebSocket = disconnectWebSocket;
window.toggleKeyboardControl = toggleKeyboardControl;
window.sendEStop = sendEStop;
window.sendEStopRelease = sendEStopRelease;
window.sendRobotConnect = sendRobotConnect;
window.sendRobotDisconnect = sendRobotDisconnect;
