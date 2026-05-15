import type { TFunction } from 'i18next'

export type DashboardPayload = Record<string, unknown> | null

export type CockpitPanelProps = {
  dashboard: DashboardPayload
  t: TFunction
}

export type RoadmapTabKey = 'created' | 'in_progress' | 'planned' | 'blocked'
