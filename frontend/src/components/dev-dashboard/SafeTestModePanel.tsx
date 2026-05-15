import type { CockpitPanelProps } from './types'

export function SafeTestModePanel({ dashboard, t }: CockpitPanelProps) {
  const stm = (dashboard?.safe_test_mode as Record<string, unknown>) || {}
  const locked = stm.locked === true
  const blocked = Array.isArray(stm.blocked_operations) ? (stm.blocked_operations as string[]) : []
  return (
    <div
      className={`rounded-xl border p-4 ${locked ? 'border-rose-600/60 bg-rose-950/30' : 'border-emerald-600/50 bg-emerald-950/20'}`}
      data-testid="dev-dashboard-safe-test-mode-panel"
    >
      <h2 className="text-base font-semibold text-white">{t('devDashboard.safeTestMode.title')}</h2>
      <p className="mt-1 font-mono text-lg">{String(stm.mode || '—')}</p>
      <p className="text-xs text-slate-300 mt-2">{t(locked ? 'devDashboard.safeTestMode.locked' : 'devDashboard.safeTestMode.unlocked')}</p>
      {locked && blocked.length > 0 ? (
        <p className="text-xs text-amber-200 mt-2">{t('devDashboard.testsInvalidWhenBlocked')}</p>
      ) : null}
      {blocked.length > 0 ? (
        <ul className="mt-2 list-disc pl-4 text-xs text-slate-300">
          {blocked.map((op) => (
            <li key={op}>{op}</li>
          ))}
        </ul>
      ) : null}
    </div>
  )
}
