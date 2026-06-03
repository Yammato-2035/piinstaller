import { fetchApi } from '../api'

export type BackendHealthSnapshot = {
  task?: string
  generated_at?: string
  overall_status?: string
  failure_classification?: string
  recommended_operator_action?: string
  backend_service_active?: boolean
  backend_port_8000_listening?: boolean
  frontend_port_3001_listening?: boolean
  api_version_http?: number
  install_profile?: string
  profile_gate_status?: string
  dev_control_enabled?: boolean
  dev_dashboard_status_http?: number
  fleet_sessions_http?: number
  recent_evidence_http?: number
  web_ui_http?: number
  expected_profile_blocks?: boolean
}

export type BackendHealthResponse = {
  status: string
  stale: boolean
  stale_after_seconds?: number
  generated_at?: string | null
  age_seconds?: number | null
  source_path?: string | null
  current_health: BackendHealthSnapshot | null
  history_tail: BackendHealthSnapshot[]
  message?: string
}

export async function fetchBackendHealth(historyLimit = 5): Promise<BackendHealthResponse | null> {
  try {
    const res = await fetchApi(
      `/api/dev-dashboard/backend-health?history_limit=${Math.min(20, Math.max(0, historyLimit))}`,
    )
    if (!res.ok) return null
    return (await res.json()) as BackendHealthResponse
  } catch {
    return null
  }
}

export type ControlCenterSummary = {
  generated_at?: string
  runtime?: Record<string, unknown>
  roadmap?: Record<string, unknown>
  dev_server?: Record<string, unknown>
  rescue_developer?: Record<string, unknown>
  documentation?: Record<string, unknown>
  diagnostics?: Record<string, unknown>
  evidence?: Record<string, unknown>
  next_prompts?: Array<Record<string, unknown>>
  warnings?: string[]
  errors?: string[]
}

export async function fetchControlCenterSummary(): Promise<ControlCenterSummary | null> {
  try {
    const res = await fetchApi('/api/dev-dashboard/control-center-summary')
    if (!res.ok) return null
    const data = await res.json()
    return (data?.summary as ControlCenterSummary) ?? null
  } catch {
    return null
  }
}
