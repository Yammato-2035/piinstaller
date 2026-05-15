import type { DashboardPayload, ModuleRow } from '../../pages/DevDashboardBody'

export type DevDashboardDataSource = 'runtime_api' | 'standalone_workspace' | 'snapshot' | 'unavailable'

export type WorkspaceScanResult = {
  workspace_root: string
  warnings?: string[]
  version?: Record<string, unknown> | null
  frontend_package?: Record<string, unknown> | null
  git?: Record<string, unknown>
  evidence_files?: Record<string, Record<string, unknown>>
  matrix?: { path?: string; exists?: boolean; lines?: number; text?: string }
  modules?: Array<Record<string, unknown>>
}

export type DevDashboardLoadResult = {
  source: DevDashboardDataSource
  dashboard: DashboardPayload
  modules: ModuleRow[]
  evidenceIndex: Record<string, unknown> | null
  apiReachable: boolean
  offlineReason?: string
  workspaceRoot?: string
  metaPrompt?: string
  capabilities: DevDashboardCapabilities
}

export type DevDashboardCapabilities = {
  runtimeApi: boolean
  workspaceAnalysis: boolean
  structureHealth: boolean
  roadmap: boolean
  promptExport: boolean
  runtimeTests: boolean
}
