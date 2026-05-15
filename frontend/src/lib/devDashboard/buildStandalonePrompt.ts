import type { DashboardPayload } from '../../pages/DevDashboardBody'

export function buildStandaloneMetaPrompt(
  dashboard: DashboardPayload,
  workspaceRoot: string,
): string {
  const sh = (dashboard?.structure_health as Record<string, unknown>) || {}
  const rg = (dashboard?.runtime_gate as Record<string, unknown>) || {}
  const stm = (dashboard?.safe_test_mode as Record<string, unknown>) || {}
  const findings: Array<Record<string, unknown>> = [
    ...((sh.critical_findings as Array<Record<string, unknown>>) || []),
    ...((sh.warnings as Array<Record<string, unknown>>) || []),
  ]

  const forbidden = [
    ...(Array.isArray(stm.blocked_operations) ? (stm.blocked_operations as string[]) : []),
    'apt_install',
    'apt_upgrade',
    'git_add_all',
    'automatic_deploy',
    'backup',
    'restore',
    'hardware_tests',
  ]

  const lines = [
    '# Setuphelfer Development Control Cockpit — Cursor Meta-Prompt',
    '',
    '## Modus',
    '**STANDALONE** — produktive Runtime-API (Port 8000 / /opt) war beim Laden nicht erreichbar.',
    'Runtime-Tests und Backup/Restore sind gesperrt, bis `./scripts/check-runtime-deploy-gate.sh` Exit 0 liefert.',
    '',
    '## Kontext',
    `Workspace (lokal analysiert): ${workspaceRoot}`,
    `Generiert: ${new Date().toISOString()}`,
    '',
    '## Verbotene Aktionen (STRICT)',
    ...[...new Set(forbidden)].map((a) => `- ${a}`),
    '',
    '## Runtime / Safe Test Mode',
    `- runtime_gate_passed: ${rg.passed === true}`,
    `- safe_test_mode: ${stm.mode ?? 'LOCKED'}`,
    `- blockers: ${(rg.blockers as string[] | undefined)?.join(', ') || 'backend_api_unreachable'}`,
    '',
    '## Findings',
    ...(findings.length
      ? findings.map((f) => `- [${f.severity || '?'}] ${f.id}: ${f.message}`)
      : ['- (keine strukturierten Findings)']),
    '',
    '## Gewünschtes Cursor-Format',
    '- Nur fokussierte Änderungen; keine git add -A',
    '- Phase 0: check-runtime-deploy-gate.sh vor Runtime-/HW-Tests',
    '- Keine Mock-Daten als produktiv markieren',
  ]
  return lines.join('\n')
}
