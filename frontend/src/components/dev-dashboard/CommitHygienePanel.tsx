import type { CockpitPanelProps } from './types'

export function CommitHygienePanel({ dashboard, t }: CockpitPanelProps) {
  const sh = (dashboard?.structure_health as Record<string, unknown>) || {}
  const git = (sh.git_hygiene as Record<string, unknown>) || {}
  const ws = (dashboard?.workspace as Record<string, unknown>) || {}
  return (
    <div className="rounded-xl border border-slate-600 bg-slate-900/50 p-4" data-testid="dev-dashboard-commit-hygiene-panel">
      <h2 className="text-base font-semibold text-white">{t('devDashboard.commitHygiene.title')}</h2>
      <dl className="mt-2 grid grid-cols-2 gap-2 text-xs">
        <div>
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.dirtyCount')}</dt>
          <dd>{git.dirty_count != null ? String(git.dirty_count) : String(ws.git_dirty_count ?? '—')}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.commitHygiene.untracked')}</dt>
          <dd>{git.untracked_count != null ? String(git.untracked_count) : '—'}</dd>
        </div>
        <div className="col-span-2">
          <dt className="text-slate-500">{t('devDashboard.commitHygiene.addAllRisk')}</dt>
          <dd>{git.add_all_risk === true ? t('devDashboard.commitHygiene.yes') : t('devDashboard.commitHygiene.no')}</dd>
        </div>
      </dl>
    </div>
  )
}
