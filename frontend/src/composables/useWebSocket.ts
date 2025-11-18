/**
 * WebSocket Composable
 * 
 * Manages WebSocket connections for real-time data streaming
 */
import { ref, onMounted, onUnmounted, Ref } from 'vue'

export interface WebSocketMessage {
  type: string
  data: any
  timestamp?: string
}

export interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  reconnectInterval?: number
  maxReconnectAttempts?: number
}

export function useWebSocket(url: string, options: UseWebSocketOptions = {}) {
  const ws: Ref<WebSocket | null> = ref(null)
  const isConnected = ref(false)
  const reconnectAttempts = ref(0)
  const maxAttempts = options.maxReconnectAttempts ?? 5
  const reconnectInterval = options.reconnectInterval ?? 3000

  let reconnectTimeout: number | null = null

  const connect = () => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      return
    }

    try {
      // Convert http/https to ws/wss
      const wsUrl = url.startsWith('http')
        ? url.replace(/^http/, 'ws')
        : url

      ws.value = new WebSocket(wsUrl)

      ws.value.onopen = () => {
        console.log(`WebSocket connected: ${url}`)
        isConnected.value = true
        reconnectAttempts.value = 0
        options.onOpen?.()
      }

      ws.value.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data)
          options.onMessage?.(message)
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error)
        }
      }

      ws.value.onclose = () => {
        console.log(`WebSocket closed: ${url}`)
        isConnected.value = false
        options.onClose?.()

        // Attempt to reconnect
        if (reconnectAttempts.value < maxAttempts) {
          reconnectAttempts.value++
          console.log(
            `Reconnecting... (${reconnectAttempts.value}/${maxAttempts})`
          )
          reconnectTimeout = window.setTimeout(connect, reconnectInterval)
        } else {
          console.error('Max reconnection attempts reached')
        }
      }

      ws.value.onerror = (error) => {
        console.error('WebSocket error:', error)
        options.onError?.(error)
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
    }
  }

  const disconnect = () => {
    if (reconnectTimeout) {
      clearTimeout(reconnectTimeout)
      reconnectTimeout = null
    }

    if (ws.value) {
      ws.value.close()
      ws.value = null
      isConnected.value = false
    }
  }

  const send = (data: any) => {
    if (ws.value?.readyState === WebSocket.OPEN) {
      const message = typeof data === 'string' ? data : JSON.stringify(data)
      ws.value.send(message)
    } else {
      console.warn('WebSocket is not connected')
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    ws,
    isConnected,
    connect,
    disconnect,
    send,
  }
}
