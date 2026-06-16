import React, { useCallback, useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ClipboardCopy, Download, Pause, Play, RefreshCw } from 'lucide-react'
import { fetchApi } from '../../api'

type LogFilter = 'important' | 'errors' | 'summary' | 'all'

type LogEvent = {
  type?: string
  line_no?: number
  text?: string
  detail?: string | null
}

type LogsResponse = {
  filter?: LogFilter
  log_file?: string
  total_lines?: number
  file_size_bytes?: number | null
  last_modified?: string | null
  lines?: string[]
  events?: LogEvent[]
  last_error?: string | null
  last_lb_exit?: string | null
  build_in_progress?: boolean
  skipped_stages?: string[]
  returned_lines?: number
}

const FILTERS: LogFilter[] = ['important', 'errors', 'summary', 'all']

function formatBytes(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) return '—'
  if (value < 1024) return `${value} B`
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KiB`
  return `${(value / (1024 * 1024)).toFixed(1)} MiB`
}

function eventTone(type: string | undefined): string {
  if (!type) return 'text-slate-300'
  if (type.includes('error') || type.includes('gap') || type === 'validator_gap') return 'text-rose-200'
  if (type === 'validator_ok' || type === 'lb_exit') return 'text-emerald-200'
  if (type === 'stage_skipped' || type === 'chroot_stale') return 'text-amber-200'
  return 'text-slate-200'
}

export function RescueBuildLogPanel({ refreshSec = 12 }: { refreshSec?: number }) {
  const { t } = useTranslation()
  const [filter, setFilter] = useState<LogFilter>('important')
  const [data, setData] = useState<LogsResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [liveFollow, setLiveFollow] = useState(true)
  const [copyState, setCopyState] = useState<string | null>(null)
  const scrollRef = useRef<HTMLPreElement>(null)

  const loadLogs = useCallback(async () => {
    try {
      setBusy(true)
      setError(null)
      const tail = filter === 'all' ? 2000 : 800
      const res = await fetchApi(
        `/api/dev-dashboard/rescue-iso/logs?filter=${encodeURIComponent(filter)}&tail=${tail}`,
      )
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      setData((await res.json()) as LogsResponse)
    } catch {
      setError('fetch_failed')
    } finally {
      setBusy(false)
    }
  }, [filter])

  useEffect(() => {
    void loadLogs()
  }, [loadLogs])

  useEffect(() => {
    const intervalMs = data?.build_in_progress && liveFollow ? 3000 : Math.max(5, refreshSec) * 1000
    const id = window.setInterval(() => void loadLogs(), intervalMs)
    return () => window.clearInterval(id)
  }, [data?.build_in_progress, liveFollow, loadLogs, refreshSec])

  useEffect(() => {
    if (!liveFollow || filter === 'summary') return
    const node = scrollRef.current
    if (node) {
      node.scrollTop = node.scrollHeight
    }
  }, [data?.lines, filter, liveFollow])

  const downloadFullLog = useCallback(async () => {
    try {
      setBusy(true)
      const res = await fetchApi('/api/dev-dashboard/rescue-iso/logs/download')
      if (!res.ok) return
      const body = (await res.json()) as { content?: string; log_file?: string }
      const blob = new Blob([body.content || ''], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = 'setuphelfer-rescue-iso-build-latest.log'
      anchor.click()
      URL.revokeObjectURL(url)
    } finally {
      setBusy(false)
    }
  }, [])

  const copyVisible = useCallback(async () => {
    const text =
      filter === 'summary'
        ? (data?.events || []).map((e) => `[${e.type}] ${e.text || ''}`).join('\n')
        : (data?.lines || []).join('\n')
    if (!text || !navigator.clipboard) return
    try {
      await navigator.clipboard.writeText(text)
      setCopyState('copied')
      window.setTimeout(() => setCopyState(null), 1600)
    } catch {
      setCopyState('failed')
      window.setTimeout(() => setCopyState(null), 1600)
    }
  }, [data?.events, data?.lines, filter])

  const buttonClass =
    'rounded-md border border-slate-700 bg-slate-900/70 px-2.5 py-1.5 text-xs text-slate-100 hover:border-slate-500 disabled:opacity-50 disabled:cursor-not-allowed'
  const filterActive = 'border-cyan-600 bg-cyan-950/40 text-cyan-100'
  const filterIdle = 'border-slate-700 bg-slate-900/70 text-slate-300'

  return (
    <div className="rounded-lg border border-slate-700/70 bg-slate-950/30 p-3 space-y-3" data-testid="rescue-build-log-panel">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <p className="text-xs font-semibold text-slate-100">{t('devDashboard.rescueIso.buildLogTitle')}</p>
          <p className="text-[10px] text-slate-400 mt-0.5">{t('devDashboard.rescueIso.buildLogSubtitle')}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className={buttonClass} onClick={() => void loadLogs()} disabled={busy}>
            <RefreshCw size={12} className={busy ? 'inline animate-spin mr-1' : 'inline mr-1'} />
            {t('devDashboard.rescueIso.buildLogRefresh')}
          </button>
          <button
            type="button"
            className={buttonClass}
            onClick={() => setLiveFollow((v) => !v)}
            title={t('devDashboard.rescueIso.buildLogLiveFollow')}
          >
            {liveFollow ? <Pause size={12} className="inline mr-1" /> : <Play size={12} className="inline mr-1" />}
            {liveFollow ? t('devDashboard.rescueIso.buildLogLiveOn') : t('devDashboard.rescueIso.buildLogLiveOff')}
          </button>
          <button type="button" className={buttonClass} onClick={() => void copyVisible()} disabled={busy}>
            <ClipboardCopy size={12} className="inline mr-1" />
            {copyState === 'copied'
              ? t('devDashboard.rescueIso.copied')
              : copyState === 'failed'
                ? t('devDashboard.rescueIso.copyFailed')
                : t('devDashboard.rescueIso.buildLogCopyVisible')}
          </button>
          <button type="button" className={buttonClass} onClick={() => void downloadFullLog()} disabled={busy}>
            <Download size={12} className="inline mr-1" />
            {t('devDashboard.rescueIso.buildLogDownload')}
          </button>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5" data-testid="rescue-build-log-filters">
        {FILTERS.map((item) => (
          <button
            key={item}
            type="button"
            className={`rounded-md border px-2 py-1 text-[11px] ${filter === item ? filterActive : filterIdle}`}
            onClick={() => setFilter(item)}
          >
            {t(`devDashboard.rescueIso.buildLogFilter.${item}`)}
          </button>
        ))}
      </div>

      <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-2 text-[10px] font-mono text-slate-300">
        <div>
          <span className="text-slate-500">{t('devDashboard.rescueIso.buildLogLbExit')}: </span>
          {data?.last_lb_exit ?? '—'}
        </div>
        <div>
          <span className="text-slate-500">{t('devDashboard.rescueIso.buildLogLines')}: </span>
          {data?.total_lines ?? 0}
        </div>
        <div>
          <span className="text-slate-500">{t('devDashboard.rescueIso.buildLogSize')}: </span>
          {formatBytes(data?.file_size_bytes)}
        </div>
        <div>
          <span className="text-slate-500">{t('devDashboard.rescueIso.buildLogStatus')}: </span>
          {data?.build_in_progress
            ? t('devDashboard.rescueIso.buildLogRunning')
            : t('devDashboard.rescueIso.buildLogIdle')}
        </div>
      </div>

      {data?.skipped_stages?.length ? (
        <div className="rounded border border-amber-800/40 bg-amber-950/20 px-2 py-1.5 text-[10px] text-amber-100">
          <span className="font-semibold">{t('devDashboard.rescueIso.buildLogSkippedWarning')}: </span>
          {data.skipped_stages.join(', ')}
        </div>
      ) : null}

      {data?.last_error ? (
        <div className="rounded border border-rose-800/40 bg-rose-950/20 px-2 py-1.5 text-[10px] font-mono text-rose-100 whitespace-pre-wrap">
          {data.last_error}
        </div>
      ) : null}

      {error ? <p className="text-xs text-rose-200">{error}</p> : null}

      {filter === 'summary' ? (
        <div className="max-h-[28rem] overflow-y-auto space-y-1.5" data-testid="rescue-build-log-events">
          {(data?.events || []).length ? (
            data?.events?.map((event, index) => (
              <div
                key={`${event.line_no}-${event.type}-${index}`}
                className="rounded border border-slate-800 bg-slate-950/60 px-2 py-1 text-[10px] font-mono"
              >
                <div className={`font-semibold ${eventTone(event.type)}`}>
                  {event.type}
                  {event.detail ? ` · ${event.detail}` : ''}
                  {event.line_no ? ` · L${event.line_no}` : ''}
                </div>
                <div className="text-slate-300 whitespace-pre-wrap break-all">{event.text}</div>
              </div>
            ))
          ) : (
            <p className="text-xs text-slate-400">{t('devDashboard.rescueIso.noLogs')}</p>
          )}
        </div>
      ) : (
        <pre
          ref={scrollRef}
          className="max-h-[28rem] min-h-[12rem] overflow-auto rounded-md border border-slate-800 bg-slate-950/70 p-3 text-[10px] text-slate-200 whitespace-pre-wrap font-mono"
          data-testid="rescue-build-log-lines"
        >
          {data?.lines?.length ? data.lines.join('\n') : t('devDashboard.rescueIso.noLogs')}
        </pre>
      )}

      {data?.log_file ? (
        <p className="text-[10px] text-slate-500 break-all font-mono">
          {t('devDashboard.rescueIso.buildLogFile')}: {data.log_file}
        </p>
      ) : null}
    </div>
  )
}
