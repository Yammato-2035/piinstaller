import type { CockpitPanelProps } from './types'
import { toneClass } from '../../pages/devDashboardFilters'

export function StructuralHealthPanel({ dashboard, t }: CockpitPanelProps) {
  const sh = (dashboard?.structure_health as Record<string, unknown>) || {}
  const tone = String(sh.status || 'gray')
  const score = sh.score != null ? String(sh.score) : '—'
  const critical = Array.isArray(sh.critical_findings) ? (sh.critical_findings as Record<string, unknown>[]) : []
  const warnings = Array.isArray(sh.warnings) ? (sh.warnings as Record<string, unknown>[]) : []
  const actions = Array.isArray(sh.recommended_next_actions) ? (sh.recommended_next_actions as string[]) : []
  return (
    <div className={`rounded-xl border p-4 ${toneClass(tone)}`} data-testid="dev-dashboard-structure-health-panel">
      <h2 className="text-base font-semibold text-white">{t('devDashboard.structureHealth.title')}</h2>
      <p className="text-sm mt-1">
        {t('devDashboard.structureHealth.score')}: <span className="font-mono font-bold">{score}</span>/100
      </p>
      {critical.length > 0 ? (
        <ul className="mt-2 list-disc pl-4 text-xs text-rose-200">
          {critical.slice(0, 8).map((f, i) => (
            <li key={`c-${i}`}>{String(f.message || f.id)}</li>
          ))}
        </ul>
      ) : null}
      {warnings.length > 0 ? (
        <ul className="mt-2 list-disc pl-4 text-xs text-amber-200">
          {warnings.slice(0, 6).map((f, i) => (
            <li key={`w-${i}`}>{String(f.message || f.id)}</li>
          ))}
        </ul>
      ) : null}
      {actions.length > 0 ? (
        <div className="mt-2 text-xs text-sky-200">
          <div className="font-semibold">{t('devDashboard.recommendedActions.title')}</div>
          <ul className="list-disc pl-4">
            {actions.map((a) => (
              <li key={a}>{a}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  )
}
