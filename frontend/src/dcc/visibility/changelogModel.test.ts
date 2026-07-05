import { describe, expect, it } from 'vitest'
import { changelogByStatus, changelogItemById, DCC_VISIBILITY_CHANGELOG } from './changelogModel'
import { buildRoadmapVisibilityStatus } from './roadmapStatus'
import { DEFAULT_WORKSPACE_HANDOFF } from './workspaceHandoff'

describe('changelogModel', () => {
  it('contains TEL-011 completed and DCC-VIS-001 in progress', () => {
    expect(changelogItemById('TEL-011')?.status).toBe('completed')
    expect(changelogItemById('DCC-VIS-001')?.status).toBe('in_progress')
    expect(changelogItemById('TEL-012')?.status).toBe('planned')
  })

  it('exposes visible surfaces per phase', () => {
    const tel011 = changelogItemById('TEL-011')
    expect(tel011?.visibleSurfaces.telemetry_dashboard).toBe(true)
    expect(tel011?.visibleSurfaces.dcc).toBe(false)
  })

  it('changelog cards status filters work', () => {
    expect(changelogByStatus('completed').map((c) => c.id)).toContain('TEL-011')
    expect(changelogByStatus('in_progress')[0]?.id).toBe('DCC-VIS-001')
    expect(changelogByStatus('planned')[0]?.id).toBe('TEL-012')
  })
})

describe('roadmapStatus', () => {
  it('includes current and next workspace', () => {
    const status = buildRoadmapVisibilityStatus({ branch: 'dcc-vis-001-visible-roadmap-changelog' })
    expect(status.current_workspace).toBe(DEFAULT_WORKSPACE_HANDOFF.currentWorkspace)
    expect(status.next_required_workspace).toBe(DEFAULT_WORKSPACE_HANDOFF.nextWorkspace)
    expect(status.changelog_items.length).toBe(DCC_VISIBILITY_CHANGELOG.length)
    expect(status.supported_languages).toEqual(['de', 'en', 'fr', 'nl'])
  })
})
