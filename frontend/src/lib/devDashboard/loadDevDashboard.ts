import { fetchApi, getApiBase, getDefaultApiBase, usesViteDevProxy } from '../../api'
import type { DashboardPayload, ModuleRow } from '../../pages/DevDashboardBody'
import {
  buildMinimalUnavailableDashboard,
  buildStandaloneDashboardFromScan,
  capabilitiesForSource,
  modulesFromScan,
} from './buildStandaloneDashboard'
import { buildStandaloneMetaPrompt } from './buildStandalonePrompt'
import { API_STATUS_PATH, STANDALONE_SNAPSHOT_PATH } from './constants'
import { invokeTauriWorkspaceScan, isTauriRuntime } from './isTauri'
import { probeBackendStartup } from './probeBackendStartup'
import type { DevDashboardLoadResult, WorkspaceScanResult } from './types'

const API_PROBE_MS = 3500

type RuntimeApiAttempt = {
  result: DevDashboardLoadResult | null
  offlineReason: string
}

async function fetchWithTimeout(path: string, init?: RequestInit): Promise<Response> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), API_PROBE_MS)
  try {
    return await fetchApi(path, { ...init, signal: ctrl.signal })
  } finally {
    clearTimeout(timer)
  }
}

function mergeRoadmapIntoDashboard(
  dashboard: DashboardPayload,
  roadmapBundle: Record<string, unknown> | null,
): DashboardPayload {
  const embedded = (dashboard?.roadmap as Record<string, unknown>) || {}
  const embeddedAreas = Array.isArray(embedded.areas) ? embedded.areas.length : 0
  if (embeddedAreas > 0) {
    return {
      ...dashboard,
      roadmap_data_source: 'live_api',
    }
  }
  const fromBundle = (roadmapBundle?.roadmap as Record<string, unknown>) || roadmapBundle
  if (fromBundle && typeof fromBundle === 'object') {
    return {
      ...dashboard,
      roadmap: fromBundle,
      roadmap_data_source: 'live_api',
    }
  }
  return {
    ...dashboard,
    roadmap_data_source: embeddedAreas > 0 ? 'live_api' : 'unavailable',
  }
}

async function tryRuntimeApi(statusQuery: string): Promise<RuntimeApiAttempt> {
  try {
    const roadmapQuery = statusQuery ? `?${statusQuery}` : ''
    const r1 = await fetchWithTimeout(`${API_STATUS_PATH}?${statusQuery}`)
    if (!r1.ok) {
      return {
        result: null,
        offlineReason: `backend_http_non_200:${r1.status}`,
      }
    }
    const d1 = await r1.json().catch(() => ({}))
    const base = (d1?.dashboard as DashboardPayload) ?? null
    if (!base) {
      return {
        result: null,
        offlineReason: 'backend_status_payload_invalid',
      }
    }

    const r2 = await fetchWithTimeout('/api/dev-dashboard/modules').catch(() => null)
    const r3 = await fetchWithTimeout('/api/dev-dashboard/evidence-index').catch(() => null)
    const r4 = await fetchWithTimeout(`/api/dev-dashboard/roadmap${roadmapQuery}`).catch(() => null)
    const d2 = r2?.ok ? await r2.json().catch(() => ({})) : {}
    const d3 = r3?.ok ? await r3.json().catch(() => ({})) : {}
    const d4 = r4?.ok ? await r4.json().catch(() => null) : null
    const dashboard = mergeRoadmapIntoDashboard(base, d4 && typeof d4 === 'object' ? (d4 as Record<string, unknown>) : null)
    return {
      result: {
        source: 'runtime_api',
        dashboard: { ...dashboard, data_source: 'runtime_api', standalone_mode: false },
        modules: Array.isArray(d2?.modules) ? (d2.modules as ModuleRow[]) : [],
        evidenceIndex: d3 && typeof d3 === 'object' ? (d3 as Record<string, unknown>) : null,
        apiReachable: true,
        capabilities: capabilitiesForSource('runtime_api'),
      },
      offlineReason: 'none',
    }
  } catch (err) {
    const hanging = err instanceof Error && err.name === 'AbortError'
    return {
      result: null,
      offlineReason: hanging ? 'backend_hanging_timeout' : 'backend_api_unreachable',
    }
  }
}

