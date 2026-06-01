import { fetchApi } from '../api'

export type FleetSessionHost = {
  hostname?: string
  user?: string
  has_kvm?: boolean
  kvm_enabled?: boolean
}

export type FleetSessionQemu = {
  pid?: number | null
  iso_path?: string
  proxy_port?: number
  timeout_seconds?: number
  acceleration?: string
  exit_code?: number | null
}

export type FleetSessionGuest = {
  report_seen?: boolean
  guest_node_id?: string | null
  guest_smoke_status?: string | null
  dev_server_report_new?: boolean
}

export type FleetSessionSerial = {
  path?: string
  exists?: boolean
  size_bytes?: number
  last_size_change_at?: string | null
}

export type FleetSessionHeartbeat = {
  last_heartbeat_at?: string
  age_seconds?: number
  healthy?: boolean
  stalled?: boolean
  stall_reason?: string
}

export type FleetSession = {
  session_id?: string
  run_id?: string
  session_type?: string
  created_at?: string
  updated_at?: string
  started_at?: string
  finished_at?: string | null
  status?: string
  severity?: string
  label?: string
  host?: FleetSessionHost
  qemu?: FleetSessionQemu
  guest?: FleetSessionGuest
  serial?: FleetSessionSerial
  heartbeat?: FleetSessionHeartbeat
  evidence_paths?: string[]
  findings?: string[]
  errors?: string[]
}

export type FleetSessionSummary = {
  code?: string
  total?: number
  active_count?: number
  finished_count?: number
  warning_count?: number
  error_count?: number
  latest_active?: FleetSession[]
  generated_at?: string
}

export async function fetchFleetSessions(includeFinished = true): Promise<FleetSession[]> {
  try {
    const q = includeFinished ? 'true' : 'false'
    const res = await fetchApi(`/api/fleet/sessions?include_finished=${q}`)
    if (!res.ok) return []
    const body = (await res.json()) as { sessions?: FleetSession[] }
    return body.sessions ?? []
  } catch {
    return []
  }
}

export async function fetchFleetSessionSummary(): Promise<FleetSessionSummary | null> {
  try {
    const res = await fetchApi('/api/fleet/sessions/summary')
    if (!res.ok) return null
    return (await res.json()) as FleetSessionSummary
  } catch {
    return null
  }
}
