import { fetchDccApi } from './dccDeveloperToken'

export type DccCompactStatus = {
  status?: string
  compact?: boolean
  install_profile?: string
  dcc_visible?: boolean
  dcc_status_allowed?: boolean
  deploy_drift_status?: string
  profile_exposure?: {
    status?: string
    forbidden_api_paths_visible?: string[]
  }
  developer_capability_exposure?: {
    status?: string
    locally_allowed_on_host?: boolean
  }
  developer_capability?: {
    configured?: boolean
    valid?: boolean
    reason?: string
  }
  telemetry?: {
    health_ok?: boolean
    ingest_enabled?: boolean
    last_error_code?: string | null
  }
  rescue?: {
    iso_uefi_validated?: boolean
    usb_written?: string
    usb_mount_detected?: boolean
    usb_mount_path?: string | null
    target_boot_validated?: boolean
  }
  blockers?: string[]
  next_operator_action?: string
  details_available?: Record<string, string>
}

export async function fetchDccCompactStatus(): Promise<{
  httpStatus: number
  body: DccCompactStatus | null
}> {
  try {
    const r = await fetchDccApi('/api/dev-dashboard/compact-status', { cache: 'no-store' })
    const body = r.ok ? ((await r.json().catch(() => null)) as DccCompactStatus | null) : null
    return { httpStatus: r.status, body }
  } catch {
    return { httpStatus: 0, body: null }
  }
}

export function deployDriftTone(status: string | undefined): string {
  const s = String(status || '').toLowerCase()
  if (s === 'green') return 'green'
  if (s === 'yellow') return 'yellow'
  if (s === 'red') return 'red'
  return 'gray'
}
