/**
 * Canonical frontend status normalization (Phase H.1).
 *
 * Single entry for StatusKind / Severity / blocking semantics.
 * No API fetches, no CSS — presentation stays in components until H.2+.
 *
 * Backend facades (read-only data sources, not imported here):
 * - dcc_status_facade
 * - system_status_facade
 * - network_info_facade
 */

export const VIEWMODEL_VERSION = 1

export type StatusKind =
  | 'ok'
  | 'warning'
  | 'degraded'
  | 'blocked'
  | 'unavailable'
  | 'unknown'

export type StatusSeverity = 'info' | 'success' | 'warning' | 'danger' | 'neutral'

export type StatusViewModel = {
  kind: StatusKind
  severity: StatusSeverity
  labelKey: string
  iconKey: string
  sortRank: number
  isBlocking: boolean
  isAvailable: boolean
}

const KIND_SORT_RANK: Record<StatusKind, number> = {
  blocked: 0,
  unavailable: 1,
  degraded: 2,
  warning: 3,
  unknown: 4,
  ok: 5,
}

const KIND_SEVERITY: Record<StatusKind, StatusSeverity> = {
  ok: 'success',
  warning: 'warning',
  degraded: 'warning',
  blocked: 'danger',
  unavailable: 'neutral',
  unknown: 'neutral',
}

const KIND_LABEL_KEY: Record<StatusKind, string> = {
  ok: 'statusViewModel.kind.ok',
  warning: 'statusViewModel.kind.warning',
  degraded: 'statusViewModel.kind.degraded',
  blocked: 'statusViewModel.kind.blocked',
  unavailable: 'statusViewModel.kind.unavailable',
  unknown: 'statusViewModel.kind.unknown',
}

const KIND_ICON_KEY: Record<StatusKind, string> = {
  ok: 'statusViewModel.icon.ok',
  warning: 'statusViewModel.icon.warning',
  degraded: 'statusViewModel.icon.degraded',
  blocked: 'statusViewModel.icon.blocked',
  unavailable: 'statusViewModel.icon.unavailable',
  unknown: 'statusViewModel.icon.unknown',
}

const INPUT_KIND_MAP: Record<string, StatusKind> = {
  ok: 'ok',
  success: 'ok',
  healthy: 'ok',
  green: 'ok',
  partial_green: 'ok',
  passed: 'ok',
  warning: 'warning',
  warn: 'warning',
  yellow: 'warning',
  amber: 'warning',
  degraded: 'degraded',
  partial: 'degraded',
  blocked: 'blocked',
  block: 'blocked',
  red: 'blocked',
  failed: 'blocked',
  error: 'blocked',
  danger: 'blocked',
  critical: 'blocked',
  unavailable: 'unavailable',
  unavailable_or_discouraged: 'unavailable',
  gray: 'unavailable',
  grey: 'unavailable',
  none: 'unavailable',
  off: 'unavailable',
  deferred: 'unavailable',
  unknown: 'unknown',
  unclear: 'unknown',
}

export function normalizeStatusKind(input: unknown): StatusKind {
  if (input == null) return 'unknown'
  const raw = String(input).trim().toLowerCase()
  if (!raw) return 'unknown'
  return INPUT_KIND_MAP[raw] ?? 'unknown'
}

function buildFromKind(kind: StatusKind): StatusViewModel {
  return {
    kind,
    severity: KIND_SEVERITY[kind],
    labelKey: KIND_LABEL_KEY[kind],
    iconKey: KIND_ICON_KEY[kind],
    sortRank: KIND_SORT_RANK[kind],
    isBlocking: kind === 'blocked',
    isAvailable: kind !== 'unavailable' && kind !== 'blocked',
  }
}

export function buildStatusViewModel(input: unknown): StatusViewModel {
  return buildFromKind(normalizeStatusKind(input))
}

/** Maps legacy traffic-light lamp strings (green/yellow/red/unknown). */
export function buildTrafficLightViewModel(input: unknown): StatusViewModel {
  return buildStatusViewModel(input)
}

/** Maps DCC/dashboard/deploy gate tones (green/yellow/red/gray/blocked/deferred/…). */
export function buildDashboardStatusViewModel(input: unknown): StatusViewModel {
  return buildStatusViewModel(input)
}

export function worstStatusViewModel(models: StatusViewModel[]): StatusViewModel {
  if (models.length === 0) return buildFromKind('unknown')
  return models.reduce((worst, current) =>
    current.sortRank < worst.sortRank ? current : worst,
  )
}

export type DashboardTone = 'green' | 'yellow' | 'red' | 'gray'

/** Legacy dashboard/deploy tone strings (green/yellow/red/gray). */
export function dashboardToneFromInput(input: unknown): DashboardTone {
  const kind = normalizeStatusKind(input)
  if (kind === 'ok') return 'green'
  if (kind === 'warning' || kind === 'degraded') return 'yellow'
  if (kind === 'blocked') return 'red'
  return 'gray'
}

const DASHBOARD_LEGACY_TONE_OVERRIDES: Record<string, DashboardTone> = {
  partial_green: 'yellow',
  pending: 'gray',
  rot: 'red',
  operator_action: 'yellow',
  forbidden: 'red',
  read_only: 'green',
}

/** DCC/control-center legacy tone tokens with stable 1:1 outputs (H.3). */
export function dashboardLegacyToneFromInput(input: unknown): DashboardTone {
  if (input === true) return 'green'
  const raw = String(input ?? '').trim().toLowerCase()
  if (!raw) return 'gray'
  const override = DASHBOARD_LEGACY_TONE_OVERRIDES[raw]
  if (override) return override
  return dashboardToneFromInput(input)
}

export type TrafficLightLampTone = 'green' | 'yellow' | 'red'

/** Legacy traffic-light lamp from normalized kind (unknown/unavailable → yellow). */
export function trafficLightLampFromKind(kind: StatusKind): TrafficLightLampTone {
  if (kind === 'ok') return 'green'
  if (kind === 'warning' || kind === 'degraded') return 'yellow'
  if (kind === 'blocked') return 'red'
  return 'yellow'
}

export function trafficLightLampFromInput(input: unknown): TrafficLightLampTone {
  return trafficLightLampFromKind(normalizeStatusKind(input))
}

/** Worst lamp across legacy inputs; empty → yellow (traffic-light convention). */
export function worstTrafficLightLampFromInputs(inputs: unknown[]): TrafficLightLampTone {
  if (inputs.length === 0) return 'yellow'
  const worst = worstStatusViewModel(inputs.map(buildTrafficLightViewModel))
  return trafficLightLampFromKind(worst.kind)
}

export function statusViewModelDiagnostics(): Record<string, unknown> {
  return {
    viewmodel_version: VIEWMODEL_VERSION,
    viewmodel_module: 'viewmodels/statusViewModel',
    status_kinds: Object.keys(KIND_SORT_RANK),
    severities: ['info', 'success', 'warning', 'danger', 'neutral'],
    public_functions: [
      'normalizeStatusKind',
      'buildStatusViewModel',
      'buildTrafficLightViewModel',
      'buildDashboardStatusViewModel',
      'worstStatusViewModel',
      'dashboardToneFromInput',
      'dashboardLegacyToneFromInput',
      'trafficLightLampFromInput',
      'worstTrafficLightLampFromInputs',
      'statusViewModelDiagnostics',
    ],
    backend_facade_sources: [
      'dcc_status_facade',
      'system_status_facade',
      'network_info_facade',
    ],
    component_migration: 'h3_partial',
    api_fetches: false,
  }
}
