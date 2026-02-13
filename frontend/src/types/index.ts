/**
 * Shared TypeScript types for the Robot AI Web Application.
 */

// ─── Auth ──────────────────────────────────────────────────────────────────

export type UserRole = "admin" | "operator" | "viewer";

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// ─── Robot ─────────────────────────────────────────────────────────────────

export type RobotState =
  | "disconnected"
  | "connecting"
  | "idle"
  | "moving"
  | "error"
  | "emergency_stopped";

export interface Robot {
  id: string;
  name: string;
  adapter_type: string;
  state: RobotState;
  capabilities: string[];
  battery_level: number | null;
  last_seen: string | null;
  created_at: string;
}

// ─── Sensor Data ───────────────────────────────────────────────────────────

export type SensorType =
  | "lidar"
  | "camera"
  | "imu"
  | "odometry"
  | "battery"
  | "gps"
  | "point_cloud"
  | "joint_state";

export interface SensorData {
  id: string;
  robot_id: string;
  sensor_type: SensorType;
  data: Record<string, unknown>;
  timestamp: string;
  session_id: string | null;
  sequence_number: number;
}

// ─── WebSocket Messages ────────────────────────────────────────────────────

export type WSMessageType =
  | "auth"
  | "auth_response"
  | "ping"
  | "pong"
  | "velocity_cmd"
  | "nav_goal"
  | "nav_cancel"
  | "estop"
  | "estop_response"
  | "lock_acquire"
  | "lock_release"
  | "lock_response"
  | "sensor_data"
  | "robot_status"
  | "error";

export interface WSMessage {
  type: WSMessageType;
  robot_id?: string;
  payload: Record<string, unknown>;
  timestamp?: number;
}

export interface VelocityCommand {
  linear_x: number;
  linear_y: number;
  angular_z: number;
}

export interface NavigationGoal {
  x: number;
  y: number;
  theta: number;
}

// ─── Dataset ───────────────────────────────────────────────────────────────

export interface Dataset {
  id: string;
  name: string;
  description: string;
  owner_id: string;
  status: string;
  sensor_types: string[];
  robot_ids: string[];
  start_time: string | null;
  end_time: string | null;
  record_count: number;
  size_bytes: number;
  tags: string[];
  created_at: string;
}

// ─── Recording ─────────────────────────────────────────────────────────────

export interface RecordingSession {
  id: string;
  robot_id: string;
  user_id: string;
  is_active: boolean;
  record_count: number;
  size_bytes: number;
  started_at: string;
  stopped_at: string | null;
  config: {
    sensor_types: string[];
    enabled: boolean;
  };
}

// ─── RAG ───────────────────────────────────────────────────────────────────

export interface RAGDocument {
  id: string;
  title: string;
  source: string;
  file_type: string;
  file_size: number;
  chunk_count: number;
  created_at: string;
}

export interface RAGQueryResult {
  answer: string;
  sources: Array<{
    chunk_id: string;
    document_id: string;
    similarity: number;
    preview: string;
  }>;
  context_used: boolean;
}

// ─── Audit ─────────────────────────────────────────────────────────────────

export interface AuditLog {
  id: string;
  user_id: string;
  action: string;
  resource_type: string;
  resource_id: string;
  details: Record<string, unknown>;
  ip_address: string;
  timestamp: string;
}
