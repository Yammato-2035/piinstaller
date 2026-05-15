import type { DevDashboardDataSource } from './types'

export type Traffic = 'green' | 'yellow' | 'red' | 'gray'

export type GovernanceAreaId =
  | 'runtime'
  | 'backup'
  | 'restore'
  | 'verify'
  | 'rescue'
  | 'hardware'
  | 'packaging'
  | 'diagnostics'
  | 'evidence'
  | 'ci'
  | 'docs'
  | 'i18n'
  | 'prompt_export'
  | 'runtime_gates'
  | 'cloud_edition'
  | 'host_pilot'

export type GovernanceAreaStatus = {
  id: GovernanceAreaId
  status: Traffic
  labelKey: string
  blockers: string[]
  recommendedAction?: string
  lastCheckedAt: string
  previousStatus?: Traffic
  changedToGreen?: boolean
  regressed?: boolean
}

export type GovernanceTransitionKind =
  | 'became_green'
  | 'became_red'
  | 'became_yellow'
  | 'recovered'
  | 'regressed'
  | 'api_online'
  | 'api_offline'
  | 'blocker_added'
  | 'blocker_resolved'

export type GovernanceTimelineEvent = {
  id: string
  at: string
  kind: GovernanceTransitionKind
  areaId?: GovernanceAreaId
  severity: 'critical' | 'warning' | 'info'
  message: string
  fromStatus?: Traffic
  toStatus?: Traffic
}

export type GovernanceHistorySnapshot = {
  at: string
  source: DevDashboardDataSource
  apiReachable: boolean
  areas: Record<GovernanceAreaId, Traffic>
  runtimeGatePassed: boolean | null
}

export type GovernanceHistoryStore = {
  version: 1
  snapshots: GovernanceHistorySnapshot[]
  timeline: GovernanceTimelineEvent[]
}

export type CockpitViewMode = 'operations' | 'compact' | 'timeline'

export type CockpitAlert = {
  id: string
  severity: 'critical' | 'warning' | 'info'
  code: string
  message: string
  areaId?: GovernanceAreaId
}
