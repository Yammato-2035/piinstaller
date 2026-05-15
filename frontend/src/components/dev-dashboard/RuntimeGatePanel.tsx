import type { CockpitPanelProps } from './types'
import { toneClass } from '../../pages/devDashboardFilters'

export function RuntimeGatePanel({ dashboard, t }: CockpitPanelProps) {
  const rg = (dashboard?.runtime_gate as Record<string, unknown>) || {}
  const tone = String(rg.status || 'gray')
  const blockers = Array.isArray(rg.blockers) ? (rg.blockers as string[]) : []
  return (
    <div className={`rounded-xl border p-4 ${toneClass(tone)}`} data-testid="dev-dashboard-runtime-gate-panel">
      <h2 className="text-base font-semibold text-white">{t('devDashboard.runtimeGate.title')}</h2>
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
