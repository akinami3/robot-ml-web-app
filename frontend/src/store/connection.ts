import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useConnectionStore = defineStore('connection', () => {
  const mqttConnected = ref(false)
  const websocketConnected = ref(false)
  const ws = ref<WebSocket | null>(null)
  const monitoringInterval = ref<number | null>(null)

  const allConnected = computed(() => mqttConnected.value && websocketConnected.value)

  function startMonitoring() {
    // Connect to connection monitor WebSocket
    const wsUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
    ws.value = new WebSocket(`${wsUrl}/api/v1/ws/connection`)

    ws.value.onopen = () => {
      console.log('Connection monitor WebSocket connected')
      websocketConnected.value = true
      // Request status update
      ws.value?.send(JSON.stringify({ type: 'status_request' }))
    }

    ws.value.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'connection_status') {
        mqttConnected.value = data.data.mqtt
        websocketConnected.value = data.data.websocket
      }
    }

    ws.value.onerror = () => {
      websocketConnected.value = false
    }

    ws.value.onclose = () => {
      websocketConnected.value = false
      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        if (!websocketConnected.value) {
          startMonitoring()
        }
      }, 5000)
    }

    // Periodic status check
    monitoringInterval.value = window.setInterval(() => {
      if (ws.value && ws.value.readyState === WebSocket.OPEN) {
        ws.value.send(JSON.stringify({ type: 'status_request' }))
      }
    }, 10000)
  }

  function stopMonitoring() {
    if (monitoringInterval.value) {
      clearInterval(monitoringInterval.value)
      monitoringInterval.value = null
    }
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }
  }

  return {
    mqttConnected,
    websocketConnected,
    allConnected,
    startMonitoring,
    stopMonitoring
  }
})
