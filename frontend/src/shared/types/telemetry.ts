export interface TelemetryEntry {
  robotId: string;
  sensorType: string;
  payload: Record<string, unknown>;
  recordedAt: string;
}

export interface DatasetSession {
  id: string;
  robotId: string;
  name: string;
  createdAt: string;
  isActive: boolean;
  metadata?: Record<string, unknown>;
}
