/**
 * WebSocket-Client für Remote-Companion (Live-Events).
 * Verbindung mit ?session=TOKEN; bei Nachrichten onMessage(type, payload) aufrufen.
 */

import { getApiBase } from '../../../api'

export interface WsEvent {
  type: string
  topic: string
  payload?: Record<string, unknown>
  ts?: string
}

export type WsMessageHandler = (event: WsEvent) => void

let ws: WebSocket | null = null
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let currentToken: string | null = null
let currentHandler: WsMessageHandler | null = null
const RECONNECT_DELAY_MS = 3000

function getWsUrl(sessionToken: string): string {
  const base = getApiBase()
  const origin = base || (typeof window !== 'undefined' ? window.location.protocol + '//' + window.location.host : 'http://localhost:8000')
  const wsProtocol = origin.startsWith('https') ? 'wss' : 'ws'
  const host = origin.replace(/^https?:\/\//, '')
  return wsProtocol + '://' + host + '/api/ws?session=' + encodeURIComponent(sessionToken)
}

export function connectWs(sessionToken: string, onMessage: WsMessageHandler): void {
  if (ws != null && ws.readyState === WebSocket.OPEN && currentToken === sessionToken) return
  disconnectWs()
  currentToken = sessionToken
  currentHandler = onMessage
  const url = getWsUrl(sessionToken)
  try {
    ws = new WebSocket(url)
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data) as WsEvent
        if (currentHandler) currentHandler(data)
      } catch {
        // ignore
      }
    }
    ws.onclose = () => {
      ws = null
      if (currentToken && currentHandler) {
        reconnectTimer = setTimeout(() => {
          connectWs(currentToken!, currentHandler!)
        }, RECONNECT_DELAY_MS)
      }
    }
    ws.onerror = () => {}
  } catch {
    if (reconnectTimer) clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(() => connectWs(sessionToken, onMessage), RECONNECT_DELAY_MS)
  }
}

export function disconnectWs(): void {
  if (reconnectTimer) {
    clearTimeout(reconnectTimer)
    reconnectTimer = null
  }
  currentToken = null
  currentHandler = null
  if (ws) {
    ws.close()
    ws = null
  }
}
