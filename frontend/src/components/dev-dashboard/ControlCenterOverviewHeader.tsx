import React from 'react'
import { useTranslation } from 'react-i18next'
import { AlertTriangle, CheckCircle2, CircleDot } from 'lucide-react'
import type { ControlCenterSummary } from '../../api/devDashboardApi'
import { toneClass } from '../../pages/devDashboardFilters'
import { dashboardLegacyToneFromInput } from '../../viewmodels/statusViewModel'

type Props = {
  summary: ControlCenterSummary | null
  loading?: boolean
  apiReachable?: boolean
}

function trafficFromGate(passed: unknown, status: unknown): string {
  if (passed === true) return 'green'
  return dashboardLegacyToneFromInput(status)
}

export function ControlCenterOverviewHeader({ summary, loading, apiReachable = true }: Props) {
  const { t } = useTranslation()
  const runtime = (summary?.runtime as Record<string, unknown>) || {}
  const roadmap = (summary?.roadmap as Record<string, unknown>) || {}
  const devServer = (summary?.dev_server as Record<string, unknown>) || {}
  const gateTone = trafficFromGate(runtime.runtime_gate_passed, runtime.runtime_gate_status)
  const blockers = Array.isArray(runtime.blockers) ? (runtime.blockers as string[]) : []
  const nextPrompts = summary?.next_prompts || []
  const recommended = nextPrompts[0]

  return (
    <section
      className="rounded-xl border border-slate-700 bg-slate-900/60 p-4 mb-4"
      data-testid="control-center-overview-header"
    >
      <div className="flex flex-wrap items-start justify-between gap-3 mb-3">
        <div>
          <h2 className="text-base font-semibold text-white">{t('devDashboard.controlCenter.overviewTitle')}</h2>
          <p className="text-xs text-slate-400 mt-1">{t('devDashboard.controlCenter.overviewSubtitle')}</p>
        </div>
        {!apiReachable ? (
          <span className="text-xs text-amber-300 border border-amber-700/50 rounded px-2 py-1">
            {t('devDashboard.controlCenter.offlineMode')}
          </span>
        ) : null}
      </div>

      {loading ? (
        <p className="text-xs text-slate-400">{t('devDashboard.controlCenter.loading')}</p>
      ) : null}

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-2 text-xs" data-testid="control-center-status-grid">
        <div className={`rounded-lg border px-3 py-2 ${toneClass(gateTone)}`}>
          <div className="text-[10px] uppercase tracking-wide opacity-80">{t('devDashboard.runtimeGate.title')}</div>
          <div className="font-semibold mt-1">{runtime.runtime_gate_passed === true ? t('devDashboard.greenVisibility.ok') : String(runtime.runtime_gate_status || 'unknown')}</div>
        </div>
        <div className={`rounded-lg border px-3 py-2 ${toneClass(String(runtime.deploy_drift_status || 'gray'))}`}>
          <div className="text-[10px] uppercase tracking-wide opacity-80">{t('devDashboard.deployDrift.title')}</div>
          <div className="font-semibold mt-1">{String(runtime.deploy_drift_status || 'unknown')}</div>
        </div>
        <div className="rounded-lg border border-slate-700 px-3 py-2">
          <div className="text-[10px] uppercase tracking-wide text-slate-400">{t('devDashboard.controlCenter.version')}</div>
          <div className="font-mono text-slate-200 mt-1">{String(runtime.version || '—')}</div>
        </div>
        <div className={`rounded-lg border px-3 py-2 ${devServer.enabled ? toneClass('green') : toneClass('gray')}`}>
          <div className="text-[10px] uppercase tracking-wide opacity-80">{t('devDashboard.devServer.title')}</div>
          <div className="font-semibold mt-1">{devServer.enabled ? String(devServer.mode || 'on') : t('devDashboard.devServer.disabled')}</div>
        </div>
        <div className="rounded-lg border border-slate-700 px-3 py-2">
          <div className="text-[10px] uppercase tracking-wide text-slate-400">{t('devDashboard.roadmap.overallStatus')}</div>
          <div className="font-semibold text-slate-200 mt-1">{String(roadmap.overall_status || 'unknown')}</div>
        </div>
        <div className="rounded-lg border border-slate-700 px-3 py-2">
          <div className="text-[10px] uppercase tracking-wide text-slate-400">{t('devDashboard.controlCenter.releaseGate')}</div>
          <div className="font-semibold text-slate-200 mt-1">{String(runtime.release_gate_status || 'unknown')}</div>
        </div>
      </div>

      {blockers.length > 0 ? (
        <div className="mt-3 rounded-lg border border-red-700/50 bg-red-950/30 p-3" data-testid="control-center-blockers">
          <div className="flex items-center gap-2 text-sm font-semibold text-red-200">
            <AlertTriangle size={14} aria-hidden />
            {t('devDashboard.controlCenter.blockers')}
          </div>
          <ul className="mt-2 space-y-1 text-xs text-red-100/90">
            {blockers.slice(0, 6).map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {recommended ? (
        <div className="mt-3 rounded-lg border border-violet-700/40 bg-violet-950/20 p-3" data-testid="control-center-next-prompt">
          <div className="flex items-center gap-2 text-sm font-semibold text-violet-100">
            <CircleDot size={14} aria-hidden />
            {t('devDashboard.controlCenter.nextStep')}
          </div>
          <p className="text-xs text-slate-200 mt-1">{String(recommended.title || recommended.id || '—')}</p>
        </div>
      ) : null}

      {(summary?.warnings?.length || 0) > 0 ? (
        <ul className="mt-3 space-y-1 text-[11px] text-amber-200/90" data-testid="control-center-warnings">
          {(summary?.warnings || []).slice(0, 5).map((w) => (
            <li key={w} className="flex items-start gap-1">
              <AlertTriangle size={10} className="mt-0.5 shrink-0" aria-hidden />
              {w}
            </li>
          ))}
        </ul>
      ) : summary && apiReachable ? (
        <p className="mt-3 text-[11px] text-emerald-300/80 flex items-center gap-1">
          <CheckCircle2 size={12} aria-hidden />
          {t('devDashboard.controlCenter.summaryOk')}
        </p>
      ) : null}
    </section>
  )
}
