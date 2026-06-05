import { fetchApi } from '../../api'
import { extractDccPortsFromVersion, type DccGateVersionInfo } from './dccGate'
import { fetchDccApi } from './dccDeveloperToken'

export type DccCapabilityStatus = {
  dcc_visible?: boolean
  reason?: string
  install_profile?: string
  dev_control_enabled?: boolean
  developer_capability_configured?: boolean
  developer_capability_valid?: boolean
  token_source_present?: boolean
  machine_binding_checked?: boolean
  dcc_developer_enabled?: boolean
  backend_runtime_path?: string
}

export type RescueTelemetryHealth = {
  status?: string
  ingest_enabled?: boolean
  enabled?: boolean
  profile_gate_independent?: boolean
  queue_available?: boolean
  queue_depth?: number
  last_ingest_at?: string | null
  last_ack_id?: string | null
  last_error_code?: string | null
  secrets_exposed?: boolean
}

export type DccLiveStatusSnapshot = {
  capability: DccCapabilityStatus | null
  capabilityHttp: number
  telemetry: RescueTelemetryHealth | null
  telemetryHttp: number
  telemetryOffline: boolean
}

export function formatTelemetryHealthLabel(http: number, body: RescueTelemetryHealth | null): string {
  if (http === 0) return 'offline'
  if (http === 404) return '404'
  if (http === 503) return '503'
  if (http === 200) {
    if (body?.ingest_enabled === true || body?.enabled === true) return '200'
    return '200'
  }
  return String(http)
}

export function formatIngestLabel(body: RescueTelemetryHealth | null): string {
  if (!body) return 'unknown'
  const enabled = body.ingest_enabled ?? body.enabled
  return enabled ? 'enabled' : 'disabled'
}

export function formatAckLabel(body: RescueTelemetryHealth | null): string {
  if (!body?.last_ack_id) return 'fehlt'
  return 'vorhanden'
}

export async function fetchDccLiveStatus(
  versionPayload: DccGateVersionInfo | null | undefined,
): Promise<DccLiveStatusSnapshot> {
  let capability: DccCapabilityStatus | null = null
  let capabilityHttp = 0
  try {
    const r = await fetchDccApi('/api/dev-dashboard/capability-status', { cache: 'no-store' })
    capabilityHttp = r.status
    if (r.ok) capability = (await r.json().catch(() => null)) as DccCapabilityStatus | null
  } catch {
    capabilityHttp = 0
  }

  let telemetry: RescueTelemetryHealth | null = null
  let telemetryHttp = 0
  try {
    const r = await fetchApi('/api/rescue/telemetry/health', { cache: 'no-store' })
    telemetryHttp = r.status
    if (r.ok) telemetry = (await r.json().catch(() => null)) as RescueTelemetryHealth | null
  } catch {
    telemetryHttp = 0
  }

  void versionPayload
  return {
    capability,
    capabilityHttp,
    telemetry,
    telemetryHttp,
    telemetryOffline: telemetryHttp === 0,
  }
}

export function buildPortLabels(versionPayload: DccGateVersionInfo | null | undefined): {
  api: string
  ui: string
} {
  const ports = extractDccPortsFromVersion(versionPayload ?? null)
  return { api: ports.api, ui: ports.ui }
}

export function capabilitySummaryLabel(cap: DccCapabilityStatus | null): string {
  if (!cap) return 'unbekannt'
  if (cap.developer_capability_valid) return 'gültig'
  if (cap.developer_capability_configured || cap.token_source_present) return 'ungültig/fehlt'
  return 'fehlt'
}

export function dccVisibilityLabel(cap: DccCapabilityStatus | null, statusHttp: number): string {
  if (statusHttp === 200) return 'sichtbar'
  if (cap?.dcc_visible) return 'sichtbar'
  return 'blockiert'
}
