// =============================================================================
// Step 2: 構造化メッセージ — app.js（メインアプリケーション）
// =============================================================================
//
// 【このファイルの概要】
// WebSocket 接続の管理、UI 操作、キーボード入力の処理を行うメインモジュール。
// protocol.js からメッセージ操作関数をインポートして使う。
//
// 【import 文とは？】
// ES Modules で他のファイルから機能を取り込む構文。
//
// import { 名前 } from "./ファイルパス.js";
//   → 指定した名前のエクスポートだけを取り込む（名前付きインポート）
//
// 【"./" の意味】
// 同じディレクトリを指す相対パス。
// "./protocol.js" = このファイルと同じフォルダの protocol.js
//
// 【注意: 拡張子 .js が必須】
// ブラウザの ES Modules では、import パスに拡張子を省略できない。
// Node.js では省略できるが、ブラウザでは明示的に .js を付ける必要がある。
//
// =============================================================================
import {
  MessageType,
  KeyBindings,
  createVelocityCmd,
  encodeMessage,
  decodeMessage,
  formatSensorData,
} from "./protocol.js";

// =============================================================================
// アプリケーション状態
// =============================================================================
//
// 【状態管理とは？】
// アプリケーションの「現在の状態」を変数で管理すること。
// React の useState、Vue の ref に近い概念。
// Step 2 ではシンプルにグローバル変数で管理する。
//
// 【let vs const の使い分け】
// let   — 値が変わる変数（ws は接続/切断で null ↔ WebSocket に変わる）
// const — 値が変わらない変数（DOM 要素の参照は変わらない）
let ws = null;           // WebSocket 接続オブジェクト
let sentCount = 0;       // 送信メッセージ数
let receivedCount = 0;   // 受信メッセージ数
let keyboardEnabled = false; // キーボード操作が有効か

const WS_URL = "ws://localhost:8080/ws";

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
  // センサーデータ表示
  sensorTemp: document.getElementById("sensorTemp"),
  sensorBattery: document.getElementById("sensorBattery"),
  sensorSpeed: document.getElementById("sensorSpeed"),
  sensorDistance: document.getElementById("sensorDistance"),
  // WASD キー表示
  keyW: document.getElementById("keyW"),
  keyA: document.getElementById("keyA"),
  keyS: document.getElementById("keyS"),
  keyD: document.getElementById("keyD"),
  keySpace: document.getElementById("keySpace"),
  // 最後のコマンド表示
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

  // --- メッセージ受信時 ---
  //
  // 【Step 1 からの変更点】
  // Step 1: event.data をそのまま表示
  // Step 2: JSON をデコードして、Type に応じた処理を実行
  ws.onmessage = function (event) {
    receivedCount++;
    updateCounter();

    // JSON 文字列をオブジェクトにデコード
    const msg = decodeMessage(event.data);
    if (!msg) {
      addMessage("⚠️ 不正なメッセージを受信", "system");
      return;
    }

    // メッセージタイプに応じた処理
    handleMessage(msg);
  };

  ws.onclose = function (event) {
    addMessage(
      `❌ 接続が閉じました（コード: ${event.code}）`,
      "system"
    );
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
// 【ディスパッチパターン】
// Go 側の readPump() の switch 文と対になる処理。
// サーバーが送信するメッセージタイプ:
//   - sensor_data  → センサー表示を更新
//   - command_ack  → コマンド応答をログに表示
//   - error        → エラーをログに表示
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

    default:
      addMessage(`⚠️ 不明なメッセージタイプ: ${msg.type}`, "system");
  }
}

