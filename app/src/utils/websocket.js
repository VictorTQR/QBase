const DEFAULT_WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'

export class WebSocketClient {
  constructor() {
    this.ws = null
    this.listeners = new Map()
    this.taskType = null
  }

  connect(taskType) {
    this.taskType = taskType
    const url = `${DEFAULT_WS_URL}/ws/tasks/${taskType}`

    this.ws = new WebSocket(url)
    this.ws.onopen = () => this.emit('connected')
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      this.emit('message', data)
    }
    this.ws.onerror = (error) => this.emit('error', error)
    this.ws.onclose = () => this.emit('disconnected')
  }

  on(event, callback) {
    if (!this.listeners.has(event)) this.listeners.set(event, [])
    this.listeners.get(event).push(callback)
  }

  off(event, callback) {
    if (!this.listeners.has(event)) return
    const callbacks = this.listeners.get(event)
    const index = callbacks.indexOf(callback)
    if (index > -1) {
      callbacks.splice(index, 1)
    }
  }

  emit(event, data) {
    if (!this.listeners.has(event)) return
    this.listeners.get(event).forEach((cb) => cb(data))
  }

  disconnect() {
    if (this.ws) this.ws.close()
    this.listeners.clear()
  }
}

export const mineruWebSocket = new WebSocketClient()
export const audioWebSocket = new WebSocketClient()
