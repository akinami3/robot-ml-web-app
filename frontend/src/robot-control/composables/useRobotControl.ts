import { onMounted, onUnmounted, ref } from 'vue'

import { useConnectionStore } from '../../app/store'
import { robotApi } from '../../shared/services/apiClient'
import { websocketManager } from '../../shared/services/wsClient'

interface RobotState {
  battery?: number
  pose?: Record<string, unknown>
  velocity?: Record<string, number>
}

interface RobotChannelMessage {
  type: string
  payload: any
}

export function useRobotControl() {
  const connectionStore = useConnectionStore()
  const robotState = ref<RobotState>({})
  const cameraStreamUrl = ref<string>('')
  let unsubscribe: (() => void) | null = null

  onMounted(() => {
  unsubscribe = websocketManager.subscribe('robot', (message: RobotChannelMessage) => {
      if (message.type === 'state') {
        robotState.value = message.payload
      } else if (message.type === 'camera') {
        cameraStreamUrl.value = message.payload.url
      }
    })
    connectionStore.setWebsocket(websocketManager.connected.value)
  })

  onUnmounted(() => {
    unsubscribe?.()
    connectionStore.setWebsocket(false)
  })

  const sendVelocityCommand = async ({ vx, vy, omega }: { vx: number; vy: number; omega: number }) => {
    await robotApi.sendVelocity({ vx, vy, omega })
  }

  return {
    robotState,
    cameraStreamUrl,
    sendVelocityCommand,
  }
}
