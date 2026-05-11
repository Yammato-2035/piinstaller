/**
 * REST-Client für Remote-Companion (Pairing, Sessions, Device, Module, Actions).
 * Nutzt getApiBase() aus der Haupt-App; Session-Token in Header oder Query.
 */

import { getApiBase } from '../../../api'

const REMOTE_TIMEOUT_MS = 15000

function getBase(): string {
  const base = getApiBase()
  return base || (typeof window !== 'undefined' ? `${window.location.origin}` : '')
}

export async function fetchWithSession(
  path: string,
  sessionToken: string | null,
  init?: RequestInit
): Promise<Response> {
  const base = getBase()
  const url = path.startsWith('http') ? path : `${base.replace(/\/$/, '')}${path.startsWith('/') ? '' : '/'}${path}`
  const headers = new Headers(init?.headers)
  if (sessionToken) headers.set('Authorization', `Bearer ${sessionToken}`)
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), REMOTE_TIMEOUT_MS)
  try {
    return await fetch(url, { ...init, headers, signal: controller.signal })
  } finally {
    clearTimeout(timeoutId)
  }
}

export interface PairingCreateResponse {
  ticket_id: string
  payload: { v: number; host: string; device_id: string; pair_token: string; expires_at: string; scope: string }
  expires_at: string
}

export async function pairingCreate(): Promise<PairingCreateResponse> {
  const base = getBase()
  const res = await fetch(`${base}/api/pairing/create`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText))
  return res.json()
}

export interface PairingClaimResponse {
  success: boolean
  message: string
  ticket_id?: string
  session_token?: string
}

export async function pairingClaim(pairToken: string, deviceId?: string, deviceName?: string): Promise<PairingClaimResponse> {
  const base = getBase()
  const res = await fetch(`${base}/api/pairing/claim`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pair_token: pairToken, device_id: deviceId, device_name: deviceName }),
  })
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText))
  return res.json()
}

export interface SessionInfo {
  session_id: string
  device_id: string
  role: string
  expires_at: string
}

export async function sessionsMe(sessionToken: string): Promise<SessionInfo> {
  const res = await fetchWithSession('/api/sessions/me', sessionToken)
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText))
  return res.json()
}

export async function deviceInfo(sessionToken: string): Promise<Record<string, unknown>> {
  const res = await fetchWithSession('/api/device', sessionToken)
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText))
  return res.json()
}

export interface ModuleDescriptor {
  id: string
  name: string
  description?: string
  widgets: Array<{ id: string; type: string; label?: string; config?: Record<string, unknown> }>
  actions: Array<{ id: string; label: string; description?: string; params_schema?: Record<string, unknown> }>
}

export async function modulesList(sessionToken: string): Promise<ModuleDescriptor[]> {
  const res = await fetchWithSession('/api/modules', sessionToken)
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText))
  return res.json()
}

export async function moduleState(moduleId: string, sessionToken: string): Promise<Record<string, unknown>> {
  const res = await fetchWithSession(`/api/modules/${encodeURIComponent(moduleId)}/state`, sessionToken)
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText))
  return res.json()
}

export interface ActionResult {
  success: boolean
  message?: string
  data?: Record<string, unknown>
}

export async function performAction(
  moduleId: string,
  actionId: string,
  payload: Record<string, unknown>,
  sessionToken: string
): Promise<ActionResult> {
  const res = await fetchWithSession(
    `/api/modules/${encodeURIComponent(moduleId)}/actions/${encodeURIComponent(actionId)}`,
    sessionToken,
    { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ payload: payload || {} }) }
  )
  if (!res.ok) throw new Error(await res.text().catch(() => res.statusText))
  return res.json()
}
