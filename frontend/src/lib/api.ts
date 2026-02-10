import { Token, User, Robot, RobotListResponse, Mission, MissionListResponse, MissionCreate, RobotCreate, CommandResponse, Position } from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class ApiClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Auth
  async login(username: string, password: string): Promise<Token> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail);
    }

    return response.json();
  }

  async register(email: string, password: string, fullName: string): Promise<User> {
    const response = await fetch(`${API_URL}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
        full_name: fullName,
      }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Registration failed' }));
      throw new Error(error.detail);
    }

    return response.json();
  }

  async getMe(): Promise<User> {
    return this.fetch<User>('/api/v1/auth/me');
  }

  // Robots
  async getRobots(params?: { skip?: number; limit?: number; vendor?: string; state?: string }): Promise<RobotListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.vendor) searchParams.append('vendor', params.vendor);
    if (params?.state) searchParams.append('state', params.state);

    const query = searchParams.toString();
    return this.fetch<RobotListResponse>(`/api/v1/robots${query ? `?${query}` : ''}`);
  }

  async getRobot(robotId: string): Promise<Robot> {
    return this.fetch<Robot>(`/api/v1/robots/${robotId}`);
  }

  async moveRobot(robotId: string, goal: Position): Promise<CommandResponse> {
    return this.fetch<CommandResponse>(`/api/v1/robots/${robotId}/move`, {
      method: 'POST',
      body: JSON.stringify({ robot_id: robotId, goal }),
    });
  }

  async stopRobot(robotId: string): Promise<CommandResponse> {
    return this.fetch<CommandResponse>(`/api/v1/robots/${robotId}/stop`, {
      method: 'POST',
    });
  }

  async createRobot(robot: RobotCreate): Promise<Robot> {
    return this.fetch<Robot>('/api/v1/robots', {
      method: 'POST',
      body: JSON.stringify(robot),
    });
  }

  async deleteRobot(robotId: number): Promise<void> {
    return this.fetch<void>(`/api/v1/robots/${robotId}`, {
      method: 'DELETE',
    });
  }

  async sendCommand(robotId: number, command: string, payload: Record<string, unknown>): Promise<CommandResponse> {
    return this.fetch<CommandResponse>(`/api/v1/robots/${robotId}/command`, {
      method: 'POST',
      body: JSON.stringify({ command, payload }),
    });
  }

  // Missions
  async getMissions(params?: { skip?: number; limit?: number; status?: string; robot_id?: string }): Promise<MissionListResponse> {
    const searchParams = new URLSearchParams();
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.status) searchParams.append('status', params.status);
    if (params?.robot_id) searchParams.append('robot_id', params.robot_id);

    const query = searchParams.toString();
    return this.fetch<MissionListResponse>(`/api/v1/missions${query ? `?${query}` : ''}`);
  }

  async createMission(mission: MissionCreate): Promise<Mission> {
    return this.fetch<Mission>('/api/v1/missions', {
      method: 'POST',
      body: JSON.stringify(mission),
    });
  }

  async cancelMission(missionId: string): Promise<Mission> {
    return this.fetch<Mission>(`/api/v1/missions/${missionId}/cancel`, {
      method: 'POST',
    });
  }

  async deleteMission(missionId: number): Promise<void> {
    return this.fetch<void>(`/api/v1/missions/${missionId}`, {
      method: 'DELETE',
    });
  }

  // Sensor Data (recorded data from Backend DB)
  async getSensorData(params?: {
    robot_id?: string;
    start_time?: string;
    end_time?: string;
    skip?: number;
    limit?: number;
  }): Promise<{ total: number; records: SensorDataRecord[] }> {
    const searchParams = new URLSearchParams();
    if (params?.robot_id) searchParams.append('robot_id', params.robot_id);
    if (params?.start_time) searchParams.append('start_time', params.start_time);
    if (params?.end_time) searchParams.append('end_time', params.end_time);
    if (params?.skip) searchParams.append('skip', params.skip.toString());
    if (params?.limit) searchParams.append('limit', params.limit.toString());

    const query = searchParams.toString();
    return this.fetch(`/api/v1/sensor-data${query ? `?${query}` : ''}`);
  }

  async getSensorDataStats(): Promise<SensorDataStats[]> {
    return this.fetch('/api/v1/sensor-data/stats');
  }
}

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

export const api = new ApiClient();
