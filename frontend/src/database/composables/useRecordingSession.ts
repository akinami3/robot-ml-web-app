import { ref } from 'vue'

import { telemetryApi } from '../../shared/services/apiClient'

interface TelemetrySession {
  id: string
  name: string
  status: string
  capture_velocity: boolean
  capture_state: boolean
  capture_images: boolean
}

export function useRecordingSession() {
  const sessions = ref<TelemetrySession[]>([])
  const activeSessionId = ref<string | null>(null)

  const refreshSessions = async () => {
    sessions.value = await telemetryApi.listSessions()
  }

  const startSession = async (payload: Record<string, any>) => {
    const session = await telemetryApi.createSession(payload)
    activeSessionId.value = session.id
    await refreshSessions()
  }

  const updateActiveStatus = async (status: string) => {
    if (!activeSessionId.value) return
    await telemetryApi.updateSession(activeSessionId.value, { status })
  if (status === 'completed' || status === 'discarded') {
      activeSessionId.value = null
    }
    await refreshSessions()
  }

  const pauseSession = () => updateActiveStatus('paused')
  const saveSession = () => updateActiveStatus('completed')
  const discardSession = () => updateActiveStatus('discarded')
  const endSession = (save: boolean) => updateActiveStatus(save ? 'completed' : 'discarded')

  return {
    sessions,
    activeSessionId,
    refreshSessions,
    startSession,
    pauseSession,
    saveSession,
    discardSession,
    endSession,
  }
}
