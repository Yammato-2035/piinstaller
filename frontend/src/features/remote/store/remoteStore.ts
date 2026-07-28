/**
 * Zustand-Store für Remote-Companion: Session, Device, Module, State.
 *
 * Paket 5 (E-09): Nur noch der REFRESH-Token wird in localStorage
 * persistiert (langlebig, aber ausschließlich gegen den Refresh-Endpunkt
 * einlösbar — nicht direkt für API-Aufrufe nutzbar). Der ACCESS-Token
 * (kurzlebig, Standard 5 Min) existiert nur im Arbeitsspeicher (Zustand-
 * State) und wird NICHT persistiert. Ein XSS-Angriff, der localStorage
 * ausliest, bekommt damit nur einen Token, der ausschließlich zum
 * Erneuern taugt, nicht zur sofortigen Aktionsausführung — und jede
 * Nutzung des Refresh-Tokens rotiert ihn serverseitig (siehe
 * core/token_lifecycle.py), was Diebstahl zusätzlich erschwert/erkennbar
 * macht.
 */

import { create } from 'zustand'
import type { ModuleDescriptor } from '../api/remoteClient'
import * as remoteClient from '../api/remoteClient'
import { connectWs, disconnectWs, type WsEvent } from '../api/wsClient'

const REFRESH_STORAGE_KEY = 'pi-installer-remote-refresh'
// Access-Token wird so früh erneuert, dass ein knapper Ablauf während
// eines laufenden Requests unwahrscheinlich ist.
const REFRESH_SAFETY_MARGIN_MS = 30_000

function getStoredRefreshToken(): string | null {
  try {
    return typeof localStorage !== 'undefined' ? localStorage.getItem(REFRESH_STORAGE_KEY) : null
  } catch {
    return null
  }
}

function storeRefreshToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(REFRESH_STORAGE_KEY, token)
    else localStorage.removeItem(REFRESH_STORAGE_KEY)
  } catch {
    // ignore (z.B. privater Modus ohne Storage-Zugriff)
  }
}

interface RemoteState {
  /** Kurzlebiger Access-Token — NUR im Speicher, niemals persistiert. */
  accessToken: string | null
  accessExpiresAt: string | null
  /** Langlebiger, rotierender Refresh-Token — in localStorage persistiert. */
  refreshToken: string | null

  deviceInfo: Record<string, unknown> | null
  modules: ModuleDescriptor[]
  moduleStates: Record<string, Record<string, unknown>>
  error: string | null

  /** Wird nach erfolgreichem Pairing-Claim aufgerufen. */
  setTokenPair: (pair: {
    accessToken: string
    accessExpiresAt: string
    refreshToken: string
  }) => void
  /**
   * Stellt sicher, dass ein gültiger Access-Token vorliegt — erneuert ihn
   * proaktiv über den Refresh-Token, falls abgelaufen oder kurz davor.
   * Gibt den gültigen Access-Token zurück, oder null wenn keine Session
   * (mehr) besteht (z.B. Refresh-Token ebenfalls abgelaufen/revoked —
   * dann muss neu gepaart werden).
   */
  ensureFreshAccessToken: () => Promise<string | null>
  fetchDeviceInfo: () => Promise<void>
  fetchModules: () => Promise<void>
  fetchModuleState: (moduleId: string) => Promise<void>
  performAction: (moduleId: string, actionId: string, payload: Record<string, unknown>) => Promise<{ success: boolean; message?: string }>
  clearSession: () => void
  handleWsEvent: (event: WsEvent) => void
  startWs: () => void
  stopWs: () => void
}

export const useRemoteStore = create<RemoteState>((set, get) => ({
  accessToken: null,
  accessExpiresAt: null,
  refreshToken: getStoredRefreshToken(),
  deviceInfo: null,
  modules: [],
  moduleStates: {},
  error: null,

  setTokenPair: ({ accessToken, accessExpiresAt, refreshToken }) => {
    storeRefreshToken(refreshToken)
    set({ accessToken, accessExpiresAt, refreshToken, error: null })
    get().startWs()
  },

  ensureFreshAccessToken: async () => {
    const { accessToken, accessExpiresAt, refreshToken } = get()

    const stillValid =
      accessToken &&
      accessExpiresAt &&
      new Date(accessExpiresAt).getTime() - Date.now() > REFRESH_SAFETY_MARGIN_MS

    if (stillValid) return accessToken

    if (!refreshToken) return null // keine Session — Pairing nötig

    try {
      const res = await remoteClient.refreshSession(refreshToken)
      // WICHTIG: der neue refresh_token ERSETZT den alten. Der alte ist ab
      // sofort serverseitig ungültig (Rotation) — wird er hier nicht
      // überschrieben, schlägt der nächste Refresh-Versuch fehl.
      storeRefreshToken(res.refresh_token)
      set({
        accessToken: res.access_token,
        accessExpiresAt: res.access_expires_at,
        refreshToken: res.refresh_token,
      })
      return res.access_token
    } catch (e) {
      // Refresh-Token ungültig/abgelaufen/als gestohlen erkannt (Backend
      // revoked dann die gesamte Session) — sauberer Session-Reset.
      get().clearSession()
      set({ error: e instanceof Error ? e.message : String(e) })
      return null
    }
  },

  fetchDeviceInfo: async () => {
    const token = await get().ensureFreshAccessToken()
    if (!token) return
    set({ error: null })
    try {
      const info = await remoteClient.deviceInfo(token)
      set({ deviceInfo: info })
    } catch (e) {
      set({ error: e instanceof Error ? e.message : String(e) })
    }
  },

  fetchModules: async () => {
    const token = await get().ensureFreshAccessToken()
    if (!token) return
    set({ error: null })
    try {
      const list = await remoteClient.modulesList(token)
      set({ modules: list })
    } catch (e) {
      set({ error: e instanceof Error ? e.message : String(e) })
    }
  },

  fetchModuleState: async (moduleId) => {
    const token = await get().ensureFreshAccessToken()
    if (!token) return
    try {
      const state = await remoteClient.moduleState(moduleId, token)
      set((s) => ({ moduleStates: { ...s.moduleStates, [moduleId]: state } }))
    } catch (e) {
      set((s) => ({ moduleStates: { ...s.moduleStates, [moduleId]: { _error: String(e) } } }))
    }
  },

  performAction: async (moduleId, actionId, payload) => {
    const token = await get().ensureFreshAccessToken()
    if (!token) return { success: false, message: 'Nicht angemeldet' }
    set({ error: null })
    try {
      const result = await remoteClient.performAction(moduleId, actionId, payload, token)
      if (result.success) get().fetchModuleState(moduleId)
      return { success: result.success, message: result.message }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e)
      set({ error: msg })
      return { success: false, message: msg }
    }
  },

  clearSession: () => {
    get().stopWs()
    storeRefreshToken(null)
    set({
      accessToken: null,
      accessExpiresAt: null,
      refreshToken: null,
      deviceInfo: null,
      modules: [],
      moduleStates: {},
      error: null,
    })
  },

  handleWsEvent: (event) => {
    if (event.type === 'module.state.changed' && event.payload?.module_id) {
      const moduleId = event.payload.module_id as string
      const state = event.payload.state as Record<string, unknown>
      if (moduleId && state) set((s) => ({ moduleStates: { ...s.moduleStates, [moduleId]: state } }))
    }
  },

  startWs: () => {
    const { accessToken } = get()
    if (accessToken) connectWs(accessToken, (ev) => get().handleWsEvent(ev))
  },

  stopWs: () => {
    disconnectWs()
  },
}))
