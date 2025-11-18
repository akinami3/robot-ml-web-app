/**
 * Recording Composable
 * 
 * Manages data recording sessions
 */
import { ref, computed } from 'vue'
import api from '@/services/api'

export interface RecordingSession {
  id: string
  name: string
  description?: string
  status: 'recording' | 'paused' | 'completed' | 'discarded'
  created_at: string
  completed_at?: string
  data_point_count: number
}

export function useRecording() {
  const sessions = ref<RecordingSession[]>([])
  const currentSession = ref<RecordingSession | null>(null)
  const isRecording = computed(() => currentSession.value?.status === 'recording')
  const isPaused = computed(() => currentSession.value?.status === 'paused')

  // Start new recording session
  const startRecording = async (name: string, description?: string) => {
    try {
      const response = await api.post('/api/v1/database/recording/start', {
        name,
        description,
      })
      currentSession.value = response.data
      await fetchSessions()
      return response.data
    } catch (error) {
      console.error('Failed to start recording:', error)
      throw error
    }
  }

  // Pause recording
  const pauseRecording = async () => {
    if (!currentSession.value) return

    try {
      const response = await api.post(
        `/api/v1/database/recording/${currentSession.value.id}/pause`
      )
      currentSession.value = response.data.session
      await fetchSessions()
    } catch (error) {
      console.error('Failed to pause recording:', error)
      throw error
    }
  }

  // Resume recording
  const resumeRecording = async () => {
    if (!currentSession.value) return

    try {
      const response = await api.post(
        `/api/v1/database/recording/${currentSession.value.id}/resume`
      )
      currentSession.value = response.data.session
      await fetchSessions()
    } catch (error) {
      console.error('Failed to resume recording:', error)
      throw error
    }
  }

  // Save recording
  const saveRecording = async () => {
    if (!currentSession.value) return

    try {
      await api.post(`/api/v1/database/recording/${currentSession.value.id}/save`)
      currentSession.value = null
      await fetchSessions()
    } catch (error) {
      console.error('Failed to save recording:', error)
      throw error
    }
  }

  // Discard recording
  const discardRecording = async () => {
    if (!currentSession.value) return

    try {
      await api.post(`/api/v1/database/recording/${currentSession.value.id}/discard`)
      currentSession.value = null
      await fetchSessions()
    } catch (error) {
      console.error('Failed to discard recording:', error)
      throw error
    }
  }

  // Fetch all sessions
  const fetchSessions = async () => {
    try {
      const response = await api.get('/api/v1/database/sessions')
      sessions.value = response.data
    } catch (error) {
      console.error('Failed to fetch sessions:', error)
    }
  }

  // Fetch session details
  const fetchSession = async (sessionId: string) => {
    try {
      const response = await api.get(`/api/v1/database/sessions/${sessionId}`)
      return response.data
    } catch (error) {
      console.error('Failed to fetch session:', error)
      throw error
    }
  }

  return {
    sessions,
    currentSession,
    isRecording,
    isPaused,
    startRecording,
    pauseRecording,
    resumeRecording,
    saveRecording,
    discardRecording,
    fetchSessions,
    fetchSession,
  }
}
