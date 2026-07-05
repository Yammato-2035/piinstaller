import React from 'react'
import { useTranslation } from 'react-i18next'
import { DCC_VISIBILITY_CHANGELOG, type ChangelogItem, type VisibleSurface } from '../../dcc/visibility/changelogModel'
import { toneClass } from '../../pages/devDashboardFilters'

const SURFACE_KEYS: VisibleSurface[] = ['dcc', 'telemetry_dashboard', 'plesk', 'website']

function statusTone(status: ChangelogItem['status']): string {
  if (status === 'completed') return 'green'
  if (status === 'in_progress') return 'yellow'
  if (status === 'blocked') return 'red'
  return 'gray'
}

export function DccVisibleResultsPanel() {
  const { t } = useTranslation()

  return (
    <section
      className="rounded-xl border border-cyan-700/40 bg-cyan-950/15 p-4 mb-4 space-y-3"
      data-testid="dcc-visible-results-panel"
    >
      <h2 className="text-sm font-semibold text-white">{t('devDashboard.vis.results.title')}</h2>
      <p className="text-xs text-slate-400">{t('devDashboard.vis.results.subtitle')}</p>

      <div className="grid gap-3 md:grid-cols-2" data-testid="dcc-changelog-cards">
        {DCC_VISIBILITY_CHANGELOG.map((item) => (
          <article
            key={item.id}
            className={`rounded-lg border p-3 text-xs ${toneClass(statusTone(item.status))}`}
            data-testid={`dcc-changelog-card-${item.id}`}
          >
            <div className="flex items-center justify-between gap-2">
              <h3 className="font-semibold text-white">{item.id}</h3>
              <span className="rounded-full border px-2 py-0.5 text-[10px] uppercase" data-testid={`dcc-changelog-status-${item.id}`}>
                {t(`devDashboard.vis.changelog.status.${item.status}`)}
              </span>
            </div>
            <p className="mt-2 text-slate-200">{t(item.titleKey)}</p>
            <p className="mt-1 text-slate-300">{t(item.resultKey)}</p>
            <p className="mt-2 text-slate-400">
              {t('devDashboard.vis.results.workspace')}: <code className="text-slate-200">{item.workspace}</code>
            </p>
            <div className="mt-2 flex flex-wrap gap-1" data-testid={`dcc-changelog-surfaces-${item.id}`}>
              {SURFACE_KEYS.map((surface) => {
                const visible = item.visibleSurfaces[surface]
                if (visible === undefined) return null
                return (
                  <span
                    key={surface}
                    className={`rounded border px-1.5 py-0.5 text-[10px] ${visible ? 'border-emerald-600/50 text-emerald-200' : 'border-slate-600 text-slate-400'}`}
                  >
                    {t(`devDashboard.vis.surface.${surface}`)}: {visible ? t('devDashboard.vis.yes') : t('devDashboard.vis.no')}
                  </span>
                )
              })}
            </div>
            {item.evidencePath ? (
              <p className="mt-2 text-slate-500">
                {t('devDashboard.vis.results.evidence')}: <code>{item.evidencePath}</code>
              </p>
            ) : null}
            {item.nextStepKey ? (
              <p className="mt-1 text-violet-200">{t(item.nextStepKey)}</p>
            ) : null}
          </article>
        ))}
      </div>
    </section>
  )
}
