import { ref } from 'vue'

import { useConnectionStore } from '../../app/store'

type Listener = (message: any) => void

class WebSocketManager {
  private sockets = new Map<string, WebSocket>()
  private listeners = new Map<string, Set<Listener>>()
  readonly connected = ref(false)

  constructor(private readonly baseUrl: string) {}

  subscribe(channel: string, listener: Listener): () => void {
    if (!this.listeners.has(channel)) {
      this.listeners.set(channel, new Set())
    }
    this.listeners.get(channel)!.add(listener)
    if (!this.sockets.has(channel)) {
      this.openSocket(channel)
    }
    return () => {
      this.listeners.get(channel)?.delete(listener)
    }
  }

  private openSocket(channel: string) {
    const url = `${this.baseUrl}/${channel}`
    const socket = new WebSocket(url)
    const store = useConnectionStore()

    socket.onopen = () => {
      this.connected.value = true
      store.setWebsocket(true)
    }

    socket.onclose = () => {
      this.connected.value = false
      store.setWebsocket(false)
      this.sockets.delete(channel)
      setTimeout(() => this.openSocket(channel), 3000)
    }

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        this.listeners.get(channel)?.forEach((listener) => listener(data))
      } catch (error) {
        console.error('Invalid WebSocket payload', error)
      }
    }

    this.sockets.set(channel, socket)
  }
}

const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
const wsBase = `${wsProtocol}://${window.location.host}/ws`

export const websocketManager = new WebSocketManager(wsBase)
