export type PhaseStatus = 'planned' | 'in_progress' | 'completed' | 'blocked'

export type VisibleSurface = 'dcc' | 'telemetry_dashboard' | 'plesk' | 'website' | 'none'

export type ChangelogItem = {
  id: string
  titleKey: string
  status: PhaseStatus
  resultKey: string
  workspace: string
  visibleSurfaces: Partial<Record<VisibleSurface, boolean>>
  evidencePath?: string
  nextStepKey?: string
}

export const DCC_VISIBILITY_CHANGELOG: ChangelogItem[] = [
  {
    id: 'SP-CSE-014',
    titleKey: 'devDashboard.vis.changelog.spCse014.title',
    status: 'completed',
    resultKey: 'devDashboard.vis.changelog.spCse014.result',
    workspace: 'setuphelfer-cloudserver-edition',
    visibleSurfaces: { dcc: false, telemetry_dashboard: false },
    evidencePath: 'docs/evidence/cloud-edition/',
  },
  {
    id: 'TEL-011',
    titleKey: 'devDashboard.vis.changelog.tel011.title',
    status: 'completed',
    resultKey: 'devDashboard.vis.changelog.tel011.result',
    workspace: 'setuphelfer-telemetry-server',
    visibleSurfaces: { telemetry_dashboard: true, dcc: false },
    evidencePath: 'docs/evidence/telemetry/TEL_011_LAB_CLIENT_REGISTRATION.md',
  },
  {
    id: 'DCC-VIS-001',
    titleKey: 'devDashboard.vis.changelog.dccVis001.title',
    status: 'in_progress',
    resultKey: 'devDashboard.vis.changelog.dccVis001.result',
    workspace: '/home/volker/setuphelfer/piinstaller',
    visibleSurfaces: { dcc: true },
    evidencePath: 'docs/evidence/DCC_VIS_001_VISIBLE_ROADMAP_CHANGELOG.md',
    nextStepKey: 'devDashboard.vis.changelog.dccVis001.next',
  },
  {
    id: 'TEL-012',
    titleKey: 'devDashboard.vis.changelog.tel012.title',
    status: 'planned',
    resultKey: 'devDashboard.vis.changelog.tel012.result',
    workspace: 'setuphelfer-telemetry-server',
    visibleSurfaces: { telemetry_dashboard: true, dcc: true },
    nextStepKey: 'devDashboard.vis.changelog.tel012.next',
  },
]

export function changelogByStatus(status: PhaseStatus): ChangelogItem[] {
  return DCC_VISIBILITY_CHANGELOG.filter((item) => item.status === status)
}

export function changelogItemById(id: string): ChangelogItem | undefined {
  return DCC_VISIBILITY_CHANGELOG.find((item) => item.id === id)
}
