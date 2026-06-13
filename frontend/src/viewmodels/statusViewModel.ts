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

export type GovernanceTraffic = DashboardTone

/** Governance matrix traffic — only exact green/yellow/red; else gray (H.5, 1:1 normTraffic). */
export function governanceTrafficFromInput(raw: unknown): GovernanceTraffic {
  const s = String(raw || 'gray').toLowerCase()
  if (s === 'green' || s === 'yellow' || s === 'red') return s
  return 'gray'
}

/** Worst traffic across governance module statuses (H.5). */
export function worstGovernanceTrafficFromInputs(tones: GovernanceTraffic[]): GovernanceTraffic {
  if (tones.length === 0) return 'gray'
  if (tones.some((t) => t === 'red')) return 'red'
  if (tones.some((t) => t === 'yellow')) return 'yellow'
  if (tones.every((t) => t === 'green')) return 'green'
  return 'yellow'
}

export function isGreenGovernanceTraffic(tone: GovernanceTraffic): boolean {
  return tone === 'green'
}

export function isRedGovernanceTraffic(tone: GovernanceTraffic): boolean {
  return tone === 'red'
}

export function isYellowGovernanceTraffic(tone: GovernanceTraffic): boolean {
  return tone === 'yellow'
}

/** Evidence area traffic from normalized tests status (H.5). */
export function governanceEvidenceTrafficFromTone(tone: GovernanceTraffic): 'green' | 'yellow' | 'red' {
  if (tone === 'green') return 'green'
  if (tone === 'red') return 'red'
  return 'yellow'
}

/** Docs area traffic from structure status (H.5). */
export function governanceDocsTrafficFromTone(tone: GovernanceTraffic): 'green' | 'yellow' {
  if (tone === 'green') return 'green'
  return 'yellow'
}

export type RoadmapFilterBucket = 'green' | 'yellow' | 'red'

const ROADMAP_TRAFFIC_FILTER_IDS: ReadonlySet<string> = new Set(['green', 'yellow', 'red'])

export function isRoadmapTrafficFilter(filter: string): filter is RoadmapFilterBucket {
  return ROADMAP_TRAFFIC_FILTER_IDS.has(filter)
}

/** Roadmap filter bucket — partial_green→green; planned→yellow (H.5). */
export function roadmapFilterBucketFromStatus(status: string): RoadmapFilterBucket | null {
  const s = status.trim().toLowerCase()
  if (s === 'green' || s === 'partial_green') return 'green'
  if (s === 'yellow' || s === 'planned') return 'yellow'
  if (s === 'blocked' || s === 'red') return 'red'
  return null
}

/** True when runtime/deploy gate status counts as green stable (H.4 ReadyStableSection). */
export function isDashboardGreenStatus(raw: unknown): boolean {
  return raw === true || dashboardLegacyToneFromInput(raw) === 'green'
}

/** True for normalized dashboard green tone (H.4 StatusCard). */
export function isGreenDashboardTone(tone: DashboardTone): boolean {
  return tone === 'green'
}

export type RiskWarningTitleKey =
  | 'risk.cardTitle.danger'
  | 'risk.cardTitle.systemChange'
  | 'risk.cardTitle.note'

/** i18n key for RiskWarningCard default title by risk level (H.4). */
export function riskWarningTitleKeyForLevel(level: unknown): RiskWarningTitleKey {
  const tone = dashboardToneFromInput(level)
  if (tone === 'red') return 'risk.cardTitle.danger'
  if (tone === 'yellow') return 'risk.cardTitle.systemChange'
  return 'risk.cardTitle.note'
}

export function worstTrafficLightLampFromInputs(inputs: unknown[]): TrafficLightLampTone {
  if (inputs.length === 0) return 'yellow'
  const worst = worstStatusViewModel(inputs.map(buildTrafficLightViewModel))
  return trafficLightLampFromKind(worst.kind)
}

export function isYellowTrafficLightLamp(lamp: TrafficLightLampTone): boolean {
  return lamp === 'yellow'
}

export function isGreenTrafficLightLamp(lamp: TrafficLightLampTone): boolean {
  return lamp === 'green'
}

export function isRedTrafficLightLamp(lamp: TrafficLightLampTone): boolean {
  return lamp === 'red'
}

/** LampDot glow suffix (H.6 StatusDots, 1:1). */
export function lampDotGlowSuffix(lamp: TrafficLightLampTone, quiet?: boolean): string {
  if (quiet || isGreenTrafficLightLamp(lamp)) return ''
  if (isYellowTrafficLightLamp(lamp)) return ' shadow-[0_0_4px_rgba(251,191,36,0.35)]'
  return ' shadow-[0_0_8px_rgba(239,68,68,0.55)]'
}

