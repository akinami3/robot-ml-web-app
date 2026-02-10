// Robot types
export type RobotState = 'IDLE' | 'MOVING' | 'PAUSED' | 'ERROR' | 'CHARGING';
export type RobotStatus = 'idle' | 'active' | 'charging' | 'error' | 'offline';

export interface Position {
  x: number;
  y: number;
  theta?: number;
}

export interface Capabilities {
  supports_pause: boolean;
  supports_docking: boolean;
}

export interface Robot {
  id: number;
  robot_id?: string;
  name: string;
  serial_number: string;
  vendor: string;
  model: string | null;
  state?: RobotState;
  status: RobotStatus;
  battery: number;
  pos_x?: number;
  pos_y?: number;
  pos_theta?: number;
  position?: Position;
  capabilities?: Capabilities | null;
  is_online: boolean;
  last_seen: string | null;
  created_at: string;
}

export interface RobotCreate {
  name: string;
  serial_number: string;
  model?: string;
  vendor?: string;
}

export interface RobotListResponse {
  total: number;
  robots: Robot[];
}

// Mission types
export type MissionStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'cancelled' | 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';

export interface Waypoint {
  x: number;
  y: number;
  action?: string;
}

export interface Mission {
  id: number;
  mission_id?: string;
  name: string;
  description?: string;
  robot_id: number;
  status: MissionStatus;
  priority?: number;
  waypoints?: Waypoint[];
  goal_x?: number;
  goal_y?: number;
  goal_theta?: number;
  created_by?: number | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
}

export type MissionListResponse = {
  total: number;
  missions: Mission[];
};

export interface MissionCreate {
  name: string;
  description?: string;
  robot_id: number;
  priority?: number;
  waypoints: Waypoint[];
}

// User types
export type UserRole = 'ADMIN' | 'OPERATOR' | 'VIEWER';

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

// Auth types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

// Command types
export interface MoveCommand {
  robot_id: string;
  goal: Position;
}

export interface CommandResponse {
  success: boolean;
  message: string;
  command_id?: string;
}

// API Error
export interface ApiError {
  detail: string;
}

// Sensor Data Recording types
export interface SensorDataRecord {
  id: number;
  robot_id: string;
  recorded_at: string;
  sensor_data: Record<string, number>;
  control_data: Record<string, number>;
  created_at: string;
}

export interface SensorDataStats {
  robot_id: string;
  total_records: number;
  earliest: string | null;
  latest: string | null;
}

// Command Data Recording types
export interface CommandDataRecord {
  id: number;
  robot_id: string;
  recorded_at: string;
  command: string;
  parameters: Record<string, number>;
  user_id: string | null;
  success: boolean;
  error_message: string | null;
  robot_state_before: Record<string, number>;
  created_at: string;
}

export interface CommandDataStats {
  robot_id: string;
  total_commands: number;
  earliest: string | null;
  latest: string | null;
  success_count: number;
  failure_count: number;
}

export interface CommandTypeStats {
  command: string;
  count: number;
  success_rate: number;
}

// ML Training Pair types
export interface TrainingPair {
  timestamp: string;
  state: Record<string, number>;
  action: {
    command: string;
    parameters: Record<string, number>;
  };
  user_id: string | null;
}

export interface TrainingPairsResponse {
  robot_id: string;
  total_pairs: number;
  pairs: TrainingPair[];
}
