import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Activity, RefreshCw } from 'lucide-react'
import {
  fetchFleetSessionSummary,
  fetchFleetSessions,
  type FleetSession,
  type FleetSessionSummary,
} from '../../api/fleetSessionsApi'

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
                  onClick={() => setExpanded(isOpen ? null : sid)}
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