/** LampDot background Tailwind (H.6 StatusDots, 1:1). */
export function lampDotBackgroundClass(lamp: TrafficLightLampTone, quiet?: boolean): string {
  if (isGreenTrafficLightLamp(lamp)) {
    return `bg-emerald-400${quiet ? '' : ' shadow-[0_0_6px_rgba(52,211,153,0.45)]'}`
  }
  if (isYellowTrafficLightLamp(lamp)) return `bg-amber-400${lampDotGlowSuffix(lamp, quiet)}`
  return `bg-red-500${lampDotGlowSuffix(lamp, quiet)}`
}

/** LampAreaCard border class (H.6). */
export function lampAreaBorderClass(lamp: TrafficLightLampTone): string {
  if (isGreenTrafficLightLamp(lamp)) return 'border-emerald-500/90'
  if (isYellowTrafficLightLamp(lamp)) return 'border-amber-500/60'
  return 'border-red-500'
}

/** LampAreaCard background class (H.6). */
export function lampAreaBackgroundClass(lamp: TrafficLightLampTone): string {
  if (isGreenTrafficLightLamp(lamp)) return 'bg-emerald-950/30'
  if (isYellowTrafficLightLamp(lamp)) return 'bg-amber-950/15'
  return 'bg-red-950/35'
}

export type TrafficLightLampPosition = TrafficLightLampTone

export function isActiveTrafficLightPosition(
  active: TrafficLightLampTone,
  position: TrafficLightLampPosition,
): boolean {
  return active === position
}

/** SVG panda traffic-light lamp fill (H.6 TrafficLight.tsx, 1:1). */
export function svgTrafficLightLampBackground(
  active: TrafficLightLampTone,
  position: TrafficLightLampPosition,
  onColor: string,
  dimColor: string,
): string {
  return isActiveTrafficLightPosition(active, position) ? onColor : dimColor
}

/** SVG panda traffic-light lamp box-shadow (H.6). */
export function svgTrafficLightLampBoxShadow(
  active: TrafficLightLampTone,
  position: TrafficLightLampPosition,
): string {
  if (!isActiveTrafficLightPosition(active, position)) return 'none'
  if (position === 'green') return '0 0 10px rgba(52, 211, 153, 0.45)'
  if (position === 'yellow') return '0 0 8px rgba(251, 191, 36, 0.4)'
  return '0 0 10px rgba(239, 68, 68, 0.5)'
}

export type GovernanceTrafficTransitionKind =
  | 'recovered'
  | 'became_green'
  | 'regressed'
  | 'became_red'
  | 'became_yellow'

/** Governance history transition (H.6 governanceHistory, 1:1). */
export function governanceTrafficTransitionKind(
  from: GovernanceTraffic | undefined,
  to: GovernanceTraffic,
): GovernanceTrafficTransitionKind | null {
  if (!from || from === to) return null
  if (isGreenGovernanceTraffic(to) && !isGreenGovernanceTraffic(from)) {
    if (isRedGovernanceTraffic(from) || isYellowGovernanceTraffic(from)) return 'recovered'
    return 'became_green'
  }
  if (isRedGovernanceTraffic(to) && !isRedGovernanceTraffic(from)) {
    return isGreenGovernanceTraffic(from) ? 'regressed' : 'became_red'
  }
  if (isYellowGovernanceTraffic(to) && isGreenGovernanceTraffic(from)) return 'regressed'
  if (isYellowGovernanceTraffic(to) && isRedGovernanceTraffic(from)) return 'recovered'
  return 'became_yellow'
}

export type StandaloneMatrixCategory = 'created' | 'in_progress' | 'planned' | 'blocked'

/** Standalone dashboard ampel normalization (H.6, 1:1 normalizeAmpel). */
export function standaloneAmpelFromInput(raw: string | undefined): string {
  const s = String(raw || '').toLowerCase()
  const map: Record<string, string> = {
    grün: 'green',
    gruen: 'green',
    green: 'green',
    gelb: 'yellow',
    yellow: 'yellow',
    rot: 'red',
    red: 'red',
    gray: 'gray',
    grey: 'gray',
    blocked: 'red',
    failed: 'red',
  }
  return map[s] || 'unknown'
}

/** Matrix row category from normalized ampel (H.6). */
export function standaloneMatrixCategoryFromAmpel(ampel: string): StandaloneMatrixCategory {
  if (ampel === 'green') return 'created'
  if (ampel === 'yellow') return 'in_progress'
  if (ampel === 'red' || ampel === 'unknown') return 'blocked'
  return 'planned'
}

