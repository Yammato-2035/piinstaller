import { fetchApi } from '../api'

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
