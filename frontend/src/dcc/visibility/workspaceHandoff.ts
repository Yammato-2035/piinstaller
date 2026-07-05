export type WorkspaceHandoff = {
  currentWorkspace: string
  currentPhase: string
  currentBranch?: string
  currentCommit?: string
  nextWorkspace: string
  nextPhase: string
  reasonKey: string
  allowedKey: string
  forbiddenKey: string
}

export const DEFAULT_WORKSPACE_HANDOFF: WorkspaceHandoff = {
  currentWorkspace: '/home/volker/setuphelfer/piinstaller',
  currentPhase: 'DCC-VIS-001',
  nextWorkspace: '/home/volker/setuphelfer-private/setuphelfer-telemetry-server',
  nextPhase: 'TEL-012',
  reasonKey: 'devDashboard.vis.handoff.reasonTel012',
  allowedKey: 'devDashboard.vis.handoff.allowedTel012',
  forbiddenKey: 'devDashboard.vis.handoff.forbiddenTel012',
}

export function buildWorkspaceHandoff(overrides?: Partial<WorkspaceHandoff>): WorkspaceHandoff {
  return { ...DEFAULT_WORKSPACE_HANDOFF, ...overrides }
}
