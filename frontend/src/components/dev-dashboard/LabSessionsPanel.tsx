import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Activity, Copy, RefreshCw } from 'lucide-react'
import {
  fetchFleetSessionSummary,
  fetchFleetSessions,
  type FleetSession,
  type FleetSessionSummary,
} from '../../api/fleetSessionsApi'
import {
  copyTextToClipboard,
  fetchEvidenceIndex,
  fetchQemuSmokeDiagnosticExport,
  fetchQemuSmokeMarkdownReport,
  type DiagnosticExport,
} from '../../api/devDiagnosticsApi'
import {
  devDiagnosticsUiEnabled,
  fleetSessionsUiEnabled,
} from '../../config/buildProfile'

const TERMINAL = new Set(['timeout', 'failed', 'success', 'cancelled'])
const RUNNING = new Set([
  'starting',
  'proxy_starting',
  'proxy_ready',
  'qemu_starting',
  'booting',
  'autopilot_waiting',
  'guest_report_seen',
  'serial_active',
  'serial_empty',
  'timeout_warning',
])

function sessionLedClass(session: FleetSession): string {
  const st = session.status || 'unknown'
  const sev = session.severity || 'info'
  if (st === 'success') return 'bg-emerald-500'
  if (st === 'timeout' || st === 'failed' || sev === 'error') return 'bg-red-500'
  if (st === 'serial_empty' || st === 'timeout_warning' || sev === 'warning') return 'bg-amber-400'
  if (RUNNING.has(st) && (session.heartbeat?.healthy ?? true)) {
    return 'bg-sky-400 animate-pulse'
  }
  if (TERMINAL.has(st)) return 'bg-slate-500'
  return 'bg-slate-600'
}

function formatAge(seconds: number | undefined): string {
  if (seconds == null) return '—'
  if (seconds < 60) return `${seconds}s`
  return `${Math.floor(seconds / 60)}m`
}