/** Worst tests-evidence overall ampel (H.6). */
export function worstStandaloneAmpelOverall(currentOverall: string, ampel: string): string {
  if (ampel === 'red') return 'red'
  if (ampel === 'yellow' && currentOverall === 'green') return 'yellow'
  return currentOverall
}

export type RiskLevelLabelKey = 'risk.label.safe' | 'risk.label.systemChange' | 'risk.label.danger'

/** i18n key for page risk level label (H.7 riskLevels, 1:1). */
export function riskLevelLabelKeyForLevel(level: unknown): RiskLevelLabelKey {
  const tone = dashboardToneFromInput(level)
  if (tone === 'red') return 'risk.label.danger'
  if (tone === 'yellow') return 'risk.label.systemChange'
  return 'risk.label.safe'
}

/** DCC cockpit tone border/background classes (H.7 devDashboardFilters, 1:1 toneClass). */
export function dashboardToneBorderClass(tone: DashboardTone): string {
  if (tone === 'green') return 'border-emerald-600/50 bg-emerald-950/30 text-emerald-100'
  if (tone === 'yellow') return 'border-amber-600/50 bg-amber-950/30 text-amber-100'
  if (tone === 'red') return 'border-red-600/50 bg-red-950/30 text-red-100'
  return 'border-slate-600/50 bg-slate-900/40 text-slate-200'
}

const DASHBOARD_TRAFFIC_FILTER_KEYS: ReadonlySet<string> = new Set(['red', 'yellow', 'green', 'gray'])

export function isDashboardTrafficFilterKey(
  filter: string,
): filter is 'red' | 'yellow' | 'green' | 'gray' {
  return DASHBOARD_TRAFFIC_FILTER_KEYS.has(filter)
}

/** True when every lamp is green (H.7 trafficLightModel). */
export function allTrafficLightLampsGreen(lamps: TrafficLightLampTone[]): boolean {
  return lamps.length > 0 && lamps.every((l) => isGreenTrafficLightLamp(l))
}

/** Roadmap drawer row shell classes by status token (H.7, 1:1 toneForStatus). */
export function roadmapDrawerRowToneClass(status: string): string {
  const s = status.trim().toLowerCase()
  if (s === 'green') return 'border-emerald-700/50 bg-emerald-950/20 text-emerald-100'
  if (s === 'partial_green') return 'border-teal-700/50 bg-teal-950/20 text-teal-100'
  if (s === 'yellow') return 'border-amber-700/50 bg-amber-950/20 text-amber-100'
  if (s === 'blocked' || s === 'red') return 'border-red-700/50 bg-red-950/20 text-red-100'
  if (s === 'deferred') return 'border-slate-600 bg-slate-900/50 text-slate-200'
  return 'border-slate-700 bg-slate-900/40 text-slate-200'
}

export type ToolStatusTone = 'safe' | 'review' | 'blocked' | 'info' | 'unknown'

/** Partition tool theme tone from risk level string (H.7 setuphelferToolTheme, 1:1). */
export function toolStatusToneFromRisk(risk: string | undefined): ToolStatusTone {
  const tone = dashboardToneFromInput(risk)
  if (tone === 'green') return 'safe'
  if (tone === 'red') return 'blocked'
  if (tone === 'yellow') return 'review'
  return 'unknown'
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
      'isDashboardGreenStatus',
      'isGreenDashboardTone',
      'riskWarningTitleKeyForLevel',
      'governanceTrafficFromInput',
      'worstGovernanceTrafficFromInputs',
      'isGreenGovernanceTraffic',
      'isRedGovernanceTraffic',
      'isYellowGovernanceTraffic',
      'governanceEvidenceTrafficFromTone',
      'governanceDocsTrafficFromTone',
      'roadmapFilterBucketFromStatus',
      'isRoadmapTrafficFilter',
      'isYellowTrafficLightLamp',
      'lampDotBackgroundClass',
      'lampAreaBorderClass',
      'governanceTrafficTransitionKind',
      'standaloneAmpelFromInput',
      'riskLevelLabelKeyForLevel',
      'dashboardToneBorderClass',
      'isDashboardTrafficFilterKey',
      'allTrafficLightLampsGreen',
      'roadmapDrawerRowToneClass',
      'toolStatusToneFromRisk',
      'statusViewModelDiagnostics',
    ],
    backend_facade_sources: [
      'dcc_status_facade',
      'system_status_facade',
      'network_info_facade',
    ],
    component_migration: 'h7_final',
    api_fetches: false,
  }
}
