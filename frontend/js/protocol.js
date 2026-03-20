// =============================================================================
// Step 5: 安全パイプライン — protocol.js（拡張版）
// =============================================================================
//
// 【Step 4 からの変更点】
// 1. safety_status メッセージタイプを追加
// 2. estop_release メッセージ作成関数を追加
// 3. status（安全状態問い合わせ）メッセージ作成関数を追加
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
// メッセージタイプ定数（Step 5 追加分）
// =============================================================================
export const MessageType = Object.freeze({
  ...Step2Types,
  ADAPTER_INFO: "adapter_info",
  ESTOP: "estop",
  CONNECT: "connect",
  DISCONNECT: "disconnect",
  // Step 5 追加
  ESTOP_RELEASE: "estop_release",   // E-Stop 解除
  SAFETY_STATUS: "safety_status",   // 安全状態通知
  STATUS: "status",                 // 状態問い合わせ
});

// =============================================================================
// メッセージ作成関数
// =============================================================================

export function createEStopCmd() {
  return {
    type: MessageType.ESTOP,
    robot_id: "robot-01",
    timestamp: new Date().toISOString(),
    payload: {},
  };
}

// Step 5 新規: E-Stop 解除コマンド
export function createEStopReleaseCmd() {
  return {
    type: MessageType.ESTOP_RELEASE,
    robot_id: "robot-01",
    timestamp: new Date().toISOString(),
    payload: {},
  };
}

export function createConnectCmd() {
  return {
    type: MessageType.CONNECT,
    robot_id: "robot-01",
    timestamp: new Date().toISOString(),
    payload: {},
  };
}

export function createDisconnectCmd() {
  return {
    type: MessageType.DISCONNECT,
    robot_id: "robot-01",
    timestamp: new Date().toISOString(),
    payload: {},
  };
}

// Step 5 新規: 安全状態の問い合わせ
export function createStatusCmd() {
  return {
    type: MessageType.STATUS,
    robot_id: "robot-01",
    timestamp: new Date().toISOString(),
    payload: {},
  };
}

// =============================================================================
// フォーマット関数
// =============================================================================
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