// =============================================================================
// handleSensorData — センサーデータの受信処理
// =============================================================================
//
// 【Step 1 からの変更点】
// Step 1: "📊 センサーデータ | 温度: 23.5°C | ..." というテキストを表示
// Step 2: JSON の各フィールドを個別のUI要素に表示（リアルタイムダッシュボード風）
function handleSensorData(msg) {
  const formatted = formatSensorData(msg.payload);

  // 各センサー値をUIに反映
  if (elements.sensorTemp) elements.sensorTemp.textContent = formatted.temperature;
  if (elements.sensorBattery) elements.sensorBattery.textContent = formatted.battery;
  if (elements.sensorSpeed) elements.sensorSpeed.textContent = formatted.speed;
  if (elements.sensorDistance) elements.sensorDistance.textContent = formatted.distance;

  // バッテリー残量に応じて色を変える
  //
  // 【条件（三項）演算子 ? : とは？】
  // 条件 ? 真の場合の値 : 偽の場合の値
  // if-else を1行で書ける。Go にはこの構文がない（if-else を使う）。
  if (elements.sensorBattery) {
    const level = msg.payload.battery;
    elements.sensorBattery.style.color =
      level > 50 ? "#28a745" : level > 20 ? "#ffc107" : "#dc3545";
  }
}

