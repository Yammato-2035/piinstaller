import type { CockpitPanelProps } from './types'
import { toneClass } from '../../pages/devDashboardFilters'
import { isDashboardGreenStatus } from '../../viewmodels/statusViewModel'

type StableItem = {
  id: string
  label: string
  value: string
  tone: string
  evidence?: string
}

export function ReadyStableSection({ dashboard, t }: CockpitPanelProps) {
  const rg = (dashboard?.runtime_gate as Record<string, unknown>) || {}
  const dd = (dashboard?.deploy_drift as Record<string, unknown>) || {}
  const stm = (dashboard?.safe_test_mode as Record<string, unknown>) || {}
  const dataSource = String(dashboard?.roadmap_data_source || dashboard?.data_source || 'unknown')

  const items: StableItem[] = []
  if (rg.passed === true || isDashboardGreenStatus(rg.status)) {
    items.push({
      id: 'runtime_gate',
      label: t('devDashboard.runtimeGate.title'),
      value: t('devDashboard.greenVisibility.ok'),
      tone: 'green',
      evidence: 'scripts/check-runtime-deploy-gate.sh',
    })
  }
  if (isDashboardGreenStatus(dd.status)) {
    items.push({
      id: 'deploy_drift',
      label: t('devDashboard.deployDrift.title'),
      value: String(dd.status || 'green'),
      tone: 'green',
      evidence: 'GET /api/dev-dashboard/deploy/status',
    })
  }
  if (stm.locked === false && isDashboardGreenStatus(stm.mode)) {
    items.push({
      id: 'safe_test_mode',
      label: t('devDashboard.safeTestMode.title'),
      value: String(stm.mode || '—'),
      tone: 'green',
    })
  }

  if (items.length === 0) return null

  return (
    <section
      className="rounded-xl border border-emerald-700/50 bg-emerald-950/25 p-4 ring-1 ring-emerald-600/30"
      data-testid="dev-dashboard-ready-stable"
    >
      <h2 className="text-base font-semibold text-emerald-100">{t('devDashboard.greenVisibility.readyTitle')}</h2>
      <p className="text-xs text-emerald-200/80 mt-1">{t('devDashboard.greenVisibility.readySubtitle')}</p>
      <p className="text-[11px] text-slate-400 mt-2">{t('devDashboard.greenVisibility.dataSource')}: {dataSource}</p>
      <ul className="mt-3 space-y-2">
        {items.map((item) => (
          <li
            key={item.id}
            className={`rounded-lg border px-3 py-2 text-sm flex flex-wrap items-center justify-between gap-2 ${toneClass(item.tone)}`}
            data-testid={`dev-dashboard-stable-${item.id}`}
          >
            <span>
              <span className="font-semibold">{item.label}</span>
              <span className="mx-2 text-emerald-300">·</span>
              <span className="font-mono text-xs">{item.value}</span>
            </span>
            {item.evidence ? (
              <span className="text-[10px] text-slate-400 font-mono truncate max-w-full">{item.evidence}</span>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  )

}
