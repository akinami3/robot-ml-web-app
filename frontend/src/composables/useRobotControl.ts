/**
 * Robot Control Composable
 * 
 * Manages robot control operations and WebSocket communication
 */
import { ref, computed } from 'vue'
import { useWebSocket } from './useWebSocket'
import api from '@/services/api'

export interface RobotStatus {
  id: string
  position_x: number
  position_y: number
  orientation: number
  battery_level: number
  is_moving: boolean
  timestamp: string
}

export interface NavigationGoal {
  target_x: number
  target_y: number
  target_orientation: number
}

export function useRobotControl() {
  const robotStatus = ref<RobotStatus | null>(null)
  const cameraImage = ref<string>('')
  const isNavigating = ref(false)

  // WebSocket for real-time robot data
  const { isConnected, send } = useWebSocket(
    `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/api/v1/ws/robot`,
    {
      onMessage: (message) => {
        if (message.type === 'robot_status') {
          robotStatus.value = message.data
        } else if (message.type === 'camera_image') {
          cameraImage.value = message.data.image
        } else if (message.type === 'navigation_status') {
          isNavigating.value = message.data.status === 'active'
        }
      },
    }
  )

  // Send velocity command
  const sendVelocityCommand = async (vx: number, vy: number, vz: number, angular: number) => {
    try {
      await api.post('/api/v1/robot/control/velocity', {
        vx,
        vy,
        vz,
        angular,
      })
    } catch (error) {
      console.error('Failed to send velocity command:', error)
    }
  }

  // Send velocity via WebSocket (for real-time control)
  const sendVelocityWs = (vx: number, vy: number, vz: number, angular: number) => {
    send({
      type: 'velocity_command',
      data: { vx, vy, vz, angular },
    })
  }

  // Get robot status
  const fetchRobotStatus = async () => {
    try {
      const response = await api.get('/api/v1/robot/status')
      robotStatus.value = response.data
    } catch (error) {
      console.error('Failed to fetch robot status:', error)
    }
  }

  // Set navigation goal
  const setNavigationGoal = async (goal: NavigationGoal) => {
    try {
      await api.post('/api/v1/robot/control/navigate', goal)
      isNavigating.value = true
    } catch (error) {
      console.error('Failed to set navigation goal:', error)
      throw error
    }
  }

  // Cancel navigation
  const cancelNavigation = async () => {
    try {
      await api.delete('/api/v1/robot/control/navigate')
      isNavigating.value = false
    } catch (error) {
      console.error('Failed to cancel navigation:', error)
      throw error
    }
  }

  // Battery level color indicator
  const batteryColor = computed(() => {
    if (!robotStatus.value) return 'gray'
    const level = robotStatus.value.battery_level
    if (level > 60) return 'green'
    if (level > 30) return 'yellow'
    return 'red'
  })

  return {
    robotStatus,
    cameraImage,
    isNavigating,
    isConnected,
    sendVelocityCommand,
    sendVelocityWs,
    fetchRobotStatus,
    setNavigationGoal,
    cancelNavigation,
    batteryColor,
  }
}