// =============================================================================
// handleCommandAck — コマンド応答の表示
// =============================================================================
function handleCommandAck(msg) {
  const { status, description } = msg.payload;
  //
  // 【分割代入（Destructuring）とは？】
  // オブジェクトからプロパティを取り出して変数に代入する構文。
  // const { status, description } = msg.payload;
  // ↓ これと同じ
  // const status = msg.payload.status;
  // const description = msg.payload.description;
  addMessage(`🤖 [${status}] ${description}`, "received");
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
//
// 【コマンド送信の流れ】
// 1. createVelocityCmd() で構造化メッセージを作成
// 2. encodeMessage() で JSON 文字列に変換
// 3. ws.send() で WebSocket 経由で送信
//
// この3段階は Go 側の sendMessage() と対称的:
// 1. protocol.NewVelocityCmd() でメッセージ作成
// 2. codec.Encode() でバイト列に変換
// 3. conn.WriteMessage() で送信
export function sendVelocityCmd(linearX, linearY, angularZ) {
  if (!ws || ws.readyState !== WebSocket.OPEN) return;

  const msg = createVelocityCmd(linearX, linearY, angularZ);
  const json = encodeMessage(msg);
  ws.send(json);

  sentCount++;
  updateCounter();
}

// =============================================================================
// キーボード入力の処理
// =============================================================================
//
// 【WASD キーボード操作】
// ゲームでよく使われる WASD 配置でロボットを操作する。
// W = 前進、A = 左旋回、S = 後退、D = 右旋回、Space = 停止
//
// 【keydown と keyup イベント】
// keydown: キーが「押された」瞬間に発火
// keyup:   キーが「離された」瞬間に発火
//
// ここでは keydown でコマンドを送信する。
// 将来的には keyup で停止コマンドを送る実装も考えられる。

// toggleKeyboardControl — キーボード操作の ON/OFF を切り替え
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

// handleKeyDown — キーボードのキー押下を処理
//
// 【event.key とは？】
// 押されたキーの名前を表す文字列。
// "w", "a", "s", "d", " "（スペース）など。
// 大文字 "W" と小文字 "w" は区別される → .toLowerCase() で統一。
//
// 【event.repeat とは？】
// キーを押しっぱなしにすると、keydown イベントが連続で発火する。
// repeat が true の場合は押しっぱなしによるリピート。
// リピートの度にコマンドを送ると通信が多すぎるため、無視する。
function handleKeyDown(event) {
  if (!keyboardEnabled) return;
  if (event.repeat) return; // キーリピートを無視

  const key = event.key.toLowerCase();
  const binding = KeyBindings.get(key);

  if (binding) {
    // 対応する速度コマンドを送信
    sendVelocityCmd(binding.linearX, binding.linearY, binding.angularZ);

    // 押されたキーをUIでハイライト表示
    highlightKey(key, true);

    // 最後のコマンドを表示
    if (elements.lastCommand) {
      elements.lastCommand.textContent = binding.label;
    }

    // デフォルト動作を防止（スペースキーでページがスクロールするのを防ぐ）
    // 【preventDefault() とは？】
    // ブラウザのデフォルト動作を無効化する関数。
    // スペースキーのデフォルト動作 = ページの下スクロール
    // これを防がないと、操作するたびにページがスクロールしてしまう。
    event.preventDefault();
  }
}

// handleKeyUp — キーが離された時の処理
function handleKeyUp(event) {
  if (!keyboardEnabled) return;

  const key = event.key.toLowerCase();
  if (KeyBindings.has(key)) {
    highlightKey(key, false);
  }
}

// highlightKey — WASD キーのUIハイライト
//
// 【キーとDOM要素の対応】
// "w" → elements.keyW, "a" → elements.keyA, ...
// キー名からDOM要素を引く辞書（オブジェクト）を使う。
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

// addMessage — メッセージをログに追加
function addMessage(text, type) {
  const div = document.createElement("div");
  div.classList.add("message", type);

  const time = new Date().toLocaleTimeString();
  div.innerHTML = `<span class="timestamp">[${time}]</span> ${text}`;

  elements.messagesDiv.appendChild(div);
  elements.messagesDiv.scrollTop = elements.messagesDiv.scrollHeight;

  // メッセージが多くなりすぎたら古いものを削除
  //
  // 【なぜ削除するの？】
  // DOM要素が増え続けると、メモリを消費しブラウザが重くなる。
  // 200件を超えたら古いものから削除して、パフォーマンスを維持する。
  const MAX_MESSAGES = 200;
  while (elements.messagesDiv.children.length > MAX_MESSAGES) {
    elements.messagesDiv.removeChild(elements.messagesDiv.firstChild);
  }
}

// setConnectedState — UI の接続状態を更新
function setConnectedState(connected) {
  if (connected) {
    elements.statusDot.classList.add("connected");
    elements.statusText.textContent = `接続中 (${WS_URL})`;
    elements.btnConnect.disabled = true;
    elements.btnDisconnect.disabled = false;
    if (elements.btnKeyboard) elements.btnKeyboard.disabled = false;
  } else {
    elements.statusDot.classList.remove("connected");
    elements.statusText.textContent = "未接続";
    elements.btnConnect.disabled = false;
    elements.btnDisconnect.disabled = true;
    if (elements.btnKeyboard) elements.btnKeyboard.disabled = true;
    keyboardEnabled = false;
    if (elements.btnKeyboard) {
      elements.btnKeyboard.textContent = "🎮 キーボード OFF";
      elements.btnKeyboard.classList.remove("active");
    }
  }
}

// updateCounter — カウンター表示を更新
function updateCounter() {
  elements.counterDiv.textContent = `送信: ${sentCount} | 受信: ${receivedCount}`;
}

// =============================================================================
// イベントリスナーの登録
// =============================================================================
//
// 【addEventListener とは？】
// DOM要素にイベント（クリック、キー入力など）の処理を登録する関数。
// onclick="..." よりも推奨される方法:
// - 複数のリスナーを登録できる
// - HTMLとJSの分離（関心の分離）
// - removeEventListener で解除できる
//
// 【document にリスナーを付ける理由】
// キーボードイベントはページ全体で検知したいので、
// 特定のinput要素ではなく document に登録する。
document.addEventListener("keydown", handleKeyDown);
document.addEventListener("keyup", handleKeyUp);

// =============================================================================
// グローバルに公開（HTMLのonclickから呼び出せるようにする）
// =============================================================================
//
// 【window オブジェクトとは？】
// ブラウザの最上位オブジェクト。グローバルスコープに相当。
// ES Modules 内の関数はデフォルトでモジュールスコープに閉じている。
// HTML の onclick="connectWebSocket()" から呼ぶには、
// window.connectWebSocket = connectWebSocket; としてグローバルに公開する必要がある。
//
// 【より良い方法】
// onclick 属性の代わりに addEventListener を使うべき（Step 9 の React ではそうなる）。
// ここでは HTML の構造をシンプルに保つため、この方法を使う。
window.connectWebSocket = connectWebSocket;
window.disconnectWebSocket = disconnectWebSocket;
window.toggleKeyboardControl = toggleKeyboardControl;
