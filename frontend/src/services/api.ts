/**
 * API client using Axios.
 */

import axios from "axios";
import { useAuthStore } from "@/stores/authStore";
import type {
  AuthTokens,
  Dataset,
  RAGDocument,
  RAGQueryResult,
  RecordingSession,
  Robot,
  SensorData,
  User,
} from "@/types";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

// Request interceptor - attach token
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const store = useAuthStore.getState();
      if (store.refreshToken) {
        try {
          const res = await axios.post("/api/v1/auth/refresh", {
            refresh_token: store.refreshToken,
          });
          store.setTokens(res.data);
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api.request(error.config);
        } catch {
          store.logout();
        }
      } else {
        store.logout();
      }
    }
    return Promise.reject(error);
  }
);

// ─── Auth ──────────────────────────────────────────────────────────────────

export const authApi = {
  login: (username: string, password: string) =>
    api.post<AuthTokens>("/auth/login", { username, password }),
  register: (data: { username: string; email: string; password: string }) =>
    api.post<User>("/auth/register", data),
  me: () => api.get<User>("/auth/me"),
};

// ─── Robots ────────────────────────────────────────────────────────────────

export const robotApi = {
  list: () => api.get<Robot[]>("/robots"),
  get: (id: string) => api.get<Robot>(`/robots/${id}`),
  create: (data: { name: string; adapter_type: string }) =>
    api.post<Robot>("/robots", data),
  update: (id: string, data: Partial<Robot>) =>
    api.patch<Robot>(`/robots/${id}`, data),
  delete: (id: string) => api.delete(`/robots/${id}`),
};

// ─── Sensors ───────────────────────────────────────────────────────────────

export const sensorApi = {
  query: (params: {
    robot_id: string;
    sensor_type?: string;
    limit?: number;
  }) => api.get<SensorData[]>("/sensors/data", { params }),
  latest: (robot_id: string, sensor_type: string) =>
    api.get<SensorData | null>("/sensors/data/latest", {
      params: { robot_id, sensor_type },
    }),
  types: () => api.get<Array<{ value: string; name: string }>>("/sensors/types"),
};

// ─── Datasets ──────────────────────────────────────────────────────────────

export const datasetApi = {
  list: () => api.get<Dataset[]>("/datasets"),
  get: (id: string) => api.get<Dataset>(`/datasets/${id}`),
  create: (data: {
    name: string;
    description: string;
    robot_ids: string[];
    sensor_types: string[];
    tags?: string[];
  }) => api.post<Dataset>("/datasets", data),
  export: (id: string, format: string) =>
    api.post(`/datasets/${id}/export`, { format }),
  delete: (id: string) => api.delete(`/datasets/${id}`),
};

// ─── Recordings ────────────────────────────────────────────────────────────

export const recordingApi = {
  list: () => api.get<RecordingSession[]>("/recordings"),
  get: (id: string) => api.get<RecordingSession>(`/recordings/${id}`),
  start: (data: {
    robot_id: string;
    sensor_types?: string[];
  }) => api.post<RecordingSession>("/recordings", data),
  stop: (id: string) =>
    api.post<RecordingSession>(`/recordings/${id}/stop`),
};

// ─── RAG ───────────────────────────────────────────────────────────────────

export const ragApi = {
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return api.post<RAGDocument>("/rag/documents", form, {
      headers: { "Content-Type": "multipart/form-data" },
    });
  },
  listDocuments: () => api.get<RAGDocument[]>("/rag/documents"),
  deleteDocument: (id: string) => api.delete(`/rag/documents/${id}`),
  query: (question: string, top_k?: number) =>
    api.post<RAGQueryResult>("/rag/query", { question, top_k }),
};

export default api;
