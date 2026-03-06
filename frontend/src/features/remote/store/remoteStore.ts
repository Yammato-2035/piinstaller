/**
 * Zustand-Store für Remote-Companion: Session, Device, Module, State.
 * Session-Token wird in localStorage persistiert.
 */

import { create } from 'zustand'
import type { ModuleDescriptor } from '../api/remoteClient'
import * as remoteClient from '../api/remoteClient'
import { connectWs, disconnectWs, type WsEvent } from '../api/wsClient'

const SESSION_STORAGE_KEY = 'pi-installer-remote-session'

function getStoredSession(): string | null {
  try {
    return typeof localStorage !== 'undefined' ? localStorage.getItem(SESSION_STORAGE_KEY) : null
  } catch {
    return null
  }
}

interface RemoteState {
  sessionToken: string | null
  deviceInfo: Record<string, unknown> | null
  modules: ModuleDescriptor[]
  moduleStates: Record<string, Record<string, unknown>>
  error: string | null
  setSessionToken: (token: string | null) => void
  loadSessionFromStorage: () => void
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
  sessionToken: getStoredSession(),
  deviceInfo: null,
  modules: [],
  moduleStates: {},
  error: null,

  setSessionToken: (token) => {
    try {
      if (token) localStorage.setItem(SESSION_STORAGE_KEY, token)
      else localStorage.removeItem(SESSION_STORAGE_KEY)
    } catch {
      // ignore
    }
    set({ sessionToken: token, error: null })
    if (!token) get().stopWs()
    else get().startWs()
  },

  loadSessionFromStorage: () => {
    try {
      const t = localStorage.getItem(SESSION_STORAGE_KEY)
      if (t) set({ sessionToken: t })
    } catch {
      // ignore
    }
  },

  fetchDeviceInfo: async () => {
    const token = get().sessionToken
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
    const token = get().sessionToken
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
    const token = get().sessionToken
    if (!token) return
    try {
      const state = await remoteClient.moduleState(moduleId, token)
      set((s) => ({ moduleStates: { ...s.moduleStates, [moduleId]: state } }))
    } catch (e) {
      set((s) => ({ moduleStates: { ...s.moduleStates, [moduleId]: { _error: String(e) } } }))
    }
  },

  performAction: async (moduleId, actionId, payload) => {
    const token = get().sessionToken
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
    get().setSessionToken(null)
    set({ deviceInfo: null, modules: [], moduleStates: {}, error: null })
  },

  handleWsEvent: (event) => {
    if (event.type === 'module.state.changed' && event.payload?.module_id) {
      const moduleId = event.payload.module_id as string
      const state = event.payload.state as Record<string, unknown>
      if (moduleId && state) set((s) => ({ moduleStates: { ...s.moduleStates, [moduleId]: state } }))
    }
  },

  startWs: () => {
    const token = get().sessionToken
    if (token) connectWs(token, (ev) => get().handleWsEvent(ev))
  },

  stopWs: () => {
    disconnectWs()
  },
}))
