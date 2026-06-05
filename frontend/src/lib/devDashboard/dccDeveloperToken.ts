/** Local-only DCC developer token (never commit, never log). */

import { fetchApi } from '../../api'

export const DCC_DEVELOPER_TOKEN_STORAGE_KEY = 'setuphelfer-dcc-developer-token-v1'

export function readStoredDccDeveloperToken(): string | null {
  try {
    const v = typeof localStorage !== 'undefined' ? localStorage.getItem(DCC_DEVELOPER_TOKEN_STORAGE_KEY) : null
    const trimmed = String(v || '').trim()
    return trimmed || null
  } catch {
    return null
  }
}

export function writeStoredDccDeveloperToken(token: string | null): void {
  try {
    const trimmed = String(token || '').trim()
    if (trimmed) localStorage.setItem(DCC_DEVELOPER_TOKEN_STORAGE_KEY, trimmed)
    else localStorage.removeItem(DCC_DEVELOPER_TOKEN_STORAGE_KEY)
    if (typeof window !== 'undefined') {
      window.dispatchEvent(new CustomEvent('setuphelfer-dcc-developer-token-changed'))
    }
  } catch {
    /* ignore */
  }
}

export function dccDeveloperAuthHeaders(): Record<string, string> {
  const token = readStoredDccDeveloperToken()
  if (!token) return {}
  return { 'X-Setuphelfer-Developer-Token': token }
}

/** fetchApi wrapper that attaches the local DCC developer token when present. */
export async function fetchDccApi(path: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers)
  const auth = dccDeveloperAuthHeaders()
  for (const [key, value] of Object.entries(auth)) {
    if (!headers.has(key)) headers.set(key, value)
  }
  return fetchApi(path, { ...init, headers })
}
