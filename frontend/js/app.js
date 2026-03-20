// =============================================================================
// Step 3: Adapter パターン — app.js（メインアプリケーション）
// =============================================================================
//
// 【Step 2 からの変更点】
// 1. adapter_info メッセージへの対応（接続時にロボット情報を受信）
// 2. 緊急停止（E-Stop）ボタンの処理
// 3. ロボット接続/切断をUIから操作
// 4. オドメトリ + バッテリーのセンサー表示
// 5. Docker 環境対応（WSホスト自動判定）
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
  formatOdomData,
  formatBatteryData,
} from "./protocol.js";

// =============================================================================
// アプリケーション状態
// =============================================================================
let ws = null;
let sentCount = 0;
let receivedCount = 0;
let keyboardEnabled = false;

// 【Docker 環境対応】
// ブラウザのホスト名に応じて WebSocket 接続先を決定。
// Docker Compose では frontend が nginx:3000、gateway が gateway:8080 で動く。
// ブラウザから見ると:
//   - ローカル開発: ws://localhost:8080/ws
//   - Docker: ws://localhost:8080/ws（ポートマッピング経由）
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
  // Step 3 追加: ロボット関連
  btnRobotConnect: document.getElementById("btnRobotConnect"),
  btnRobotDisconnect: document.getElementById("btnRobotDisconnect"),
  btnEStop: document.getElementById("btnEStop"),
  robotStatus: document.getElementById("robotStatus"),
  adapterName: document.getElementById("adapterName"),
  // Step 3: オドメトリ表示
  odomPosX: document.getElementById("odomPosX"),
  odomPosY: document.getElementById("odomPosY"),
  odomTheta: document.getElementById("odomTheta"),
  odomSpeed: document.getElementById("odomSpeed"),
  // Step 3: バッテリー表示
  batteryPercent: document.getElementById("batteryPercent"),
  batteryVoltage: document.getElementById("batteryVoltage"),
  batteryTemp: document.getElementById("batteryTemp"),
  batteryBar: document.getElementById("batteryBar"),
  // WASD キー表示
  keyW: document.getElementById("keyW"),
  keyA: document.getElementById("keyA"),
  keyS: document.getElementById("keyS"),
  keyD: document.getElementById("keyD"),
  keySpace: document.getElementById("keySpace"),
  lastCommand: document.getElementById("lastCommand"),
};

// =============================================================================
// connectWebSocket — WebSocket 接続を確立
// =============================================================================
export function connectWebSocket() {
  ws = new WebSocket(WS_URL);

  ws.onopen = function () {
    addMessage("✅ サーバーに接続しました", "system");
    setConnectedState(true);
  };

  ws.onmessage = function (event) {
    receivedCount++;
    updateCounter();

    const msg = decodeMessage(event.data);
    if (!msg) {
      addMessage("⚠️ 不正なメッセージを受信", "system");
      return;
    }

    handleMessage(msg);
  };

  ws.onclose = function (event) {
    addMessage(`❌ 接続が閉じました（コード: ${event.code}）`, "system");
    setConnectedState(false);
    ws = null;
  };

  ws.onerror = function () {
    addMessage("⚠️ WebSocket エラーが発生しました", "system");
  };
}

// =============================================================================
// disconnectWebSocket — WebSocket 接続を切断
// =============================================================================
export function disconnectWebSocket() {
  if (ws) {
    ws.close(1000, "ユーザーが切断しました");
  }
}

// =============================================================================
// handleMessage — 受信メッセージを Type に応じて処理
// =============================================================================
//
// 【Step 2 からの変更点】
// adapter_info メッセージ対応を追加。
// sensor_data の処理を Adapter 形式に対応。
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
// handleAdapterInfo — アダプター情報の受信処理
// =============================================================================
//
// 【Step 3 で新規追加】
// 接続直後にサーバーからアダプター情報が送られてくる。
// ロボットの能力を知ることで、UIを適切に設定できる。
function handleAdapterInfo(msg) {
  const info = msg.payload;
  addMessage(`🤖 アダプター: ${info.adapter_name} (接続: ${info.connected})`, "received");

  // アダプター名を表示
  if (elements.adapterName) {
    elements.adapterName.textContent = info.adapter_name;
  }

  // ロボット接続状態を更新
  setRobotConnected(info.connected);

  // 能力情報をログに表示
  if (info.capabilities) {
    const caps = info.capabilities;
    addMessage(
      `  速度制御: ${caps.velocity_control ? "✅" : "❌"} | ` +
      `E-Stop: ${caps.estop ? "✅" : "❌"} | ` +
      `ナビ: ${caps.navigation ? "✅" : "❌"}`,
      "system"
    );
    if (caps.max_linear) {
      addMessage(
        `  速度上限: linear=${caps.max_linear} m/s, angular=${caps.max_angular} rad/s`,
        "system"
      );
    }
  }
}