export function LabSessionsPanel({ refreshSec = 15 }: { refreshSec?: number }) {
  const { t } = useTranslation()
  const [sessions, setSessions] = useState<FleetSession[]>([])
  const [summary, setSummary] = useState<FleetSessionSummary | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [diagExport, setDiagExport] = useState<DiagnosticExport | null>(null)
  const [diagSummary, setDiagSummary] = useState<string | null>(null)
  const [diagMarkdown, setDiagMarkdown] = useState<string | null>(null)
  const [evidencePaths, setEvidencePaths] = useState<string[]>([])
  const [copyFallback, setCopyFallback] = useState<string | null>(null)
  const [copyNotice, setCopyNotice] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    setLoading(true)
    try {
      const [s, sum] = await Promise.all([fetchFleetSessions(true), fetchFleetSessionSummary()])
      setSessions(s)
      setSummary(sum)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void loadData()
    const id = window.setInterval(() => void loadData(), refreshSec * 1000)
    return () => window.clearInterval(id)
  }, [loadData, refreshSec])

  const active = sessions.filter((s) => !TERMINAL.has(s.status || ''))

  const loadDiagnostics = useCallback(async (session: FleetSession) => {
    const runId = session.run_id
    if (!runId) {
      setDiagExport(null)
      setDiagSummary(null)
      setDiagMarkdown(null)
      setEvidencePaths([])
      return
    }
    const [expRes, md, evIdx] = await Promise.all([
      fetchQemuSmokeDiagnosticExport(runId),
      fetchQemuSmokeMarkdownReport(runId),
      fetchEvidenceIndex(runId),
    ])
    setDiagExport(expRes?.export ?? null)
    setDiagSummary(expRes?.summary_text ?? null)
    setDiagMarkdown(md)
    const paths = (evIdx?.index?.paths ?? [])
      .filter((p) => p.exists && p.path)
      .map((p) => p.path as string)
    setEvidencePaths(paths)
  }, [])

  const handleExpand = (session: FleetSession, sid: string, isOpen: boolean) => {
    if (isOpen) {
      setExpanded(null)
      setDiagExport(null)
      setCopyFallback(null)
      return
    }
    setExpanded(sid)
    setCopyFallback(null)
    setCopyNotice(null)
    void loadDiagnostics(session)
  }

  const doCopy = async (text: string, okKey: string) => {
    const ok = await copyTextToClipboard(text)
    if (ok) {
      setCopyFallback(null)
      setCopyNotice(t(okKey))
      window.setTimeout(() => setCopyNotice(null), 2500)
    } else {
      setCopyFallback(text)
      setCopyNotice(t('devDashboard.labSessions.copyFallback'))
    }
  }

  if (!fleetSessionsUiEnabled) {
    return null
  }

  return (
    <section
      className="rounded-xl border border-slate-700 bg-slate-900/50 p-4 mb-4"
      data-testid="lab-sessions-panel"
    >
      <div className="flex items-start justify-between gap-3 mb-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Activity className="text-violet-400" size={18} aria-hidden />
            {t('devDashboard.labSessions.title')}
          </h2>
          <p className="text-xs text-slate-400 mt-1">{t('devDashboard.labSessions.subtitle')}</p>
        </div>
        <button
          type="button"
          className="btn-secondary inline-flex items-center gap-1 text-xs"
          onClick={() => void loadData()}
          disabled={loading}
          data-testid="lab-sessions-refresh"
        >
          <RefreshCw className={loading ? 'animate-spin' : ''} size={14} />
          {t('backup.ui.refresh')}
        </button>
      </div>

      <p className="text-[11px] text-slate-500 mb-3" data-testid="lab-sessions-scope-hint">
        {t('devDashboard.labSessions.scopeHint')}
      </p>
      <p
        className="text-[11px] text-amber-500/90 mb-3 border border-amber-700/40 rounded px-2 py-1"
        data-testid="lab-sessions-sharing-warning"
      >
        {t('devDashboard.labSessions.sharingWarning')}
      </p>
      {copyNotice ? (
        <p className="text-xs text-emerald-400 mb-2" data-testid="lab-sessions-copy-notice">
          {copyNotice}
        </p>
      ) : null}

      <div className="grid sm:grid-cols-4 gap-2 mb-4 text-xs" data-testid="lab-sessions-summary-grid">
        <div className="rounded border border-slate-700 px-2 py-1.5">
          <span className="text-slate-500">{t('devDashboard.labSessions.active')}</span>
          <div className="text-slate-200">{summary?.active_count ?? active.length}</div>
        </div>
        <div className="rounded border border-slate-700 px-2 py-1.5">
          <span className="text-slate-500">{t('devDashboard.labSessions.finished')}</span>
          <div className="text-slate-200">{summary?.finished_count ?? 0}</div>
        </div>
        <div className="rounded border border-slate-700 px-2 py-1.5">
          <span className="text-slate-500">{t('devDashboard.labSessions.warnings')}</span>
          <div className="text-amber-300">{summary?.warning_count ?? 0}</div>
        </div>
        <div className="rounded border border-slate-700 px-2 py-1.5">
          <span className="text-slate-500">{t('devDashboard.labSessions.errors')}</span>
          <div className="text-red-300">{summary?.error_count ?? 0}</div>
        </div>
      </div>

      {sessions.length === 0 ? (
        <p className="text-xs text-slate-400" data-testid="lab-sessions-empty">
          {t('devDashboard.labSessions.empty')}
        </p>
      ) : (
        <ul className="space-y-2" data-testid="lab-sessions-list">
          {sessions.map((session) => {
            const sid = session.session_id || session.run_id || ''
            const isOpen = expanded === sid
            const kvm = session.host?.kvm_enabled
              ? t('devDashboard.labSessions.kvmEnabled')
              : session.host?.has_kvm
                ? t('devDashboard.labSessions.kvmAvailable')
                : t('devDashboard.labSessions.kvmTcg')
            const serialLabel =
              (session.serial?.size_bytes ?? 0) > 0
                ? t('devDashboard.labSessions.serialActive')
                : session.serial?.exists
                  ? t('devDashboard.labSessions.serialEmpty')
                  : t('devDashboard.labSessions.serialMissing')
            const guestLabel = session.guest?.report_seen
              ? t('devDashboard.labSessions.guestReportSeen')
              : t('devDashboard.labSessions.guestReportMissing')
            return (
              <li
                key={sid}
                className="rounded-lg border border-slate-700 px-3 py-2 text-sm"
                data-testid={`lab-session-${sid}`}
              >
                <button
                  type="button"
                  className="w-full text-left"
                  onClick={() => handleExpand(session, sid, isOpen)}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`w-2.5 h-2.5 rounded-full shrink-0 ${sessionLedClass(session)}`}
                      aria-hidden
                    />
                    <span className="font-medium text-white">{session.label || sid}</span>
                    <span className="text-[10px] uppercase tracking-wide text-slate-400">
                      {session.status}
                    </span>
                    <span className="text-xs text-slate-500 ml-auto">
                      {t('devDashboard.labSessions.heartbeatAge')}:{' '}
                      {formatAge(session.heartbeat?.age_seconds)}
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1 grid sm:grid-cols-2 lg:grid-cols-4 gap-1">
                    <span>
                      {t('devDashboard.labSessions.runId')}: {session.run_id}
                    </span>
                    <span>{kvm}</span>
                    <span>{serialLabel}</span>
                    <span>{guestLabel}</span>
                  </div>
                </button>
                {isOpen ? (
                  <div className="mt-2 pt-2 border-t border-slate-700 text-xs text-slate-300 space-y-1">
                    {session.qemu?.exit_code != null ? (
                      <p>
                        {t('devDashboard.labSessions.qemuExit')}: {session.qemu.exit_code}
                      </p>
                    ) : null}
                    {(session.findings?.length ?? 0) > 0 ? (
                      <p>
                        {t('devDashboard.labSessions.findings')}: {session.findings?.join(', ')}
                      </p>
                    ) : null}
                    {(session.evidence_paths?.length ?? 0) > 0 ? (
                      <p className="font-mono break-all">
                        {t('devDashboard.labSessions.evidence')}: {session.evidence_paths?.join(', ')}
                      </p>
                    ) : null}
                    {session.run_id && devDiagnosticsUiEnabled ? (
                      <div className="mt-2 space-y-2" data-testid="lab-session-diagnostics">
                        {diagExport ? (
                          <div className="rounded border border-slate-600 p-2 text-[11px] space-y-1">
                            <p>
                              <span className="text-slate-500">
                                {t('devDashboard.labSessions.diagClassification')}:
                              </span>{' '}
                              <span className="text-amber-300 font-mono">
                                {diagExport.classification?.primary ?? '—'}
                              </span>
                            </p>
                            <p>
                              {t('devDashboard.labSessions.serialSize')}:{' '}
                              <span
                                className={
                                  (diagExport.qemu_smoke?.serial_size_bytes as number) === 0
                                    ? 'text-red-400'
                                    : 'text-slate-200'
                                }
                              >
                                {String(diagExport.qemu_smoke?.serial_size_bytes ?? '—')}
                              </span>
                            </p>
                            <p>
                              report_new:{' '}
                              <span
                                className={
                                  diagExport.devserver_ingest?.report_new
                                    ? 'text-emerald-400'
                                    : 'text-red-400'
                                }
                              >
                                {String(diagExport.devserver_ingest?.report_new ?? false)}
                              </span>
                              {' · '}
                              guest_found:{' '}
                              <span
                                className={
                                  diagExport.devserver_ingest?.guest_found
                                    ? 'text-emerald-400'
                                    : 'text-red-400'
                                }
                              >
                                {String(diagExport.devserver_ingest?.guest_found ?? false)}
                              </span>
                            </p>
                            {diagExport.qemu_smoke?.proxy_bind === '0.0.0.0' ? (
                              <p className="text-amber-400">
                                {t('devDashboard.labSessions.proxyLabWarning')}
                              </p>
                            ) : null}
                          </div>
                        ) : (
                          <p className="text-slate-500">
                            {t('devDashboard.labSessions.diagLoading')}
                          </p>
                        )}
                        <div className="flex flex-wrap gap-1">
                          <button
                            type="button"
                            className="btn-secondary text-[10px] inline-flex items-center gap-1"
                            disabled={!diagSummary}
                            onClick={(e) => {
                              e.stopPropagation()
                              if (diagSummary) void doCopy(diagSummary, 'devDashboard.labSessions.copyOk')
                            }}
                            data-testid="lab-copy-summary"
                          >
                            <Copy size={12} />
                            {t('devDashboard.labSessions.copySummary')}
                          </button>
                          <button
                            type="button"
                            className="btn-secondary text-[10px] inline-flex items-center gap-1"
                            disabled={!diagExport}
                            onClick={(e) => {
                              e.stopPropagation()
                              if (diagExport)
                                void doCopy(
                                  JSON.stringify(diagExport, null, 2),
                                  'devDashboard.labSessions.copyOk'
                                )
                            }}
                            data-testid="lab-copy-json"
                          >
                            <Copy size={12} />
                            {t('devDashboard.labSessions.copyJson')}
                          </button>
                          <button
                            type="button"
                            className="btn-secondary text-[10px] inline-flex items-center gap-1"
                            disabled={!diagMarkdown}
                            onClick={(e) => {
                              e.stopPropagation()
                              if (diagMarkdown)
                                void doCopy(diagMarkdown, 'devDashboard.labSessions.copyOk')
                            }}
                            data-testid="lab-copy-markdown"
                          >
                            <Copy size={12} />
                            {t('devDashboard.labSessions.copyMarkdown')}
                          </button>
                        </div>
                        {evidencePaths.length > 0 ? (
                          <details className="text-[10px]">
                            <summary className="cursor-pointer text-slate-400">
                              {t('devDashboard.labSessions.showEvidencePaths')}
                            </summary>
                            <ul className="mt-1 font-mono break-all text-slate-500">
                              {evidencePaths.map((p) => (
                                <li key={p}>{p}</li>
                              ))}
                            </ul>
                          </details>
                        ) : null}
                        {copyFallback ? (
                          <textarea
                            className="w-full h-24 text-[10px] font-mono bg-slate-950 border border-slate-600 rounded p-1"
                            readOnly
                            value={copyFallback}
                            data-testid="lab-copy-fallback-textarea"
                            onClick={(e) => e.stopPropagation()}
                          />
                        ) : null}
                      </div>
                    ) : null}
                    <p className="text-slate-500">{t('devDashboard.labSessions.hostSessionNote')}</p>
                  </div>
                ) : null}
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
