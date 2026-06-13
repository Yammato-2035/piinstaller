import { isRoadmapTrafficFilter, roadmapFilterBucketFromStatus } from '../../viewmodels/statusViewModel'

export type RoadmapFilterId =
  | 'all'
  | 'red'
  | 'yellow'
  | 'green'
  | 'rescue'
  | 'windows'
  | 'backup'
  | 'restore'
  | 'dcc'
  | 'runtime'

export type JsonRow = Record<string, unknown>

export function asRows(value: unknown): JsonRow[] {
  return Array.isArray(value) ? (value as JsonRow[]) : []
}

function statusBucket(status: string): RoadmapFilterId | null {
  return roadmapFilterBucketFromStatus(status)
}

function areaTags(areaId: string): Set<RoadmapFilterId> {
  const id = areaId.toLowerCase()
  const tags = new Set<RoadmapFilterId>()
  if (id.includes('rescue') || id === 'rescue-stick') tags.add('rescue')
  if (id.includes('windows')) tags.add('windows')
  if (id.includes('backup')) tags.add('backup')
  if (id.includes('restore')) tags.add('restore')
  if (id.includes('dev-dashboard') || id.includes('dcc')) tags.add('dcc')
  if (id.includes('runtime') || id.includes('governance')) tags.add('runtime')
  return tags
}

function rowMatchesFilter(row: JsonRow, kind: 'area' | 'milestone' | 'task', filter: RoadmapFilterId, areaId: string): boolean {
  if (filter === 'all') return true
  const status = String(row.status || 'unknown')
  const bucket = statusBucket(status)
  if (isRoadmapTrafficFilter(filter)) {
    return bucket === filter
  }
  if (kind === 'area') {
    return areaTags(String(row.id || areaId)).has(filter)
  }
  return areaTags(areaId).has(filter)
}

export function filterAreas(areas: JsonRow[], filter: RoadmapFilterId): JsonRow[] {
  if (filter === 'all') return areas
  return areas.filter((area) => {
    const areaId = String(area.id || '')
    if (rowMatchesFilter(area, 'area', filter, areaId)) return true
    const milestones = asRows(area.milestones)
    return milestones.some((m) => {
      if (rowMatchesFilter(m, 'milestone', filter, areaId)) return true
      return asRows(m.tasks).some((t) => rowMatchesFilter(t, 'task', filter, areaId))
    })
  })
}

export type RoadmapBlockerSummary = {
  id: string
  title: string
  areaId: string
  severity: string
  status: string
}

export function extractTopBlockers(areas: JsonRow[], limit = 5): RoadmapBlockerSummary[] {
  const out: RoadmapBlockerSummary[] = []
  for (const area of areas) {
    const areaId = String(area.id || '')
    for (const blocker of asRows(area.blockers)) {
      out.push({
        id: String(blocker.id || ''),
        title: String(blocker.title_de || blocker.title_en || blocker.id || '—'),
        areaId,
        severity: String(blocker.severity || 'medium'),
        status: String(blocker.status || 'blocked'),
      })
    }
    for (const milestone of asRows(area.milestones)) {
      for (const blocker of asRows(milestone.blockers)) {
        out.push({
          id: String(blocker.id || ''),
          title: String(blocker.title_de || blocker.title_en || blocker.id || '—'),
          areaId,
          severity: String(blocker.severity || 'medium'),
          status: String(blocker.status || 'blocked'),
        })
      }
    }
  }
  const severityRank: Record<string, number> = { critical: 0, high: 1, medium: 2, low: 3 }
  return out
    .sort((a, b) => (severityRank[a.severity] ?? 9) - (severityRank[b.severity] ?? 9))
    .slice(0, limit)
}

export type RoadmapCompactSummary = {
  overallStatus: string
  recommendedPromptTitle: string
  recommendedPromptId: string
  runtimeGateStatus: string
  topBlockers: RoadmapBlockerSummary[]
  warnings: string[]
  windowsTrackPresent: boolean
}

export function buildCompactSummary(roadmap: JsonRow): RoadmapCompactSummary {
  const summary = (roadmap.summary as JsonRow) || {}
  const recommended = (roadmap.recommended_prompt as JsonRow) || {}
  const runtimeOverlay = (roadmap.runtime_overlay as JsonRow) || {}
  const areas = asRows(roadmap.areas)
  const warnings = Array.isArray(roadmap.validation_warnings)
    ? (roadmap.validation_warnings as string[])
    : roadmap.validation_warnings
      ? [String(roadmap.validation_warnings)]
      : []

  return {
    overallStatus: String(summary.overall_status || 'unknown'),
    recommendedPromptTitle: String(recommended.title_de || recommended.title_en || recommended.id || '—'),
    recommendedPromptId: String(recommended.id || ''),
    runtimeGateStatus: String(runtimeOverlay.runtime_gate_status || 'unknown'),
    topBlockers: extractTopBlockers(areas, 5),
    warnings,
    windowsTrackPresent: areas.some((a) => String(a.id) === 'windows-laptop-rescue-inspect'),
  }
}

export function buildFilteredTreeRows(
  areas: JsonRow[],
  filter: RoadmapFilterId,
): Array<{ key: string; level: number; row: JsonRow; kind: 'area' | 'milestone' | 'task' }> {
  const filteredAreas = filterAreas(areas, filter)
  const rows: Array<{ key: string; level: number; row: JsonRow; kind: 'area' | 'milestone' | 'task' }> = []
  for (const area of filteredAreas) {
    const areaId = String(area.id || '')
    rows.push({ key: `area-${areaId}`, level: 0, row: area, kind: 'area' })
    for (const milestone of asRows(area.milestones)) {
      if (filter !== 'all' && !rowMatchesFilter(milestone, 'milestone', filter, areaId) && filter !== 'rescue' && filter !== 'windows' && filter !== 'backup' && filter !== 'restore' && filter !== 'dcc' && filter !== 'runtime') {
        const tasks = asRows(milestone.tasks).filter((t) => rowMatchesFilter(t, 'task', filter, areaId))
        if (!tasks.length) continue
      }
      rows.push({ key: `milestone-${String(milestone.id)}`, level: 1, row: milestone, kind: 'milestone' })
      for (const task of asRows(milestone.tasks)) {
        if (filter === 'all' || rowMatchesFilter(task, 'task', filter, areaId) || ['rescue', 'windows', 'backup', 'restore', 'dcc', 'runtime'].includes(filter)) {
          rows.push({ key: `task-${String(task.id)}`, level: 2, row: task, kind: 'task' })
        }
      }
    }
  }
  return rows
}
