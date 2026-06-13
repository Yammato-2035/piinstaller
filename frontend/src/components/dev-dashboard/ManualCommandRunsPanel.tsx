import React, { useCallback, useEffect, useState } from 'react'
import { fetchApi } from '../../api'
import { toneClass } from '../../pages/devDashboardFilters'
import { dashboardLegacyToneFromInput } from '../../viewmodels/statusViewModel'
import type { CockpitPanelProps } from './types'

type CommandRow = {
  command?: string
  purpose?: string
  exit_code?: number | null
  safety_class?: string
  stdout_excerpt?: string
  stderr_excerpt?: string
  full_log_path?: string | null
  excerpt_only?: boolean
  notes?: string
}

type RunRow = {
  run_id?: string
  created_at?: string
  operator?: string
  branch?: string
  head?: string
  source_file?: string
  excerpt_only_warning?: boolean
  has_forbidden_commands?: boolean
  commands?: CommandRow[]
  summary?: { status?: string; reason?: string }
  not_executed?: string[]
}

type Payload = {
  status?: string
  runs?: RunRow[]
  run_count?: number
  overall_status?: string
  excerpt_only_detected?: boolean
  warnings?: string[]
  runs_dir?: string
  read_only?: boolean
  execution_allowed?: boolean
}

function safetyTone(safety: string): string {
  const raw = String(safety || 'read_only').trim().toLowerCase()
  return dashboardLegacyToneFromInput(raw || 'read_only')
}

export function ManualCommandRunsPanel({ t }: CockpitPanelProps) {
  const [data, setData] = useState<Payload | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetchApi('/api/dev-dashboard/manual-command-runs')
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        setData(null)
        return
      }
      setData((await res.json()) as Payload)
    } catch {
      setError('fetch_failed')
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const [showAll, setShowAll] = useState(false)
  const allRuns = data?.runs ?? []
  const displayLimit = showAll ? 20 : 5
  const runs = allRuns.slice(0, displayLimit)
  const overall = String(data?.overall_status || 'gray')

  return (
    <section
      className="rounded-xl border border-slate-600 bg-slate-900/50 p-4"
      data-testid="dev-dashboard-manual-command-runs-panel"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-white">{t('devDashboard.manualCommandRuns.title')}</h2>
          <p className="text-xs text-slate-400 mt-1">{t('devDashboard.manualCommandRuns.subtitle')}</p>
        </div>
        <button type="button" className="btn-secondary text-xs" onClick={() => void load()} disabled={loading}>
          {t('backup.ui.refresh')}
        </button>
      </div>

      <p className="text-[11px] text-amber-200/90 mt-2 border border-amber-700/40 bg-amber-950/20 rounded px-2 py-1">
        {t('devDashboard.manualCommandRuns.noExecute')}
      </p>

      {data?.excerpt_only_detected ? (
        <p className="text-xs text-amber-200 mt-2" data-testid="manual-command-runs-excerpt-warning">
          {t('devDashboard.manualCommandRuns.excerptWarning')}
        </p>
      ) : null}

      {loading ? <p className="text-sm text-slate-400 mt-3">…</p> : null}
      {error ? <p className="text-sm text-red-300 mt-3">{error}</p> : null}

      {!loading && !error ? (
        <>
          <p className={`text-xs mt-2 inline-block rounded px-2 py-0.5 border ${toneClass(overall)}`}>
            {t('devDashboard.manualCommandRuns.overall')}: {overall} ({runs.length}/{allRuns.length})
          </p>
          {allRuns.length > 5 ? (
            <button
              type="button"
              className="text-[11px] text-violet-300 hover:underline mt-1"
              onClick={() => setShowAll((v) => !v)}
            >
              {showAll ? t('devDashboard.recentEvidence.showFive') : t('devDashboard.recentEvidence.showMore')}
            </button>
          ) : null}
          {data?.runs_dir ? (
            <p className="text-[11px] text-slate-500 mt-1 font-mono">{data.runs_dir}</p>
          ) : null}
          {runs.length === 0 ? (
            <p className="text-sm text-slate-400 mt-3">{t('devDashboard.manualCommandRuns.empty')}</p>
          ) : (
            <ul className="mt-3 space-y-3">
              {runs.map((run) => (
                <li
                  key={String(run.run_id || run.source_file)}
                  className={`rounded-lg border p-3 text-xs ${toneClass(String(run.summary?.status || 'gray'))}`}
                  data-testid={`manual-command-run-${run.run_id}`}
                >
                  <div className="font-semibold text-white">{run.run_id}</div>
                  <div className="text-slate-400 mt-0.5">
                    {run.created_at} · {run.operator} · {run.branch}@{run.head}
                  </div>
                  {run.excerpt_only_warning ? (
                    <p className="text-amber-200 mt-1">{t('devDashboard.manualCommandRuns.runExcerptOnly')}</p>
                  ) : null}
                  <ul className="mt-2 space-y-1">
                    {(run.commands || []).map((cmd, idx) => (
                      <li
                        key={`${run.run_id}-cmd-${idx}`}
                        className={`rounded border px-2 py-1 ${toneClass(safetyTone(String(cmd.safety_class || 'read_only')))}`}
                      >
                        <span className="font-mono text-[11px]">{cmd.command}</span>
                        <span className="text-slate-400"> — {cmd.purpose}</span>
                        <span className="ml-1">exit={String(cmd.exit_code ?? '—')}</span>
                        <span className="ml-1 uppercase text-[10px]">{cmd.safety_class}</span>
                        {cmd.excerpt_only ? (
                          <span className="ml-1 text-amber-300">({t('devDashboard.manualCommandRuns.excerptOnly')})</span>
                        ) : null}
                        {cmd.full_log_path ? (
                          <div className="font-mono text-[10px] text-slate-500 mt-0.5">{cmd.full_log_path}</div>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          )}
        </>
      ) : null}
    </section>
  )
}
