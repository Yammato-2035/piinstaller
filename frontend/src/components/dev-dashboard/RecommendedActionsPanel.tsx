import type { CockpitPanelProps } from './types'

export function RecommendedActionsPanel({ dashboard, t }: CockpitPanelProps) {
  const sh = (dashboard?.structure_health as Record<string, unknown>) || {}
  const actions = Array.isArray(sh.recommended_next_actions) ? (sh.recommended_next_actions as string[]) : []
  const drift = (dashboard?.deploy_drift as Record<string, unknown>) || {}
  const suggested = Array.isArray(drift.suggested_actions) ? (drift.suggested_actions as string[]) : []
  const combined = [...new Set([...actions, ...suggested.filter((x) => x !== 'none')])]
  if (!combined.length) return null
  return (
    <div className="rounded-xl border border-sky-700/40 bg-sky-950/20 p-4" data-testid="dev-dashboard-recommended-actions-panel">
      <h2 className="text-base font-semibold text-white">{t('devDashboard.recommendedActions.title')}</h2>
      <ul className="mt-2 list-disc pl-4 text-xs text-sky-100">
        {combined.map((a) => (
          <li key={a}>
            {a.startsWith('deploy_') || a.startsWith('restart_') || a.startsWith('generate_')
              ? t(`devDashboard.deployDrift.action.${a}`, { defaultValue: a })
              : a}
          </li>
        ))}
      </ul>
    </div>
  )
}
