import { fetchApi, getApiBase } from '../../api'
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
import type { DevDashboardLoadResult, WorkspaceScanResult } from './types'

const API_PROBE_MS = 3500

async function fetchWithTimeout(path: string, init?: RequestInit): Promise<Response> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), API_PROBE_MS)
  try {
    return await fetchApi(path, { ...init, signal: ctrl.signal })
  } finally {
    clearTimeout(timer)
  }
}

async function tryRuntimeApi(statusQuery: string): Promise<DevDashboardLoadResult | null> {
  try {
    const [r1, r2, r3] = await Promise.all([
      fetchWithTimeout(`${API_STATUS_PATH}?${statusQuery}`),
      fetchWithTimeout('/api/dev-dashboard/modules'),
      fetchWithTimeout('/api/dev-dashboard/evidence-index'),
    ])
    if (!r1.ok) return null
    const d1 = await r1.json().catch(() => ({}))
    const d2 = await r2.json().catch(() => ({}))
    const d3 = await r3.json().catch(() => ({}))
    const dashboard = (d1?.dashboard as DashboardPayload) ?? null
    if (!dashboard) return null
    return {
      source: 'runtime_api',
      dashboard: { ...dashboard, data_source: 'runtime_api', standalone_mode: false },
      modules: Array.isArray(d2?.modules) ? (d2.modules as ModuleRow[]) : [],
      evidenceIndex: d3 && typeof d3 === 'object' ? (d3 as Record<string, unknown>) : null,
      apiReachable: true,
      capabilities: capabilitiesForSource('runtime_api'),
    }
  } catch {
    return null
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
  const runtime = await tryRuntimeApi(statusQuery)
  if (runtime) return runtime

  const offlineReason = 'backend_api_unreachable'
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
  return base || '(same-origin / nicht gesetzt)'
}
