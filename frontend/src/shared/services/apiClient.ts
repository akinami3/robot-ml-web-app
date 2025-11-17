import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
})

export const robotApi = {
  async sendVelocity(payload: { vx: number; vy: number; omega: number }) {
    await api.post('/robot/control/velocity', payload)
  },
  async sendNavigation(payload: unknown) {
    await api.post('/robot/control/navigation', payload)
  },
}

export const telemetryApi = {
  async createSession(payload: unknown) {
    const response = await api.post('/telemetry/sessions', payload)
    return response.data
  },
  async listSessions() {
    const response = await api.get('/telemetry/sessions')
    return response.data
  },
  async updateSession(sessionId: string, payload: unknown) {
    const response = await api.patch(`/telemetry/sessions/${sessionId}`, payload)
    return response.data
  },
}

export const mlApi = {
  async createJob(payload: unknown) {
    const response = await api.post('/ml/jobs', payload)
    return response.data
  },
  async listJobs() {
    const response = await api.get('/ml/jobs')
    return response.data
  },
}

export const chatbotApi = {
  async query(question: string) {
    const response = await api.post('/chatbot/query', { question })
    return response.data
  },
}

export const simulationApi = {
  async start() {
    await api.post('/simulation/start')
  },
  async stop() {
    await api.post('/simulation/stop')
  },
}
