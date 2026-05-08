import { ref, readonly } from 'vue'
import type { WSMessage } from '../types'

export type WsStatus = 'idle' | 'connecting' | 'running' | 'done' | 'error'

const messages = ref<WSMessage[]>([])
const status = ref<WsStatus>('idle')
let ws: WebSocket | null = null

export function useWebSocket() {
  function connect(sessionId: string, params: { job_name: string; job_age: string }) {
    status.value = 'connecting'
    messages.value = []

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    ws = new WebSocket(`${protocol}//${window.location.host}/ws/optimize/${sessionId}`)

    ws.onopen = () => {
      status.value = 'running'
      ws!.send(JSON.stringify(params))
    }

    ws.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data)
      messages.value = [...messages.value, msg]

      if (msg.type === 'complete') status.value = 'done'
      if (msg.type === 'error') status.value = 'error'
    }

    ws.onerror = () => {
      status.value = 'error'
    }

    ws.onclose = () => {
      if (status.value === 'running') status.value = 'done'
    }
  }

  function disconnect() {
    ws?.close()
    ws = null
    status.value = 'idle'
  }

  return {
    messages: readonly(messages),
    status: readonly(status),
    connect,
    disconnect,
  }
}
