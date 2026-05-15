import type { CockpitPanelProps } from './types'
import { toneClass } from '../../pages/devDashboardFilters'

export function PackageGatePanel({ dashboard, t }: CockpitPanelProps) {
  const pg = (dashboard?.package_gate as Record<string, unknown>) || {}
  const tone = String(pg.status || 'gray')
  return (
    <div className={`rounded-xl border p-4 ${toneClass(tone)}`} data-testid="dev-dashboard-package-gate-panel">
      <h2 className="text-base font-semibold text-white">{t('devDashboard.packageGate.title')}</h2>
      <p className="text-xs text-slate-300 mt-1">{t('devDashboard.packageGate.subtitle')}</p>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div>
          <dt className="text-slate-500">{t('devDashboard.packageGate.debInstalled')}</dt>
          <dd>{pg.deb_installed === true ? '✓' : pg.deb_installed === false ? '✗' : '—'}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.packageGate.runtimePresent')}</dt>
          <dd>{pg.runtime_tree_present === true ? '✓' : '✗'}</dd>
        </div>
        <div className="col-span-2">
          <dt className="text-slate-500">{t('devDashboard.packageGate.requiresConfirmation')}</dt>
          <dd>{pg.requires_confirmation === true ? t('devDashboard.packageGate.yes') : '—'}</dd>
        </div>
      </dl>
    </div>
  )
}
