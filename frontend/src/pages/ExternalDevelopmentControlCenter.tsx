import React, { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { Activity, Copy, RefreshCw, Terminal } from 'lucide-react'
import { StandaloneModeBanner } from '../components/dev-dashboard/StandaloneModeBanner'
import { RuntimeGatePanel } from '../components/dev-dashboard/RuntimeGatePanel'
import { DeployDriftPanel } from '../components/dev-dashboard/DeployDriftPanel'
import { SafeTestModePanel } from '../components/dev-dashboard/SafeTestModePanel'
import { writeCockpitRefreshSec } from '../lib/devDashboard/cockpitWindow'
import { AREA_LABELS } from '../lib/devDashboard/governanceMatrix'
import { clearGovernanceHistory } from '../lib/devDashboard/governanceHistory'
import type { CockpitViewMode, GovernanceAreaStatus, Traffic } from '../lib/devDashboard/governanceTypes'
import { useGovernanceMonitor } from '../lib/devDashboard/useGovernanceMonitor'
import { toneClass } from './devDashboardFilters'

function trafficDot(status: Traffic): string {
  if (status === 'green') return 'bg-emerald-500'
  if (status === 'yellow') return 'bg-amber-400'
  if (status === 'red') return 'bg-red-500'
  return 'bg-slate-500'
}

function GovernanceMatrixGrid({ areas, t }: { areas: GovernanceAreaStatus[]; t: (k: string) => string }) {
  return (
    <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-2" data-testid="governance-matrix">
      {areas.map((a) => (
        <div
          key={a.id}
          className={`rounded-lg border px-3 py-2 text-sm ${toneClass(a.status)}`}
          data-testid={`governance-area-${a.id}`}
        >
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${trafficDot(a.status)}`} aria-hidden />
            <span className="font-medium text-white">{t(AREA_LABELS[a.id])}</span>
            {a.changedToGreen ? (
              <span className="ml-auto text-[10px] uppercase tracking-wide text-emerald-300">
                {t('devDashboard.governance.becameGreen')}
              </span>
            ) : null}
            {a.regressed ? (
              <span className="ml-auto text-[10px] uppercase tracking-wide text-red-300">
                {t('devDashboard.governance.regressed')}
              </span>
            ) : null}
          </div>
          {a.blockers[0] ? <p className="text-xs text-slate-300 mt-1 truncate">{a.blockers[0]}</p> : null}
        </div>
      ))}
    </div>
  )
}

export const ExternalDevelopmentControlCenter: React.FC = () => {
  const { t } = useTranslation()
  const statusQuery = useMemo(() => {
    const params = new URLSearchParams()
    const fv =
      typeof __APP_VERSION__ !== 'undefined' && String(__APP_VERSION__).trim() ? String(__APP_VERSION__).trim() : ''
    if (fv) params.set('frontend_build_version', fv)
    params.set('frontend_runtime_source', import.meta.env.DEV ? 'dev' : 'build')
    return params.toString()
  }, [])

  const mon = useGovernanceMonitor(statusQuery)

  const viewBtn = (mode: CockpitViewMode, label: string) => (
    <button
      type="button"
      data-testid={`cockpit-view-${mode}`}
      onClick={() => mon.setViewMode(mode)}
      className={`px-3 py-1.5 rounded-md text-xs font-medium border ${
        mon.viewMode === mode
          ? 'bg-violet-900/70 border-violet-500/60 text-white'
          : 'border-slate-600 text-slate-300 hover:bg-slate-800/60'
      }`}
    >
      {label}
    </button>
  )

  const copyPrompt = async () => {
    if (!mon.governancePrompt) {
      toast.error(t('devDashboard.noData'))
      return
    }
    try {
      await navigator.clipboard.writeText(mon.governancePrompt)
      toast.success(t('devDashboard.governance.promptCopied'))
    } catch {
      toast.error(t('devDashboard.noData'))
    }
  }

  const onRefreshInterval = (sec: number) => {
    writeCockpitRefreshSec(sec)
    mon.setRefreshSec(sec)
  }

  return (
    <div className="max-w-[1600px] mx-auto px-4 py-5" data-testid="external-development-control-center">
      <header className="flex flex-wrap items-start justify-between gap-4 mb-4 border-b border-slate-700 pb-4">
        <div>
          <h1 className="text-xl font-semibold text-white flex items-center gap-2">
            <Terminal className="text-violet-400" size={24} aria-hidden />
            {t('devDashboard.governance.title')}
          </h1>
          <p className="text-sm text-slate-400 mt-1">{t('devDashboard.governance.subtitle')}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {viewBtn('operations', t('devDashboard.governance.view.operations'))}
          {viewBtn('compact', t('devDashboard.governance.view.compact'))}
          {viewBtn('timeline', t('devDashboard.governance.view.timeline'))}
          <label className="text-xs text-slate-400 flex items-center gap-1">
            {t('devDashboard.governance.refreshSec')}
            <select
              className="bg-slate-900 border border-slate-600 rounded px-1 py-0.5 text-slate-200"
              value={mon.refreshSec}
              onChange={(e) => onRefreshInterval(Number(e.target.value))}
              data-testid="cockpit-refresh-interval"
            >
              {[5, 8, 10, 12, 15].map((n) => (
                <option key={n} value={n}>
                  {n}s
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="btn-secondary inline-flex items-center gap-1 text-xs"
            onClick={() => void mon.refresh()}
            disabled={mon.loading}
            data-testid="cockpit-refresh"
          >
            <RefreshCw className={mon.loading ? 'animate-spin' : ''} size={14} />
            {t('backup.ui.refresh')}
          </button>
          <button
            type="button"
            className="btn-primary inline-flex items-center gap-1 text-xs"
            onClick={() => void copyPrompt()}
            data-testid="cockpit-copy-prompt"
          >
            <Copy size={14} />
            {t('devDashboard.governance.copyPrompt')}
          </button>
        </div>
      </header>

      <StandaloneModeBanner
        source={mon.source}
        apiReachable={mon.apiReachable}
        capabilities={mon.capabilities}
        workspaceRoot={mon.workspaceRoot}
      />

      {mon.alerts.length > 0 ? (
        <ul className="mb-4 space-y-1" data-testid="cockpit-alerts">
          {mon.alerts.slice(0, 8).map((a) => (
            <li
              key={a.id}
              className={`text-xs px-3 py-2 rounded border ${
                a.severity === 'critical'
                  ? 'border-red-700/60 bg-red-950/40 text-red-100'
                  : a.severity === 'warning'
                    ? 'border-amber-700/50 bg-amber-950/30 text-amber-100'
                    : 'border-sky-700/40 bg-sky-950/20 text-sky-100'
              }`}
            >
              {a.message}
            </li>
          ))}
        </ul>
      ) : null}

      {(mon.changedToGreen.length > 0 || mon.regressed.length > 0) && (
        <div className="grid md:grid-cols-2 gap-3 mb-4" data-testid="cockpit-transitions">
          <div className="rounded-lg border border-emerald-700/40 bg-emerald-950/20 p-3">
            <h2 className="text-sm font-semibold text-emerald-200 flex items-center gap-1">
              <Activity size={14} />
              {t('devDashboard.governance.greenTransitions')}
            </h2>
            <ul className="text-xs text-emerald-100/90 mt-2 space-y-1">
              {mon.changedToGreen.length
                ? mon.changedToGreen.map((a) => (
                    <li key={a.id}>
                      {t(AREA_LABELS[a.id])} ({a.previousStatus} → green)
                    </li>
                  ))
                : [{ key: 'none', text: t('devDashboard.governance.noGreenTransitions') }].map((x) => (
                    <li key={x.key}>{x.text}</li>
                  ))}
            </ul>
          </div>
          <div className="rounded-lg border border-red-700/40 bg-red-950/20 p-3">
            <h2 className="text-sm font-semibold text-red-200">{t('devDashboard.governance.regressions')}</h2>
            <ul className="text-xs text-red-100/90 mt-2 space-y-1">
              {mon.regressed.length
                ? mon.regressed.map((a) => (
                    <li key={a.id}>
                      {t(AREA_LABELS[a.id])} ({a.previousStatus} → {a.status})
                    </li>
                  ))
                : [{ key: 'none', text: t('devDashboard.governance.noRegressions') }].map((x) => (
                    <li key={x.key}>{x.text}</li>
                  ))}
            </ul>
          </div>
        </div>
      )}

      {mon.viewMode === 'timeline' ? (
        <section className="rounded-xl border border-slate-700 bg-slate-900/50 p-4" data-testid="cockpit-timeline">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-base font-semibold text-white">{t('devDashboard.governance.timeline')}</h2>
            <button
              type="button"
              className="text-xs text-slate-400 hover:text-slate-200"
              onClick={() => {
                clearGovernanceHistory()
                void mon.refresh()
              }}
            >
              {t('devDashboard.governance.clearHistory')}
            </button>
          </div>
          <ul className="space-y-2 max-h-[70vh] overflow-y-auto text-xs">
            {mon.timeline.length ? (
              mon.timeline.map((e) => (
                <li key={e.id} className="border-l-2 border-slate-600 pl-3 py-1">
                  <span className="text-slate-500">{e.at}</span> — {e.message}
                </li>
              ))
            ) : (
              <li className="text-slate-400">{t('devDashboard.governance.timelineEmpty')}</li>
            )}
          </ul>
        </section>
      ) : (
        <>
          <section className="mb-4">
            <h2 className="text-sm font-semibold text-slate-300 mb-2">{t('devDashboard.governance.matrixTitle')}</h2>
            <GovernanceMatrixGrid areas={mon.areas} t={t} />
          </section>

          {mon.viewMode === 'operations' && mon.dashboard ? (
            <section className="space-y-4" data-testid="cockpit-operations-panels">
              <RuntimeGatePanel dashboard={mon.dashboard} t={t} />
              <SafeTestModePanel dashboard={mon.dashboard} t={t} />
              <DeployDriftPanel dashboard={mon.dashboard} t={t} />
            </section>
          ) : null}
        </>
      )}

      <p className="text-[11px] text-slate-500 mt-6 border-t border-slate-800 pt-3">
        {t('devDashboard.governance.readOnlyFooter')}
      </p>
    </div>
  )
}