async function loadSnapshot(): Promise<WorkspaceScanResult | null> {
  try {
    const r = await fetch(STANDALONE_SNAPSHOT_PATH, { cache: 'no-store' })
    if (!r.ok) return null
    const body = await r.json()
    if (body?.workspace_root) return body as WorkspaceScanResult
    if (body?.scan?.workspace_root) return body.scan as WorkspaceScanResult
  } catch {
    /* ignore */
  }
  return null
}

async function loadTauriScan(): Promise<WorkspaceScanResult | null> {
  if (!isTauriRuntime()) return null
  try {
    const raw = await invokeTauriWorkspaceScan()
    if (raw && typeof raw === 'object' && 'workspace_root' in (raw as object)) {
      return raw as WorkspaceScanResult
    }
  } catch {
    /* ignore */
  }
  return null
}

export async function loadDevDashboard(statusQuery: string): Promise<DevDashboardLoadResult> {
  const startup = await probeBackendStartup()
  if (startup.state !== 'backend_ok') {
    const offlineReason =
      startup.offlineReason ||
      (startup.state === 'backend_degraded' ? 'backend_version_unavailable' : 'backend_api_unreachable')
    let scan = await loadTauriScan()
    let source: DevDashboardLoadResult['source'] = 'standalone_workspace'
    if (!scan) {
      scan = await loadSnapshot()
      source = scan ? 'snapshot' : 'unavailable'
    }
    if (!scan) {
      const dashboard = buildMinimalUnavailableDashboard(offlineReason)
      return {
        source: 'unavailable',
        dashboard,
        modules: [],
        evidenceIndex: null,
        apiReachable: false,
        offlineReason,
        metaPrompt: buildStandaloneMetaPrompt(dashboard, '(unavailable)'),
        capabilities: capabilitiesForSource('unavailable'),
      }
    }
    const matrixText = typeof scan.matrix?.text === 'string' ? scan.matrix.text : undefined
    const dashboard = buildStandaloneDashboardFromScan(scan, source, { matrixText, offlineReason })
    return {
      source,
      dashboard,
      modules: modulesFromScan(scan),
      evidenceIndex: { status: 'standalone', gates: scan.evidence_files },
      apiReachable: false,
      offlineReason,
      workspaceRoot: scan.workspace_root,
      metaPrompt: buildStandaloneMetaPrompt(dashboard, scan.workspace_root),
      capabilities: capabilitiesForSource(source),
    }
  }

  const runtime = await tryRuntimeApi(statusQuery)
  if (runtime.result) return runtime.result

  const offlineReason = runtime.offlineReason || 'backend_api_unreachable'
  let scan = await loadTauriScan()
  let source: DevDashboardLoadResult['source'] = 'standalone_workspace'

  if (!scan) {
    scan = await loadSnapshot()
    source = scan ? 'snapshot' : 'unavailable'
  }

  if (!scan) {
    const dashboard = buildMinimalUnavailableDashboard(offlineReason)
    const metaPrompt = buildStandaloneMetaPrompt(dashboard, '(unavailable)')
    return {
      source: 'unavailable',
      dashboard,
      modules: [],
      evidenceIndex: null,
      apiReachable: false,
      offlineReason,
      metaPrompt,
      capabilities: capabilitiesForSource('unavailable'),
    }
  }

  const matrixText =
    typeof scan.matrix?.text === 'string'
      ? scan.matrix.text
      : undefined
  const dashboard = buildStandaloneDashboardFromScan(scan, source, {
    matrixText,
    offlineReason,
  })
  const modules = modulesFromScan(scan)
  const metaPrompt = buildStandaloneMetaPrompt(dashboard, scan.workspace_root)

  return {
    source,
    dashboard,
    modules,
    evidenceIndex: { status: 'standalone', gates: scan.evidence_files },
    apiReachable: false,
    offlineReason,
    workspaceRoot: scan.workspace_root,
    metaPrompt,
    capabilities: capabilitiesForSource(source),
  }
}

export function getApiBaseLabel(): string {
  const base = getApiBase()
  if (base) return base
  if (usesViteDevProxy()) return '(same-origin / Vite-Proxy)'
  return getDefaultApiBase()
}
