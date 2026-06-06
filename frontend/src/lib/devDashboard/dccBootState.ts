import {
  decideDccVisibility,
  DCC_BUNDLE_FIX_MARKER,
  type DccGateVersionInfo,
} from './dccGate'

export type DccBootState =
  | 'dcc_active'
  | 'dcc_token_required'
  | 'profile_blocked_release'
  | 'api_unreachable'
  | 'api_error'
  | 'frontend_runtime_error'
  | 'stale_or_wrong_bundle'
  | 'unknown_dcc_boot_failure'
  | 'boot_loading'

export type DccBootProbeResult = {
  versionHttp: number
  statusHttp: number
  statusCode: string | null
  versionPayload: Record<string, unknown> | null
  versionFetchFailed: boolean
  statusFetchFailed: boolean
  versionUrl: string
  statusUrl: string
  loadedUrl: string
  apiBaseUrl: string
  buildVersion: string
  buildId: string
  frontendBuildProfile: string
}

export type DccBootClassification = {
  state: DccBootState
  shouldShowDcc: boolean
  dccExpectedVisible: boolean
  reason?: string
}

export function hasDccBundleMarkers(): { ok: boolean; marker: string } {
  return { ok: DCC_BUNDLE_FIX_MARKER === 'DCC_BOOT_DIAGNOSTICS_V1', marker: DCC_BUNDLE_FIX_MARKER }
}

export function classifyDccBootState(
  probe: DccBootProbeResult | null,
  bundleOk: boolean,
): DccBootClassification {
  if (!bundleOk) {
    return {
      state: 'stale_or_wrong_bundle',
      shouldShowDcc: false,
      dccExpectedVisible: false,
      reason: 'bundle_marker_missing',
    }
  }

  if (!probe) {
    return { state: 'boot_loading', shouldShowDcc: false, dccExpectedVisible: false, reason: 'probe_pending' }
  }

  const { versionHttp, statusHttp, statusCode, versionPayload, versionFetchFailed, statusFetchFailed } = probe

  if (versionFetchFailed && statusFetchFailed) {
    return {
      state: 'api_unreachable',
      shouldShowDcc: false,
      dccExpectedVisible: false,
      reason: 'version_and_status_unreachable',
    }
  }

  if (statusHttp === 404 && statusCode === 'PROFILE_ROUTE_BLOCKED') {
    return {
      state: 'profile_blocked_release',
      shouldShowDcc: false,
      dccExpectedVisible: false,
      reason: 'PROFILE_ROUTE_BLOCKED',
    }
  }

  if (
    statusHttp === 404 &&
    (statusCode === 'DEVELOPER_CAPABILITY_REQUIRED' ||
      statusCode === 'DEVELOPER_CAPABILITY_NOT_CONFIGURED')
  ) {
    const configured = versionPayload?.developer_capability_configured === true
    if (statusCode === 'DEVELOPER_CAPABILITY_REQUIRED' && configured) {
      return {
        state: 'dcc_token_required',
        shouldShowDcc: true,
        dccExpectedVisible: true,
        reason: statusCode,
      }
    }
    return {
      state: 'profile_blocked_release',
      shouldShowDcc: false,
      dccExpectedVisible: false,
      reason: statusCode,
    }
  }

  if (statusHttp === 200) {
    return { state: 'dcc_active', shouldShowDcc: true, dccExpectedVisible: true, reason: 'status_200' }
  }

  if (statusFetchFailed || statusHttp === 0) {
    return {
      state: 'api_unreachable',
      shouldShowDcc: false,
      dccExpectedVisible: false,
      reason: 'status_route_unreachable',
    }
  }

  const versionInfo: DccGateVersionInfo = {
    dev_control_enabled: versionPayload?.dev_control_enabled as boolean | null | undefined,
    install_profile: versionPayload?.install_profile as string | null | undefined,
    runtime_ports: versionPayload?.runtime_ports as DccGateVersionInfo['runtime_ports'],
  }

  const decision = decideDccVisibility(versionInfo, { httpStatus: statusHttp, code: statusCode })

  if (decision.kind === 'disabled') {
    return {
      state: 'profile_blocked_release',
      shouldShowDcc: false,
      dccExpectedVisible: false,
      reason: decision.disabledReason,
    }
  }

  if (statusHttp >= 400 || decision.kind === 'error') {
    return {
      state: 'api_error',
      shouldShowDcc: false,
      dccExpectedVisible: false,
      reason: statusCode ?? decision.kind === 'error' ? decision.errorReason : `http_${statusHttp}`,
    }
  }

  if (versionHttp === 0 && !versionFetchFailed) {
    return {
      state: 'api_unreachable',
      shouldShowDcc: false,
      dccExpectedVisible: false,
      reason: 'version_http_zero',
    }
  }

  return {
    state: 'unknown_dcc_boot_failure',
    shouldShowDcc: false,
    dccExpectedVisible: false,
    reason: 'unclassified_boot_state',
  }
}
