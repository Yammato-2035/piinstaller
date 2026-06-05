/** Runtime marker — must appear in production bundle for deploy verification. */
export const DCC_BUNDLE_FIX_MARKER = 'DCC_BOOT_DIAGNOSTICS_V1' as const

export type DccGateVersionInfo = {
  dev_control_enabled?: boolean | null
  install_profile?: string | null
  runtime_ports?: {
    backend_api?: { host?: string | null; port?: number | null }
    frontend_ui?: { host?: string | null; port?: number | null }
    nginx_default?: { host?: string | null; port?: number | null }
    qemu_lab_proxy_host?: { host?: string | null; port?: number | null }
    qemu_guest_devserver?: { host?: string | null; port?: number | null }
  } | null
}

export type DccGateStatusInfo = {
  httpStatus: number
  // For blocked cases the backend returns e.g. { status: "error", code: "PROFILE_ROUTE_BLOCKED" }
  code?: string | null
}

export type DccGateDecision =
  | { kind: 'allowed' }
  | { kind: 'disabled'; disabledReason: 'profile_route_blocked' | 'dev_control_disabled_and_status_blocked' }
  | { kind: 'error'; errorReason: 'inconsistent_or_unknown' }

/**
 * Source-of-truth: `/api/dev-dashboard/status`
 *
 * Rules:
 * - If status HTTP 200 -> DCC must be shown (even if `/api/version` is stale / says release).
 * - If status HTTP 404 with code PROFILE_ROUTE_BLOCKED -> show disabled page.
 * - If `/api/version` says dev_control_enabled=false and status is not 200 -> show disabled page.
 * - Otherwise -> error state (avoid false "release disabled" page).
 */
export function decideDccVisibility(version: DccGateVersionInfo, status: DccGateStatusInfo | null): DccGateDecision {
  if (!status || !Number.isInteger(status.httpStatus)) {
    return { kind: 'error', errorReason: 'inconsistent_or_unknown' }
  }

  if (status.httpStatus === 200) return { kind: 'allowed' }

  if (status.httpStatus === 404 && status.code === 'PROFILE_ROUTE_BLOCKED') {
    return { kind: 'disabled', disabledReason: 'profile_route_blocked' }
  }

  if (version.dev_control_enabled === false) {
    // status is blocked (non-200), and dev_control explicitly disabled -> safe to show disabled page.
    return { kind: 'disabled', disabledReason: 'dev_control_disabled_and_status_blocked' }
  }

  return { kind: 'error', errorReason: 'inconsistent_or_unknown' }
}

export type DccDisplayPorts = {
  api: string
  ui: string
  nginx: string
  qemu_host_proxy?: string
  qemu_guest_devserver?: string
}

function hostPort(host?: string | null, port?: number | null): string {
  const h = typeof host === 'string' && host.trim() ? host.trim() : 'unknown'
  const p = typeof port === 'number' && Number.isInteger(port) ? port : 'unknown'
  return `${h}:${p}`
}

export function extractDccPortsFromVersion(version: DccGateVersionInfo | null | undefined): DccDisplayPorts {
  const v = version ?? {}
  return {
    api: hostPort(v.runtime_ports?.backend_api?.host, v.runtime_ports?.backend_api?.port),
    ui: hostPort(v.runtime_ports?.frontend_ui?.host, v.runtime_ports?.frontend_ui?.port),
    nginx: hostPort(v.runtime_ports?.nginx_default?.host, v.runtime_ports?.nginx_default?.port),
    qemu_host_proxy: v.runtime_ports?.qemu_lab_proxy_host
      ? hostPort(v.runtime_ports.qemu_lab_proxy_host.host, v.runtime_ports.qemu_lab_proxy_host.port)
      : undefined,
    qemu_guest_devserver: v.runtime_ports?.qemu_guest_devserver
      ? hostPort(v.runtime_ports.qemu_guest_devserver.host, v.runtime_ports.qemu_guest_devserver.port)
      : undefined,
  }
}

export function buildFullApiUrl(apiBase: string, path: string): string {
  const base = apiBase?.trim() ? apiBase.trim().replace(/\/+$/, '') : ''
  if (!base) return path
  const p = path.startsWith('/') ? path : `/${path}`
  return `${base}${p}`
}

