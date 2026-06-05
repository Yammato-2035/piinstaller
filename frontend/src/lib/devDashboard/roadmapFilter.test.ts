import { describe, expect, it } from 'vitest'
import { buildCompactSummary, buildFilteredTreeRows, extractTopBlockers, filterAreas } from './roadmapFilter'

const areas = [
  {
    id: 'windows-laptop-rescue-inspect',
    status: 'yellow',
    title_de: 'Windows Inspect',
    blockers: [{ id: 'b1', title_de: 'HW pending', severity: 'high', status: 'blocked' }],
    milestones: [{ id: 'm1', status: 'planned', tasks: [{ id: 't1', status: 'planned' }] }],
  },
  {
    id: 'dev-dashboard',
    status: 'green',
    title_de: 'DCC',
    blockers: [],
    milestones: [],
  },
  {
    id: 'rescue-stick',
    status: 'blocked',
    title_de: 'Rescue',
    blockers: [{ id: 'b2', title_de: 'No boot proof', severity: 'critical', status: 'blocked' }],
    milestones: [],
  },
]

describe('roadmapFilter', () => {
  it('filters windows areas', () => {
    const filtered = filterAreas(areas, 'windows')
    expect(filtered).toHaveLength(1)
    expect(filtered[0].id).toBe('windows-laptop-rescue-inspect')
  })

  it('extracts top blockers by severity', () => {
    const blockers = extractTopBlockers(areas, 2)
    expect(blockers[0].severity).toBe('critical')
    expect(blockers).toHaveLength(2)
  })

  it('builds compact summary with windows track flag', () => {
    const summary = buildCompactSummary({
      summary: { overall_status: 'yellow' },
      recommended_prompt: { id: 'WINDOWS11_RESCUE_INSPECT_MVP', title_de: 'Windows MVP' },
      runtime_overlay: { runtime_gate_status: 'green' },
      areas,
    })
    expect(summary.windowsTrackPresent).toBe(true)
    expect(summary.recommendedPromptId).toBe('WINDOWS11_RESCUE_INSPECT_MVP')
  })

  it('builds filtered tree rows without dumping all areas for red filter', () => {
    const rows = buildFilteredTreeRows(areas, 'red')
    expect(rows.some((r) => r.kind === 'area' && r.row.id === 'rescue-stick')).toBe(true)
    expect(rows.some((r) => r.kind === 'area' && r.row.id === 'dev-dashboard')).toBe(false)
  })
})
