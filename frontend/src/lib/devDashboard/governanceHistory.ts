import type {
  GovernanceAreaId,
  GovernanceAreaStatus,
  GovernanceHistorySnapshot,
  GovernanceHistoryStore,
  GovernanceTimelineEvent,
  GovernanceTransitionKind,
  Traffic,
} from './governanceTypes'
import type { DevDashboardDataSource } from './types'
import { governanceTrafficTransitionKind } from '../../viewmodels/statusViewModel'

const STORAGE_KEY = 'setuphelfer-cockpit-governance-history-v1'
const MAX_SNAPSHOTS = 120
const MAX_TIMELINE = 200

function newEventId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
}

export function loadGovernanceHistory(): GovernanceHistoryStore {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { version: 1, snapshots: [], timeline: [] }
    const parsed = JSON.parse(raw) as GovernanceHistoryStore
    if (parsed?.version === 1 && Array.isArray(parsed.snapshots) && Array.isArray(parsed.timeline)) {
      return parsed
    }
  } catch {
    /* ignore */
  }
  return { version: 1, snapshots: [], timeline: [] }
}

export function saveGovernanceHistory(store: GovernanceHistoryStore): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(store))
  } catch {
    /* ignore quota */
  }
}

function transitionKind(from: Traffic | undefined, to: Traffic): GovernanceTransitionKind | null {
  return governanceTrafficTransitionKind(from, to)
}

export type HistoryUpdateResult = {
  store: GovernanceHistoryStore
  changedToGreen: GovernanceAreaStatus[]
  regressed: GovernanceAreaStatus[]
  newEvents: GovernanceTimelineEvent[]
}

export function appendGovernanceSnapshot(
  store: GovernanceHistoryStore,
  params: {
    source: DevDashboardDataSource
    apiReachable: boolean
    areas: GovernanceAreaStatus[]
    runtimeGatePassed: boolean | null
    previousApiReachable?: boolean
  },
): HistoryUpdateResult {
  const at = new Date().toISOString()
  const areaMap = Object.fromEntries(params.areas.map((a) => [a.id, a.status])) as Record<
    GovernanceAreaId,
    Traffic
  >

  const prev = store.snapshots[store.snapshots.length - 1]
  const newEvents: GovernanceTimelineEvent[] = []
  const changedToGreen: GovernanceAreaStatus[] = []
  const regressed: GovernanceAreaStatus[] = []

  if (prev && prev.apiReachable !== params.apiReachable) {
    newEvents.push({
      id: newEventId(),
      at,
      kind: params.apiReachable ? 'api_online' : 'api_offline',
      severity: params.apiReachable ? 'info' : 'critical',
      message: params.apiReachable ? 'Runtime-API erreichbar' : 'Runtime-API offline',
    })
  }

  for (const area of params.areas) {
    const prevStatus = prev?.areas?.[area.id]
    const kind = transitionKind(prevStatus, area.status)
    if (!kind) continue

    const enriched = { ...area, previousStatus: prevStatus }
    if (kind === 'became_green' || kind === 'recovered') {
      enriched.changedToGreen = true
      changedToGreen.push(enriched)
    }
    if (kind === 'regressed' || kind === 'became_red') {
      enriched.regressed = true
      regressed.push(enriched)
    }

    const severity =
      kind === 'regressed' || kind === 'became_red' ? 'critical' : kind === 'became_green' ? 'info' : 'warning'
    newEvents.push({
      id: newEventId(),
      at,
      kind,
      areaId: area.id,
      severity,
      message: `${area.id}: ${prevStatus ?? '?'} → ${area.status}`,
      fromStatus: prevStatus,
      toStatus: area.status,
    })
  }

  const snapshot: GovernanceHistorySnapshot = {
    at,
    source: params.source,
    apiReachable: params.apiReachable,
    areas: areaMap,
    runtimeGatePassed: params.runtimeGatePassed,
  }

  const snapshots = [...store.snapshots, snapshot].slice(-MAX_SNAPSHOTS)
  const timeline = [...newEvents, ...store.timeline].slice(0, MAX_TIMELINE)

  return {
    store: { version: 1, snapshots, timeline },
    changedToGreen,
    regressed,
    newEvents,
  }
}

export function clearGovernanceHistory(): GovernanceHistoryStore {
  const empty = { version: 1 as const, snapshots: [], timeline: [] }
  saveGovernanceHistory(empty)
  return empty
}
