/**
 * Joystick Composable
 * 
 * Manages virtual joystick for robot control
 */
import { ref, onMounted, onUnmounted, Ref } from 'vue'
import nipplejs, { JoystickManager, JoystickOutputData } from 'nipplejs'

export interface JoystickData {
  vx: number
  vy: number
  vz: number
  angular: number
}

export interface UseJoystickOptions {
  maxSpeed?: number
  maxAngular?: number
  onMove?: (data: JoystickData) => void
  onEnd?: () => void
}

export function useJoystick(
  containerRef: Ref<HTMLElement | null>,
  options: UseJoystickOptions = {}
) {
  const maxSpeed = options.maxSpeed ?? 1.0
  const maxAngular = options.maxAngular ?? 1.0

  const joystickData = ref<JoystickData>({
    vx: 0,
    vy: 0,
    vz: 0,
    angular: 0,
  })

  let manager: JoystickManager | null = null
  let sendInterval: number | null = null

  const initJoystick = () => {
    if (!containerRef.value) {
      console.warn('Joystick container not available')
      return
    }

    try {
      manager = nipplejs.create({
        zone: containerRef.value,
        mode: 'static',
        position: { left: '50%', top: '50%' },
        color: '#3b82f6',
        size: 150,
      })

      manager.on('move', (_evt: any, data: JoystickOutputData) => {
        if (!data.vector) return

        // Convert joystick position to velocity commands
        // X axis: left/right movement (vy)
        // Y axis: forward/backward movement (vx)
        const vx = -data.vector.y * maxSpeed
        const vy = data.vector.x * maxSpeed
        const angular = data.vector.x * maxAngular

        joystickData.value = {
          vx,
          vy,
          vz: 0,
          angular,
        }

        options.onMove?.(joystickData.value)
      })

      manager.on('end', () => {
        joystickData.value = {
          vx: 0,
          vy: 0,
          vz: 0,
          angular: 0,
        }
        options.onEnd?.()
      })

      console.log('Joystick initialized')
    } catch (error) {
      console.error('Failed to initialize joystick:', error)
    }
  }

  const destroyJoystick = () => {
    if (sendInterval) {
      clearInterval(sendInterval)
      sendInterval = null
    }

    if (manager) {
      manager.destroy()
      manager = null
    }
  }

  onMounted(() => {
    // Wait for next tick to ensure container is rendered
    setTimeout(initJoystick, 100)
  })

  onUnmounted(() => {
    destroyJoystick()
  })

  return {
    joystickData,
    initJoystick,
    destroyJoystick,
  }
}
