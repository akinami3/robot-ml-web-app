import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export const useConnectionStore = defineStore('connection', () => {
  const mqtt = ref(false)
  const websocket = ref(false)

  const status = computed(() => ({
    mqtt: mqtt.value,
    websocket: websocket.value,
  }))

  function setMqtt(connected: boolean) {
    mqtt.value = connected
  }

  function setWebsocket(connected: boolean) {
    websocket.value = connected
  }

  return {
    mqtt,
    websocket,
    status,
    setMqtt,
    setWebsocket,
  }
})
