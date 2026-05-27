import type { CockpitPanelProps } from './types'
import { toneClass } from '../../pages/devDashboardFilters'

export function RuntimeGatePanel({ dashboard, t }: CockpitPanelProps) {
  const rg = (dashboard?.runtime_gate as Record<string, unknown>) || {}
  const tone = String(rg.status || 'gray')
  const passed = rg.passed === true
  const blockers = Array.isArray(rg.blockers) ? (rg.blockers as string[]) : []
  return (
    <div
      className={`rounded-xl border p-4 ${toneClass(tone)}${passed ? ' ring-1 ring-emerald-500/30' : ''}`}
      data-testid="dev-dashboard-runtime-gate-panel"
    >
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="text-base font-semibold text-white">{t('devDashboard.runtimeGate.title')}</h2>
        {passed ? (
          <span className="text-[10px] font-bold uppercase text-emerald-300 border border-emerald-600/50 rounded px-2 py-0.5">
            {t('devDashboard.greenVisibility.ok')}
          </span>
        ) : null}
      </div>
      <p className="text-xs text-slate-300 mt-1">{t('devDashboard.runtimeGate.subtitle')}</p>
      <p className="mt-2 font-mono text-sm">
        {t('devDashboard.runtimeGate.passed')}: {rg.passed === true ? '✓' : '✗'}
      </p>
      {blockers.length > 0 ? (
        <ul className="mt-2 list-disc pl-4 text-xs text-rose-200">
          {blockers.map((b) => (
            <li key={b}>{b}</li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
