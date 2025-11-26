import { create } from 'zustand'
import { config } from '../config'

interface ConnectionState {
  mqttConnected: boolean
  websocketConnected: boolean
  ws: WebSocket | null
  startMonitoring: () => void
  stopMonitoring: () => void
  setMqttConnected: (connected: boolean) => void
  setWebsocketConnected: (connected: boolean) => void
}

export const useConnectionStore = create<ConnectionState>((set, get) => ({
  mqttConnected: false,
  websocketConnected: false,
  ws: null,

  setMqttConnected: (connected: boolean) => set({ mqttConnected: connected }),
  setWebsocketConnected: (connected: boolean) => set({ websocketConnected: connected }),

  startMonitoring: () => {
    const wsUrl = `${config.wsUrl}/api/v1/ws/connection`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log('Connection monitor WebSocket connected')
      set({ websocketConnected: true })
      ws.send(JSON.stringify({ type: 'status_request' }))
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'connection_status') {
        set({
          mqttConnected: data.data.mqtt || false,
          websocketConnected: data.data.websocket || false,
        })
      }
    }

    ws.onerror = () => {
      set({ websocketConnected: false })
    }

    ws.onclose = () => {
      set({ websocketConnected: false })
      setTimeout(() => {
        if (!get().websocketConnected) {
          get().startMonitoring()
        }
      }, 5000)
    }

    set({ ws })

    // Periodic status check
    const interval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: 'status_request' }))
      }
    }, 10000)

    // Store interval for cleanup
    ;(ws as any)._interval = interval
  },

  stopMonitoring: () => {
    const { ws } = get()
    if (ws) {
      if ((ws as any)._interval) {
        clearInterval((ws as any)._interval)
      }
      ws.close()
      set({ ws: null })
    }
  },
}))
