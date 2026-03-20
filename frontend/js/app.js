// =============================================================================
// Step 6: REST API + ハッシュルーター — app.js
// =============================================================================
//
// 【Step 5 からの変更点】
// 1. ハッシュルーター導入 → 複数ページ構成
// 2. REST API クライアント追加（fetch() でバックエンドと通信）
// 3. ロボット一覧・登録ページの追加
// 4. リアルタイム制御を「ページ」として分離
//
// 【ファイル構成の変化】
// Step 5:
//   app.js ← 全ロジックが1ファイル
//
// Step 6:
//   app.js ← ルーター + グローバル状態 + WS 管理
//   router.js ← ルーター本体
//   api.js ← REST API クライアント
//   pages/robot-list.js ← ロボット一覧ページ
//   pages/robot-form.js ← ロボット登録/編集ページ
//   pages/control.js ← リアルタイム制御ページ
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
import { Router } from "./router.js";
import { renderRobotListPage } from "./pages/robot-list.js";
import { renderRobotFormPage } from "./pages/robot-form.js";
import { renderControlPage } from "./pages/control.js";

// =============================================================================
// ルーターのセットアップ
// =============================================================================
//
// 【ルーティングテーブル】
// URL ハッシュとページ描画関数の対応表。
//
//   #/           → ダッシュボード（ロボット一覧）
//   #/robots     → ロボット一覧
//   #/robots/new → ロボット新規登録
//   #/robots/edit→ ロボット編集（パスパラメータで ID 指定）
//   #/control    → リアルタイム制御（Step 5 の画面）
//
const router = new Router("page-content");

router
  .addRoute("/", renderRobotListPage)
  .addRoute("/robots", renderRobotListPage)
  .addRoute("/robots/new", renderRobotFormPage)
  .addRoute("/robots/edit", renderRobotFormPage)
  .addRoute("/control", (container) => {
    // 制御ページは特殊: 描画後にセンサーを初期化する
    renderControlPage(container);
    initSensorsAfterRender();
  })
  .setNotFound((container, { path }) => {
    container.innerHTML = `
      <div class="error-message">
        <h2>404 Not Found</h2>
        <p>ページ「${path}」は見つかりません。</p>
        <a href="#/" class="btn btn-primary">ホームに戻る</a>
      </div>
    `;
  });

// =============================================================================
// センサービューアの遅延初期化
// =============================================================================
//
// 【なぜ遅延初期化？】
// Step 5 では最初から全センサーの Canvas が HTML にあった。
// Step 6 ではルーターでページを切り替えるため、
// センサーの Canvas は「制御ページ」に遷移した時点でDOMに追加される。
// → Canvas が存在する前に初期化するとエラーになる。
//
// 解決策: 制御ページの描画後に初期化する。
//
let lidarViewer = null;
let imuChart = null;
let batteryGauge = null;
let odomViewer = null;

async function initSensorsAfterRender() {
  // 動的 import — モジュールを必要な時だけ読み込む
  const { LidarViewer } = await import("./sensors/lidar-viewer.js");
  const { ImuChart } = await import("./sensors/imu-chart.js");
  const { BatteryGauge } = await import("./sensors/battery-gauge.js");
  const { OdometryViewer } = await import("./sensors/odometry.js");

  lidarViewer = new LidarViewer("lidarCanvas");
  imuChart = new ImuChart("imuCanvas", "imuLegend");
  batteryGauge = new BatteryGauge("batteryGauge");
  odomViewer = new OdometryViewer("odomCanvas", "odomValues");

  // Hz カウンター要素を再取得
  hzCounters.lidar.element = document.getElementById("lidarHz");
  hzCounters.imu.element = document.getElementById("imuHz");
  hzCounters.odom.element = document.getElementById("odomHz");
  hzCounters.battery.element = document.getElementById("batteryHz");

  // DOM 要素を再取得
  refreshElements();
}

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
let estopActive = false;

const WS_HOST = window.location.hostname || "localhost";
const WS_URL = `ws://${WS_HOST}:8080/ws`;

// =============================================================================
// DOM 要素のキャッシュ
// =============================================================================
//
// 【なぜ refreshElements() が必要？】
// ルーター がページを切り替えると、container.innerHTML が書き換わる。
// つまり古い DOM ノードは破棄され、新しいノードが生成される。
// getElementById で取得したノードは「古いノード」への参照なので、
// ページ遷移後は参照が無効になる。
//
// → ページ遷移のたびに DOM 参照を更新する必要がある。
//
let elements = {};

function refreshElements() {
  elements = {
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
    estopIndicator: document.getElementById("estopIndicator"),
    velocityLimits: document.getElementById("velocityLimits"),
    keyW: document.getElementById("keyW"),
    keyA: document.getElementById("keyA"),
    keyS: document.getElementById("keyS"),
    keyD: document.getElementById("keyD"),
    keySpace: document.getElementById("keySpace"),
    lastCommand: document.getElementById("lastCommand"),
  };

  // WebSocket が接続中ならボタン状態を復元
  if (wsClient && wsClient.isConnected) {
    setConnectedState(true);
    if (estopActive) setEStopState(true);
  }
}

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
// handleMessage — メッセージルーティング
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

  if ("ranges" in data && lidarViewer) {
    lidarViewer.update(data);
    hzCounters.lidar.count++;
    return;
  }
  if ("accel_x" in data && imuChart) {
    imuChart.update(data);
    hzCounters.imu.count++;
    return;
  }
  if ("pos_x" in data && odomViewer) {
    odomViewer.update(data);
    hzCounters.odom.count++;
    return;
  }
  if ("percentage" in data && batteryGauge) {
    batteryGauge.update(data);
    hzCounters.battery.count++;
    return;
  }
}

// =============================================================================
// handleAdapterInfo
// =============================================================================
function handleAdapterInfo(msg) {
  const info = msg.payload;
  addMessage(`🤖 アダプター: ${info.adapter_name} (接続: ${info.connected})`, "received");

  if (elements.adapterName) elements.adapterName.textContent = info.adapter_name;
  setRobotConnected(info.connected);

  if ("estop_active" in info) {
    setEStopState(info.estop_active);
  }
}

// =============================================================================
// handleSafetyStatus
// =============================================================================
function handleSafetyStatus(msg) {
  const data = msg.payload;
  if (!data) return;

  if (data.estop) {
    setEStopState(data.estop.active || data.estop.Active);
  }

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
// E-Stop 状態管理
// =============================================================================
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

  if (elements.btnEStopRelease) {
    elements.btnEStopRelease.disabled = !active;
  }
}

// =============================================================================
// キーボード操作
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
  if (estopActive) return;

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
// グローバル公開（onclick で呼ぶための関数）
// =============================================================================
window.connectWebSocket = connectWebSocket;
window.disconnectWebSocket = disconnectWebSocket;
window.toggleKeyboardControl = toggleKeyboardControl;
window.sendEStop = sendEStop;
window.sendEStopRelease = sendEStopRelease;
window.sendRobotConnect = sendRobotConnect;
window.sendRobotDisconnect = sendRobotDisconnect;

// =============================================================================
// アプリの起動
// =============================================================================
router.start();
