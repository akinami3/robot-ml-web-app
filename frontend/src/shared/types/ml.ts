export interface TrainingRun {
  id: string;
  status: string;
  modelName: string;
  datasetSessionId?: string | null;
}

export interface MetricSnapshot {
  step: number;
  name: string;
  value: number;
  timestamp: string;
}
