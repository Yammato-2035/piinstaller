import React from 'react'
import { useTranslation } from 'react-i18next'
import type { DccRuntimeStatusModel } from '../../dcc/visibility/runtimeStatusModel'
import { toneClass } from '../../pages/devDashboardFilters'

type Props = {
  model: DccRuntimeStatusModel
}

export function DccRuntimeStatusPanel({ model }: Props) {
  const { t } = useTranslation()

  return (
    <section
      className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 mb-4"
      data-testid="dcc-runtime-status-panel"
    >
      <h2 className="text-sm font-semibold text-white mb-1">
        {t('devDashboard.vis.runtime.title')}
      </h2>
      <p className="text-xs text-slate-400 mb-3">{t('devDashboard.vis.runtime.subtitle')}</p>
      {model.misleadingApiOffline ? (
        <p className="text-xs text-amber-200/90 mb-3 rounded border border-amber-700/40 bg-amber-950/20 px-2 py-1.5" data-testid="dcc-runtime-misleading-hint">
          {t('devDashboard.vis.runtime.misleadingHint')}
        </p>
      ) : null}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-2" data-testid="dcc-runtime-status-axes">
        {model.axes.map((axis) => (
          <div
            key={axis.key}
            className={`rounded-lg border px-3 py-2 text-xs ${toneClass(axis.tone)}`}
            data-testid={`dcc-runtime-axis-${axis.key}`}
          >
            <div className="text-[10px] uppercase tracking-wide opacity-80">{t(axis.labelKey)}</div>
            <div className="font-semibold mt-1">{t(axis.valueKey)}</div>
          </div>
        ))}
      </div>
    </section>
  )
}
