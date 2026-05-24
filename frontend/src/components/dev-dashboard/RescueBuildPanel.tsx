import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronDown, ChevronRight, HardDriveDownload, ShieldOff } from 'lucide-react'
import { fetchApi } from '../../api'
import { toneClass } from '../../pages/devDashboardFilters'

type GateSlice = {
  status?: string
  summary?: string
  passed?: boolean
  exit_code?: number
  last_error?: string
}

type RescueBuildPayload = {
  status?: string
  summary?: string
  code?: string
  runtime_gate?: GateSlice
  toolcheck?: GateSlice & { missing?: string[] }
  temp_runtime_bundle?: GateSlice & { files_count?: number }
  live_build_tree?: GateSlice
  controlled_iso_build?: GateSlice & { build_status?: string; last_error?: string }
  usb_write_gate?: GateSlice
  live_os_validation?: GateSlice
  latest_logs?: { lines?: string[]; last_error?: string; sources?: string[] }
  latest_artifacts?: { path?: string; sha256?: string; size_bytes?: number }
  next_operator_action?: { action?: string; priority?: string; blocked?: boolean }
}

function GateRow({ label, gate, testId }: { label: string; gate?: GateSlice; testId: string }) {
  const tone = String(gate?.status || 'gray')
  return (
    <div className={`rounded-lg border px-3 py-2 text-xs ${toneClass(tone)}`} data-testid={testId}>
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-white">{label}</span>
        <span className="uppercase tracking-wide opacity-80">{tone}</span>
      </div>
      {gate?.summary ? <p className="mt-1 text-slate-300">{gate.summary}</p> : null}
    </div>
  )
}

export function RescueBuildPanel({ refreshSec = 12 }: { refreshSec?: number }) {
  const { t } = useTranslation()
  const [data, setData] = useState<RescueBuildPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [logsOpen, setLogsOpen] = useState(false)

  const poll = useCallback(async () => {
    try {
      setError(null)
      const res = await fetchApi('/api/dev-dashboard/rescue-build/status')
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      const body = (await res.json()) as RescueBuildPayload
      setData(body)
    } catch {
      setError('fetch_failed')
    }
  }, [])

  useEffect(() => {
    void poll()
    const id = window.setInterval(() => void poll(), Math.max(5, refreshSec) * 1000)
    return () => window.clearInterval(id)
  }, [poll, refreshSec])

  const overall = String(data?.status || 'gray')
  const iso = data?.latest_artifacts
  const logs = data?.latest_logs?.lines || []
  const lastErr =
    data?.controlled_iso_build?.last_error || data?.latest_logs?.last_error || data?.summary

  return (
    <section
      className={`rounded-xl border p-4 space-y-3 ${toneClass(overall)}`}
      data-testid="rescue-build-panel"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <HardDriveDownload size={18} className="shrink-0" />
            {t('devDashboard.rescueBuild.title')}
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">{t('devDashboard.rescueBuild.subtitle')}</p>
        </div>
        <span className="text-xs uppercase tracking-wide font-mono">{overall}</span>
      </div>

      {error ? <p className="text-xs text-rose-200">{error}</p> : null}

      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
        <GateRow
          label={t('devDashboard.rescueBuild.runtimeGate')}
          gate={data?.runtime_gate}
          testId="rescue-build-gate-runtime"
        />
        <GateRow
          label={t('devDashboard.rescueBuild.toolcheck')}
          gate={data?.toolcheck}
          testId="rescue-build-gate-toolcheck"
        />
        <GateRow
          label={t('devDashboard.rescueBuild.tempBundle')}
          gate={data?.temp_runtime_bundle}
          testId="rescue-build-gate-temp-bundle"
        />
        <GateRow
          label={t('devDashboard.rescueBuild.liveBuildTree')}
          gate={data?.live_build_tree}
          testId="rescue-build-gate-live-tree"
        />
        <GateRow
          label={t('devDashboard.rescueBuild.isoBuild')}
          gate={data?.controlled_iso_build}
          testId="rescue-build-gate-iso"
        />
        <GateRow
          label={t('devDashboard.rescueBuild.liveOsTest')}
          gate={data?.live_os_validation}
          testId="rescue-build-gate-live-os"
        />
      </div>

      <div
        className="rounded-lg border border-red-800/50 bg-red-950/30 px-3 py-2 flex items-start gap-2"
        data-testid="rescue-build-usb-blocked"
      >
        <ShieldOff size={16} className="text-red-300 shrink-0 mt-0.5" />
        <div className="text-xs">
          <p className="font-semibold text-red-100">{t('devDashboard.rescueBuild.usbWriteBlocked')}</p>
          <p className="text-red-200/90 mt-0.5">
            {data?.usb_write_gate?.summary || t('devDashboard.rescueBuild.writeActionsLocked')}
          </p>
        </div>
      </div>

      {lastErr ? (
        <div
          className="rounded-lg border border-amber-800/40 bg-amber-950/20 px-3 py-2"
          data-testid="rescue-build-last-error"
        >
          <p className="text-xs font-semibold text-amber-100">{t('devDashboard.rescueBuild.lastBuildError')}</p>
          <pre className="text-[10px] text-amber-100/90 mt-1 whitespace-pre-wrap font-mono">{lastErr}</pre>
        </div>
      ) : null}

      <div className="text-xs space-y-1" data-testid="rescue-build-artifacts">
        <p className="font-medium text-slate-200">{t('devDashboard.rescueBuild.artifacts')}</p>
        {iso?.path ? (
          <div className="font-mono text-slate-300 break-all space-y-0.5">
            <div>{iso.path}</div>
            {iso.size_bytes != null ? <div>{(iso.size_bytes / (1024 * 1024)).toFixed(1)} MiB</div> : null}
            {iso.sha256 ? <div className="text-[10px]">SHA256: {iso.sha256}</div> : null}
          </div>
        ) : (
          <p className="text-slate-400">{t('devDashboard.rescueBuild.noIsoFound')}</p>
        )}
      </div>

      {data?.next_operator_action?.action ? (
        <div className="rounded-lg border border-violet-800/40 bg-violet-950/20 px-3 py-2" data-testid="rescue-build-next-action">
          <p className="text-xs font-semibold text-violet-100">{t('devDashboard.rescueBuild.nextOperatorAction')}</p>
          <p className="text-xs text-violet-100/90 mt-1">{data.next_operator_action.action}</p>
        </div>
      ) : null}

      <div>
        <button
          type="button"
          className="flex items-center gap-1 text-xs text-slate-300 hover:text-white"
          onClick={() => setLogsOpen((v) => !v)}
          data-testid="rescue-build-logs-toggle"
        >
          {logsOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          {t('devDashboard.rescueBuild.logTail')} ({logs.length})
        </button>
        {logsOpen ? (
          <pre
            className="mt-2 max-h-48 overflow-y-auto text-[10px] font-mono bg-slate-950/60 border border-slate-700 rounded p-2 text-slate-300"
            data-testid="rescue-build-log-lines"
          >
            {logs.length ? logs.join('\n') : t('devDashboard.rescueBuild.noLogs')}
          </pre>
        ) : null}
      </div>

      <p className="text-[10px] text-slate-500">{t('devDashboard.rescueBuild.noFakeGreen')}</p>
    </section>
  )
}