// =============================================================================
// handleSensorData — センサーデータの受信処理（Step 3 版）
// =============================================================================
//
// 【Step 2 からの変更点】
// Step 2: 固定的な temperature, battery, speed, distance フィールド
// Step 3: Adapter の SensorData 形式（payload が map[string]any）
//
// msg.payload にはセンサーデータの map がそのまま入っている。
// data_type フィールドでデータの種類を判別する。
//
// ただし、Step 3 の sensorDataToMessage では msg.payload = data.Data なので
// data_type は msg に直接含まれない。
// 代わりに payload の内容で判別する。
function handleSensorData(msg) {
  const data = msg.payload;
  if (!data) return;

  // オドメトリデータの判定: pos_x が含まれている
  if ("pos_x" in data) {
    const formatted = formatOdomData(data);
    if (elements.odomPosX) elements.odomPosX.textContent = formatted.posX;
    if (elements.odomPosY) elements.odomPosY.textContent = formatted.posY;
    if (elements.odomTheta) elements.odomTheta.textContent = formatted.theta;
    if (elements.odomSpeed) elements.odomSpeed.textContent = formatted.speed;
  }

  // バッテリーデータの判定: percentage が含まれている
  if ("percentage" in data) {
    const formatted = formatBatteryData(data);
    if (elements.batteryPercent) elements.batteryPercent.textContent = formatted.percentage;
    if (elements.batteryVoltage) elements.batteryVoltage.textContent = formatted.voltage;
    if (elements.batteryTemp) elements.batteryTemp.textContent = formatted.temperature;

    // バッテリーバーの更新
    const pct = data.percentage || 0;
    if (elements.batteryBar) {
      elements.batteryBar.style.width = `${pct}%`;
      // 残量に応じて色を変える
      if (pct > 50) {
        elements.batteryBar.style.backgroundColor = "#28a745";
      } else if (pct > 20) {
        elements.batteryBar.style.backgroundColor = "#ffc107";
      } else {
        elements.batteryBar.style.backgroundColor = "#dc3545";
      }
    }
  }
}

// =============================================================================
// handleCommandAck — コマンド応答の表示
// =============================================================================
function handleCommandAck(msg) {
  const { status, description } = msg.payload;
  addMessage(`🤖 [${status}] ${description}`, "received");

  // ロボット接続/切断に応じてUIを更新
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
// sendVelocityCmd — 速度コマンドを送信
// =============================================================================
export function sendVelocityCmd(linearX, linearY, angularZ) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;

  const msg = createVelocityCmd(linearX, linearY, angularZ);
  const json = encodeMessage(msg);
  ws.send(json);

  sentCount++;
  updateCounter();
}

// =============================================================================
// sendEStop — 緊急停止コマンドを送信
// =============================================================================
//
// 【緊急停止（E-Stop）とは？】
// ロボットを即座に停止させるための安全機能。
// 実際のロボットにはハードウェアのE-Stopボタンがある。
// このソフトウェア版は、WebSocket 経由でサーバーに停止命令を送る。
export function sendEStop() {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    addMessage("⚠️ サーバー未接続です", "system");
    return;
  }

  const msg = createEStopCmd();
  const json = encodeMessage(msg);
  ws.send(json);

  sentCount++;
  updateCounter();
  addMessage("🚨 緊急停止コマンドを送信しました", "sent");
}

// =============================================================================
// sendRobotConnect / sendRobotDisconnect — ロボット接続管理
// =============================================================================
export function sendRobotConnect() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;

  const msg = createConnectCmd();
  ws.send(encodeMessage(msg));
  sentCount++;
  updateCounter();
}

export function sendRobotDisconnect() {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;

  const msg = createDisconnectCmd();
  ws.send(encodeMessage(msg));
  sentCount++;
  updateCounter();
}

// =============================================================================
// キーボード入力の処理（Step 2 と共通）
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
    elements.statusDot.classList.add("connected");
    elements.statusText.textContent = `接続中 (${WS_URL})`;
    elements.btnConnect.disabled = true;
    elements.btnDisconnect.disabled = false;
    if (elements.btnKeyboard) elements.btnKeyboard.disabled = false;
    if (elements.btnRobotConnect) elements.btnRobotConnect.disabled = false;
    if (elements.btnRobotDisconnect) elements.btnRobotDisconnect.disabled = false;
    if (elements.btnEStop) elements.btnEStop.disabled = false;
  } else {
    elements.statusDot.classList.remove("connected");
    elements.statusText.textContent = "未接続";
    elements.btnConnect.disabled = false;
    elements.btnDisconnect.disabled = true;
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

// setRobotConnected — ロボット接続状態のUI更新
function setRobotConnected(connected) {
  if (elements.robotStatus) {
    elements.robotStatus.textContent = connected ? "🟢 接続中" : "🔴 未接続";
    elements.robotStatus.style.color = connected ? "#28a745" : "#dc3545";
  }
}

function updateCounter() {
  elements.counterDiv.textContent = `送信: ${sentCount} | 受信: ${receivedCount}`;
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
