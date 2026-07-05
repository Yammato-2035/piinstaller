import { DCC_VISIBILITY_CHANGELOG, type ChangelogItem } from './changelogModel'
import { DEFAULT_WORKSPACE_HANDOFF, type WorkspaceHandoff } from './workspaceHandoff'

export type RoadmapVisibilityStatus = {
  current_workspace: string
  current_phase: string
  current_branch?: string
  current_commit?: string
  last_completed_phase: string
  last_visible_result: string
  next_recommended_phase: string
  next_required_workspace: string
  blockers: string[]
  visible_surfaces: Record<string, boolean>
  evidence_links: string[]
  changelog_items: ChangelogItem[]
  supported_languages: string[]
  docs_status: 'stub' | 'complete'
  faq_status: 'stub' | 'complete'
  kb_status: 'stub' | 'complete'
  workspace_handoff: WorkspaceHandoff
}

export function buildRoadmapVisibilityStatus(params?: {
  branch?: string
  commit?: string
  blockers?: string[]
}): RoadmapVisibilityStatus {
  const completed = DCC_VISIBILITY_CHANGELOG.filter((c) => c.status === 'completed')
  const lastCompleted = completed[completed.length - 1]
  const inProgress = DCC_VISIBILITY_CHANGELOG.find((c) => c.status === 'in_progress')
  const nextPlanned = DCC_VISIBILITY_CHANGELOG.find((c) => c.status === 'planned')

  return {
    current_workspace: DEFAULT_WORKSPACE_HANDOFF.currentWorkspace,
    current_phase: inProgress?.id ?? 'DCC-VIS-001',
    current_branch: params?.branch,
    current_commit: params?.commit,
    last_completed_phase: lastCompleted ? `${lastCompleted.id}` : '—',
    last_visible_result: lastCompleted?.resultKey ?? '—',
    next_recommended_phase: inProgress?.id ?? nextPlanned?.id ?? '—',
    next_required_workspace: DEFAULT_WORKSPACE_HANDOFF.nextWorkspace,
    blockers: params?.blockers ?? [],
    visible_surfaces: {
      dcc: true,
      telemetry_dashboard: true,
      plesk: false,
      website: false,
    },
    evidence_links: DCC_VISIBILITY_CHANGELOG.map((c) => c.evidencePath).filter(Boolean) as string[],
    changelog_items: DCC_VISIBILITY_CHANGELOG,
    supported_languages: ['de', 'en', 'fr', 'nl'],
    docs_status: 'stub',
    faq_status: 'stub',
    kb_status: 'stub',
    workspace_handoff: DEFAULT_WORKSPACE_HANDOFF,
  }
}
