// =============================================================================
// Step 3: Adapter パターン — protocol.js
// =============================================================================
//
// 【Step 2 からの変更点】
// 1. adapter_info メッセージタイプを追加
// 2. estop / connect / disconnect メッセージ作成関数を追加
// 3. formatSensorData を Adapter 形式に対応
//
// =============================================================================
import {
  MessageType as Step2Types,
  KeyBindings,
  createVelocityCmd,
  encodeMessage,
  decodeMessage,
} from "./protocol-base.js";

// =============================================================================
// メッセージタイプ定数（Step 3 で追加分を含む）
// =============================================================================
//
// 【スプレッド構文 ...obj とは？】
// オブジェクトの全プロパティを展開して新しいオブジェクトに入れる。
// { ...Step2Types } → Step2Types の全プロパティをコピー。
// そこに新しいプロパティを追加して拡張する。
export const MessageType = Object.freeze({
  ...Step2Types,
  ADAPTER_INFO: "adapter_info",   // サーバー → クライアント: アダプター情報
  ESTOP: "estop",                 // クライアント → サーバー: 緊急停止
  CONNECT: "connect",             // クライアント → サーバー: ロボット接続
  DISCONNECT: "disconnect",       // クライアント → サーバー: ロボット切断
});

// =============================================================================
// createEStopCmd — 緊急停止コマンドを作成
// =============================================================================
export function createEStopCmd() {
  return {
    type: MessageType.ESTOP,
    robot_id: "robot-01",
    timestamp: new Date().toISOString(),
    payload: {},
  };
}

// =============================================================================
// createConnectCmd — ロボット接続コマンドを作成
// =============================================================================
export function createConnectCmd() {
  return {
    type: MessageType.CONNECT,
    robot_id: "robot-01",
    timestamp: new Date().toISOString(),
    payload: {},
  };
}

// =============================================================================
// createDisconnectCmd — ロボット切断コマンドを作成
// =============================================================================
export function createDisconnectCmd() {
  return {
    type: MessageType.DISCONNECT,
    robot_id: "robot-01",
    timestamp: new Date().toISOString(),
    payload: {},
  };
}

// =============================================================================
// formatOdomData — オドメトリデータを表示用に変換
// =============================================================================
//
// 【Step 3 のセンサーデータ形式】
// MockAdapter は adapter.SensorData を送信し、server の sensorDataToMessage で
// protocol.Message に変換される。Payload は map[string]any（= JS のオブジェクト）。
//
// /odom トピック:
//   { pos_x, pos_y, theta, linear_x, angular_z, speed }
//
// /battery トピック:
//   { percentage, voltage, temperature }
export function formatOdomData(data) {
  return {
    posX: `${(data.pos_x || 0).toFixed(2)} m`,
    posY: `${(data.pos_y || 0).toFixed(2)} m`,
    theta: `${((data.theta || 0) * 180 / Math.PI).toFixed(1)}°`,
    speed: `${(data.speed || 0).toFixed(2)} m/s`,
    linearX: `${(data.linear_x || 0).toFixed(2)} m/s`,
    angularZ: `${(data.angular_z || 0).toFixed(2)} rad/s`,
  };
}

export function formatBatteryData(data) {
  return {
    percentage: `${(data.percentage || 0).toFixed(0)}%`,
    voltage: `${(data.voltage || 0).toFixed(1)}V`,
    temperature: `${(data.temperature || 0).toFixed(1)}°C`,
  };
}

// Step 2 の関数を再エクスポート
export { KeyBindings, createVelocityCmd, encodeMessage, decodeMessage };
