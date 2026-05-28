import { fetchApi } from '../../api'

const HEALTH_PROBE_MS = 2500
const VERSION_PROBE_MS = 3500

export type BackendStartupState =
  | 'backend_ok'
  | 'backend_down'
  | 'backend_hanging'
  | 'backend_degraded'
  | 'backend_unknown'

export type BackendStartupProbe = {
  state: BackendStartupState
  offlineReason?: string
  healthOk: boolean
  versionOk: boolean
}

async function probePath(path: string, timeoutMs: number): Promise<'ok' | 'timeout' | 'error'> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeoutMs)
  try {
    const r = await fetchApi(path, { signal: ctrl.signal })
    if (r.ok) return 'ok'
    return 'error'
  } catch (err) {
    if (err instanceof Error && err.name === 'AbortError') return 'timeout'
    return 'error'
  } finally {
    clearTimeout(timer)
  }
}

/** Kurzprobe vor schwerem Dashboard-Laden: /health und /api/version getrennt klassifizieren. */
export async function probeBackendStartup(): Promise<BackendStartupProbe> {
  const health = await probePath('/health', HEALTH_PROBE_MS)
  if (health === 'timeout') {
    return {
      state: 'backend_hanging',
      offlineReason: 'backend_hanging_timeout',
      healthOk: false,
      versionOk: false,
    }
  }
  if (health !== 'ok') {
    return {
      state: 'backend_down',
      offlineReason: 'backend_api_unreachable',
      healthOk: false,
      versionOk: false,
    }
  }
  const version = await probePath('/api/version', VERSION_PROBE_MS)
  if (version === 'timeout') {
    return {
      state: 'backend_hanging',
      offlineReason: 'backend_hanging_timeout',
      healthOk: true,
      versionOk: false,
    }
  }
  if (version !== 'ok') {
    return {
      state: 'backend_degraded',
      offlineReason: 'backend_version_unavailable',
      healthOk: true,
      versionOk: false,
    }
  }
  return { state: 'backend_ok', healthOk: true, versionOk: true }
}
