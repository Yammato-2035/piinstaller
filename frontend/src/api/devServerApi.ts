import { fetchApi } from '../api'

export type DevServerHealth = {
  enabled?: boolean
  mode?: string
  storage_ok?: boolean
  ssh_allowed?: boolean
  public_uploads_allowed?: boolean
  version?: string
  warnings?: string[]
  errors?: string[]
}

export type DevServerNode = {
  node_id?: string
  display_name?: string
  node_kind?: string
  lab_mode?: string
  last_seen_at?: string
  status?: string
  current_action?: string | null
  tags?: string[]
  notes?: string
  last_report_type?: string | null
  last_report_at?: string | null
  ssh?: {
    enabled?: boolean
    host?: string
    port?: number
    username?: string
    last_check_status?: string
    last_check_error?: string
  }
}

export type DevServerSummary = {
  enabled?: boolean
  node_count?: number
  online_count?: number
  busy_count?: number
  error_count?: number
  reports_last_24h?: number
  latest_findings?: Array<Record<string, unknown>>
  open_actions?: number
  blocked_actions?: number
  prompt_candidates_count?: number
}

export type DevServerSshActionResponse = {
  code?: string
  action?: Record<string, unknown> | null
  report_id?: string | null
  warnings?: string[]
  errors?: string[]
}

export async function fetchDevServerHealth(): Promise<DevServerHealth | null> {
  try {
    const res = await fetchApi('/api/dev-server/health')
    if (!res.ok) return null
    return (await res.json()) as DevServerHealth
  } catch {
    return null
  }
}

export async function fetchDevServerNodes(): Promise<DevServerNode[]> {
  try {
    const res = await fetchApi('/api/dev-server/nodes')
    if (!res.ok) return []
    const body = (await res.json()) as { nodes?: DevServerNode[] }
    return body.nodes ?? []
  } catch {
    return []
  }
}

export async function fetchDevServerSummary(): Promise<DevServerSummary | null> {
  try {
    const res = await fetchApi('/api/dev-server/summary')
    if (!res.ok) return null
    return (await res.json()) as DevServerSummary
  } catch {
    return null
  }
}

export async function fetchDevServerReports(limit = 50): Promise<Record<string, unknown>[]> {
  try {
    const res = await fetchApi(`/api/dev-server/reports?limit=${limit}`)
    if (!res.ok) return []
    const body = (await res.json()) as { reports?: Record<string, unknown>[] }
    return body.reports ?? []
  } catch {
    return []
  }
}

export async function fetchDevServerActions(limit = 50): Promise<Record<string, unknown>[]> {
  try {
    const res = await fetchApi(`/api/dev-server/actions?limit=${limit}`)
    if (!res.ok) return []
    const body = (await res.json()) as { actions?: Record<string, unknown>[] }
    return body.actions ?? []
  } catch {
    return []
  }
}

async function runDevServerSshProfile(nodeId: string, path: string): Promise<DevServerSshActionResponse | null> {
  try {
    const res = await fetchApi(`/api/dev-server/nodes/${encodeURIComponent(nodeId)}/ssh/${path}`, {
      method: 'POST',
    })
    const body = (await res.json()) as DevServerSshActionResponse
    return body
  } catch {
    return null
  }
}

export function runDevServerSshCheck(nodeId: string) {
  return runDevServerSshProfile(nodeId, 'check')
}

export function runDevServerCollectInventory(nodeId: string) {
  return runDevServerSshProfile(nodeId, 'collect-inventory')
}

export function runDevServerCollectStorage(nodeId: string) {
  return runDevServerSshProfile(nodeId, 'collect-storage')
}

export function runDevServerCollectBoot(nodeId: string) {
  return runDevServerSshProfile(nodeId, 'collect-boot')
}
