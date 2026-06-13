import type { DashboardPayload } from '../../pages/DevDashboardBody'
import type { GovernanceAreaStatus, GovernanceTimelineEvent } from './governanceTypes'
import type { DevDashboardDataSource } from './types'
import { isGreenGovernanceTraffic, isRedGovernanceTraffic, isYellowGovernanceTraffic } from '../../viewmodels/statusViewModel'

function workOrder(areas: GovernanceAreaStatus[]): string[] {
  const steps: string[] = []
  const runtime = areas.find((a) => a.id === 'runtime')
  const gates = areas.find((a) => a.id === 'runtime_gates')
  const evidence = areas.find((a) => a.id === 'evidence')
  const backup = areas.find((a) => a.id === 'backup')
  const restore = areas.find((a) => a.id === 'restore')

  if (!runtime || !isGreenGovernanceTraffic(runtime.status)) steps.push('1. Runtime deploy + API erreichbar machen')
  if (!gates || !isGreenGovernanceTraffic(gates.status)) steps.push('2. ./scripts/check-runtime-deploy-gate.sh (Exit 0)')
  if (!evidence || !isGreenGovernanceTraffic(evidence.status)) steps.push('3. Evidence-Dateien unter docs/evidence/release-gates/ reparieren')
  if (backup && isRedGovernanceTraffic(backup.status)) steps.push('4. BR-001-OFFLINE Rettungsstick (kein Live-Desktop-Gate-Retry)')
  if (restore && isRedGovernanceTraffic(restore.status)) steps.push('5. Restore Preview / Sandbox-Gates')
  if (!steps.length) steps.push('1. Gate grün halten; fokussierte Änderungen mit erneutem Gate-Check')
  return steps
}

export function buildGovernanceMetaPrompt(params: {
  dashboard: DashboardPayload
  workspaceRoot: string
  source: DevDashboardDataSource
  apiReachable: boolean
  areas: GovernanceAreaStatus[]
  changedToGreen: GovernanceAreaStatus[]
  regressed: GovernanceAreaStatus[]
  timeline: GovernanceTimelineEvent[]
  basePrompt?: string
}): string {
  const { dashboard, workspaceRoot, source, apiReachable, areas, changedToGreen, regressed, timeline } = params
  const rg = (dashboard?.runtime_gate as Record<string, unknown>) || {}
  const stm = (dashboard?.safe_test_mode as Record<string, unknown>) || {}

  const redAreas = areas.filter((a) => isRedGovernanceTraffic(a.status)).map((a) => a.id)
  const greenAreas = areas.filter((a) => isGreenGovernanceTraffic(a.status)).map((a) => a.id)
  const yellowAreas = areas.filter((a) => isYellowGovernanceTraffic(a.status)).map((a) => a.id)

  const lines = [
    '# Setuphelfer Development Control Center — Governance Meta-Prompt',
    '',
    '## Modus',
    apiReachable && source === 'runtime_api'
      ? '**RUNTIME_API** — Live-Governance aus produktiver API.'
      : `**${source.toUpperCase()}** — Keine produktive Runtime; Runtime-Tests gesperrt.`,
    '',
    `Workspace: ${workspaceRoot}`,
    `Generiert: ${new Date().toISOString()}`,
    '',
    '## Verbotene Aktionen (STRICT)',
    '- backup / restore ohne grünes Gate',
    '- hardware_tests / rescue_tests im LOCKED-Modus',
    '- apt_install / apt_upgrade / automatic_deploy',
    '- git add -A',
  '',
    '## Runtime / Safe Test',
    `- runtime_gate_passed: ${rg.passed === true}`,
    `- safe_test_mode: ${stm.mode ?? 'LOCKED'}`,
    `- blockers: ${((rg.blockers as string[]) || []).join(', ') || '—'}`,
    '',
    '## Modulboard (aktuell)',
    `- rot: ${redAreas.join(', ') || '—'}`,
    `- gelb: ${yellowAreas.join(', ') || '—'}`,
    `- grün: ${greenAreas.join(', ') || '—'}`,
    '',
    '## Statusübergänge (echte Historie, lokal)',
    `### Neu grün (${changedToGreen.length})`,
    ...(changedToGreen.length
      ? changedToGreen.map((a) => `- ${a.id} (${a.previousStatus ?? '?'} → green)`)
      : ['- (keine neuen Übergänge in diesem Tick)']),
    `### Regressionen (${regressed.length})`,
    ...(regressed.length
      ? regressed.map((a) => `- ${a.id} (${a.previousStatus ?? '?'} → ${a.status})`)
      : ['- (keine Regressionen in diesem Tick)']),
    '',
    '## Timeline (letzte Ereignisse)',
    ...timeline.slice(0, 15).map((e) => `- [${e.severity}] ${e.at}: ${e.message}`),
    '',
    '## Recommended Cursor Work Order',
    ...workOrder(areas),
    '',
    '## Format',
    '- Fokussierte Diffs; Phase 0 Gate vor Runtime-Tests',
    '- Abschlussbericht bei blocked_runtime_outdated',
  ]

  if (params.basePrompt) {
    lines.push('', '---', '', '## Basis-Prompt', '', params.basePrompt)
  }

  return lines.join('\n')
}
