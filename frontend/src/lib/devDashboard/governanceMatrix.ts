import type { DashboardPayload, ModuleRow } from '../../pages/DevDashboardBody'
import type { CockpitAlert, GovernanceAreaId, GovernanceAreaStatus, Traffic } from './governanceTypes'
import type { DevDashboardDataSource } from './types'

const AREA_LABELS: Record<GovernanceAreaId, string> = {
  runtime: 'devDashboard.governance.area.runtime',
  backup: 'devDashboard.governance.area.backup',
  restore: 'devDashboard.governance.area.restore',
  verify: 'devDashboard.governance.area.verify',
  rescue: 'devDashboard.governance.area.rescue',
  hardware: 'devDashboard.governance.area.hardware',
  packaging: 'devDashboard.governance.area.packaging',
  diagnostics: 'devDashboard.governance.area.diagnostics',
  evidence: 'devDashboard.governance.area.evidence',
  ci: 'devDashboard.governance.area.ci',
  docs: 'devDashboard.governance.area.docs',
  i18n: 'devDashboard.governance.area.i18n',
  prompt_export: 'devDashboard.governance.area.promptExport',
  runtime_gates: 'devDashboard.governance.area.runtimeGates',
  cloud_edition: 'devDashboard.governance.area.cloudEdition',
  host_pilot: 'devDashboard.governance.area.hostPilot',
}

function normTraffic(raw: unknown): Traffic {
  const s = String(raw || 'gray').toLowerCase()
  if (s === 'green' || s === 'yellow' || s === 'red') return s
  return 'gray'
}

function moduleTraffic(modules: ModuleRow[], needle: RegExp): Traffic {
  const hit = modules.filter((m) => needle.test(String(m.id || '') + String(m.area || '') + String(m.title || '')))
  if (!hit.length) return 'gray'
  if (hit.some((m) => normTraffic(m.status) === 'red')) return 'red'
  if (hit.some((m) => normTraffic(m.status) === 'yellow')) return 'yellow'
  if (hit.every((m) => normTraffic(m.status) === 'green')) return 'green'
  return 'yellow'
}

export function buildGovernanceMatrix(params: {
  dashboard: DashboardPayload
  modules: ModuleRow[]
  source: DevDashboardDataSource
  apiReachable: boolean
}): GovernanceAreaStatus[] {
  const { dashboard, modules, source, apiReachable } = params
  const now = new Date().toISOString()
  const rg = (dashboard?.runtime_gate as Record<string, unknown>) || {}
  const dd = (dashboard?.deploy_drift as Record<string, unknown>) || {}
  const pg = (dashboard?.package_gate as Record<string, unknown>) || {}
  const sh = (dashboard?.structure_health as Record<string, unknown>) || {}
  const te = (dashboard?.tests_evidence as Record<string, unknown>) || {}
  const stm = (dashboard?.safe_test_mode as Record<string, unknown>) || {}

  const runtimeGatePassed = rg.passed === true
  const deployStatus = normTraffic(dd.status)
  const structureStatus = normTraffic(sh.status)
  const packageStatus = normTraffic(pg.status)
  const testsStatus = normTraffic(te.status)

  const mk = (
    id: GovernanceAreaId,
    status: Traffic,
    blockers: string[] = [],
    recommendedAction?: string,
  ): GovernanceAreaStatus => ({
    id,
    status,
    labelKey: AREA_LABELS[id],
    blockers,
    recommendedAction,
    lastCheckedAt: now,
  })

  const areas: GovernanceAreaStatus[] = [
    mk(
      'runtime',
      !apiReachable || source !== 'runtime_api' ? 'red' : runtimeGatePassed ? 'green' : normTraffic(rg.status),
      !apiReachable ? ['backend_api_unreachable'] : ((rg.blockers as string[]) || []),
      !apiReachable
        ? 'Runtime-API starten; check-runtime-deploy-gate.sh'
        : './scripts/check-runtime-deploy-gate.sh',
    ),
    mk(
      'backup',
      (() => {
        const br001 = (dashboard?.br001_gates as Record<string, unknown>) || {}
        const offlineSide = (br001.offline as Record<string, unknown>) || {}
        return offlineSide.status != null ? normTraffic(offlineSide.status) : moduleTraffic(modules, /backup/i)
      })(),
      [],
      'BR-001-OFFLINE (Rettungsstick) — kein Live-Desktop-Gate',
    ),
    mk('restore', moduleTraffic(modules, /restore/i), [], 'Restore-Evidence prüfen'),
    mk('verify', stm.locked ? 'yellow' : runtimeGatePassed ? 'green' : 'red', [], 'Verify nach grünem Gate'),
    mk('rescue', moduleTraffic(modules, /rescue/i), [], 'Rescue-Stick Evidence'),
    mk('hardware', stm.locked ? 'red' : 'gray', stm.locked ? ['safe_test_mode_locked'] : [], 'HW nur nach Gate'),
    mk('packaging', packageStatus, [], 'Kein apt upgrade ohne Freigabe'),
    mk('diagnostics', moduleTraffic(modules, /diagnostic/i), []),
    mk(
      'evidence',
      testsStatus === 'green' ? 'green' : testsStatus === 'red' ? 'red' : 'yellow',
      [],
      'docs/evidence/release-gates/*.json',
    ),
    mk('ci', testsStatus, [], 'pytest / CI Evidence'),
    mk(
      'docs',
      structureStatus === 'green' ? 'green' : 'yellow',
      [],
      'docs/roadmap/STATUS_MATRIX.md',
    ),
    mk('i18n', 'gray', [], 'frontend/src/locales'),
    mk('prompt_export', 'green', [], 'KI-Export (read-only)'),
    mk(
      'runtime_gates',
      runtimeGatePassed ? 'green' : 'red',
      (rg.blockers as string[]) || [],
      './scripts/check-runtime-deploy-gate.sh',
    ),
    mk('cloud_edition', 'gray'),
    mk('host_pilot', 'gray'),
  ]

  return areas
}

export function buildCockpitAlerts(
  areas: GovernanceAreaStatus[],
  params: { apiReachable: boolean; source: DevDashboardDataSource },
): CockpitAlert[] {
  const alerts: CockpitAlert[] = []
  if (!params.apiReachable) {
    alerts.push({
      id: 'api-offline',
      severity: 'critical',
      code: 'backend_api_unreachable',
      message: 'Runtime-API offline — Live-Daten nur aus Workspace/Snapshot',
    })
  }
  if (params.source !== 'runtime_api') {
    alerts.push({
      id: 'non-runtime-source',
      severity: 'warning',
      code: 'non_runtime_api_source',
      message: `Datenquelle: ${params.source} (keine produktive Runtime)`,
    })
  }
  for (const a of areas) {
    if (a.status === 'red') {
      alerts.push({
        id: `area-red-${a.id}`,
        severity: 'critical',
        code: `${a.id}_blocked`,
        message: a.blockers[0] || `${a.id} rot`,
        areaId: a.id,
      })
    }
    if (a.changedToGreen) {
      alerts.push({
        id: `area-green-${a.id}-${a.lastCheckedAt}`,
        severity: 'info',
        code: 'module_became_green',
        message: `${a.id} neu grün`,
        areaId: a.id,
      })
    }
    if (a.regressed) {
      alerts.push({
        id: `area-reg-${a.id}-${a.lastCheckedAt}`,
        severity: 'critical',
        code: 'regression_detected',
        message: `${a.id} Regression`,
        areaId: a.id,
      })
    }
  }
  return alerts
}

export { AREA_LABELS }
