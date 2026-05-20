/**
 * Zeigt laufende systemd-/Helper-Backup-Jobs im Development Control Center (read-only).
 * Daten aus GET /api/backup/jobs + Detail GET /api/backup/jobs/{id}.
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AlertTriangle, HardDrive } from 'lucide-react'
import { fetchApi } from '../../api'

type ProgressOptional = {
  bytes_current?: number
  throughput_mib_s?: number
  running_for_s?: number
  elapsed_seconds?: number
  phase?: string
  compression_method?: string
  compression_engine?: string
  written_human?: string
  estimated_write_rate_human?: string
  current_operation?: string
}

export type CockpitBackupJob = {
  job_id?: string
  status?: string
  type?: string
  code?: string
  backup_dir?: string
  backup_file?: string
  bytes_current?: number
  partial_path?: string
  abort_reason?: string
  diagnosis_id?: string
  tar_warning_classification?: string
  fatal_patterns_found?: boolean
  volatile_warning_paths?: string[]
  partial_deleted?: boolean
  final_archive_exists?: boolean
  subprocess_returncode?: number
  phase?: string
  written_bytes?: number
  written_human?: string
  elapsed_seconds?: number
  compression_engine?: string
  compression_threads?: number
  estimated_write_rate_human?: string
  last_status_message?: string
  last_error_code?: string
  notification_status?: string
  progress_optional?: ProgressOptional
  unit_name?: string
}

const PHASE_STEPS = [
  'preflight',
  'archiving',
  'tar_reading',
  'compressing',
  'writing',
  'finalizing',
  'sha256',
  'verify_deep',
  'notification',
  'cleanup',
  'completed',
  'success',
] as const

function formatGiB(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return '—'
  const gib = bytes / (1024 * 1024 * 1024)
  return `${gib.toFixed(2)} GiB`
}

function formatEta(seconds: number | undefined): string {
  if (seconds === undefined || !Number.isFinite(seconds) || seconds < 0) return '—'
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = Math.floor(seconds % 60)
  return `${h}h ${m}m ${s}s`
}

function statusTone(status: string | undefined): string {
  const s = (status || '').toLowerCase()
  if (s === 'success') return 'text-emerald-300'
  if (s === 'error' || s === 'failed') return 'text-rose-300'
  if (s === 'running' || s === 'queued') return 'text-amber-200'
  return 'text-slate-300'
}

export function CockpitBackupProgressPanel({ refreshSec }: { refreshSec: number }) {
  const { t } = useTranslation()
  const [job, setJob] = useState<CockpitBackupJob | null>(null)
  const [error, setError] = useState<string | null>(null)
  const cancelledRef = useRef(false)
  const lastBytesRef = useRef<{ t: number; b: number } | null>(null)
  const [staleWarning, setStaleWarning] = useState(false)

  const poll = useCallback(async () => {
    try {
      setError(null)
      const listRes = await fetchApi('/api/backup/jobs')
      const listJson = (await listRes.json()) as { status?: string; jobs?: CockpitBackupJob[] }
      if (listJson.status !== 'success' || !Array.isArray(listJson.jobs) || listJson.jobs.length === 0) {
        setJob(null)
        lastBytesRef.current = null
        return
      }
      const first = listJson.jobs[0]
      const jid = String(first?.job_id || '').trim()
      if (!jid) {
        setJob(null)
        return
      }
      const detRes = await fetchApi(`/api/backup/jobs/${encodeURIComponent(jid)}`)
      const detJson = (await detRes.json()) as { status?: string; job?: CockpitBackupJob }
      const j = detJson.status === 'success' && detJson.job ? detJson.job : first
      setJob(j)
      const bytes = j.progress_optional?.bytes_current ?? j.written_bytes ?? j.bytes_current
      if (typeof bytes === 'number' && (j.status === 'running' || j.status === 'queued')) {
        const now = Date.now()
        const prev = lastBytesRef.current
        if (prev && bytes === prev.b && now - prev.t > 5 * 60 * 1000) {
          setStaleWarning(true)
        } else if (!prev || bytes !== prev.b) {
          setStaleWarning(false)
          lastBytesRef.current = { t: now, b: bytes }
        }
      } else {
        lastBytesRef.current = null
        setStaleWarning(false)
      }
    } catch {
      setError(t('devDashboard.governance.backupProgress.fetchError'))
      setJob(null)
    }
  }, [t])

  useEffect(() => {
    cancelledRef.current = false
    void poll()
    const ms = Math.min(Math.max(refreshSec, 3), 60) * 1000
    const id = window.setInterval(() => {
      if (!cancelledRef.current) void poll()
    }, ms)
    return () => {
      cancelledRef.current = true
      window.clearInterval(id)
    }
  }, [poll, refreshSec])

  const bytes = job?.progress_optional?.bytes_current ?? job?.written_bytes ?? job?.bytes_current
  const writtenHuman =
    job?.written_human ?? job?.progress_optional?.written_human ?? (typeof bytes === 'number' ? formatGiB(bytes) : '—')
  const mib = job?.progress_optional?.throughput_mib_s
  const rateHuman =
    job?.estimated_write_rate_human ??
    job?.progress_optional?.estimated_write_rate_human ??
    (typeof mib === 'number' ? `${mib.toFixed(2)} MiB/s` : '—')
  const elapsed = job?.progress_optional?.elapsed_seconds ?? job?.progress_optional?.running_for_s ?? job?.elapsed_seconds
  const phase = job?.phase ?? job?.progress_optional?.phase
  const compressor = job?.compression_engine ?? job?.progress_optional?.compression_engine ?? job?.progress_optional?.compression_method
  const isFailed = (job?.status || '').toLowerCase() === 'error' || (job?.status || '').toLowerCase() === 'failed'
  const isRunning = (job?.status || '').toLowerCase() === 'running' || (job?.status || '').toLowerCase() === 'queued'
  const longGzipWarn =
    isRunning && compressor === 'gzip' && typeof elapsed === 'number' && elapsed > 7200

  const phaseIndex = useMemo(() => {
    const p = (phase || 'archiving').toLowerCase()
    const idx = PHASE_STEPS.indexOf(p as (typeof PHASE_STEPS)[number])
    return idx >= 0 ? idx : 1
  }, [phase])

  return (
    <section
      className={`rounded-xl border p-4 mb-4 ${
        isFailed
          ? 'border-rose-800/60 bg-rose-950/30'
          : 'border-emerald-800/50 bg-emerald-950/25'
      }`}
      data-testid="cockpit-backup-progress"
      aria-live="polite"
    >
      <h2 className="text-sm font-semibold text-emerald-100 flex items-center gap-2 mb-2">
        <HardDrive size={16} className="text-emerald-400 shrink-0" aria-hidden />
        {t('devDashboard.governance.backupProgress.title')}
      </h2>
      <p className="text-[11px] text-emerald-200/70 mb-2">{t('devDashboard.governance.backupProgress.subtitle')}</p>
      <p className="text-[11px] text-amber-200/90 mb-3 border border-amber-800/40 rounded px-2 py-1.5 bg-amber-950/30">
        {t('devDashboard.governance.backupProgress.greenRule')}
      </p>

      {error ? (
        <p className="text-xs text-amber-300">{error}</p>
      ) : !job ? (
        <p className="text-xs text-slate-400">{t('devDashboard.governance.backupProgress.noJob')}</p>
      ) : (
        <>
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-200 mb-3">
            <div className="flex flex-wrap gap-x-2">
              <dt className="text-slate-500">{t('devDashboard.governance.backupProgress.jobId')}</dt>
              <dd className="font-mono">{job.job_id}</dd>
            </div>
            <div className="flex flex-wrap gap-x-2">
              <dt className="text-slate-500">{t('devDashboard.governance.backupProgress.status')}</dt>
              <dd className={statusTone(job.status)}>{job.status}</dd>
            </div>
            <div className="flex flex-wrap gap-x-2">
              <dt className="text-slate-500">{t('devDashboard.governance.backupProgress.type')}</dt>
              <dd>{job.type ?? '—'}</dd>
            </div>
            <div className="flex flex-wrap gap-x-2">
              <dt className="text-slate-500">{t('devDashboard.governance.backupProgress.code')}</dt>
              <dd className="truncate max-w-[220px]" title={job.code}>
                {job.code ?? '—'}
              </dd>
            </div>
            <div className="sm:col-span-2 flex flex-wrap gap-x-2">
              <dt className="text-slate-500">{t('devDashboard.governance.backupProgress.bytes')}</dt>
              <dd>{writtenHuman}</dd>
            </div>
            <div className="flex flex-wrap gap-x-2">
              <dt className="text-slate-500">{t('devDashboard.governance.backupProgress.throughput')}</dt>
              <dd>{rateHuman}</dd>
            </div>
            <div className="flex flex-wrap gap-x-2">
              <dt className="text-slate-500">{t('devDashboard.governance.backupProgress.elapsed')}</dt>
              <dd>{formatEta(elapsed)}</dd>
            </div>
            {phase ? (
              <div className="sm:col-span-2 flex flex-wrap gap-x-2">
                <dt className="text-slate-500">{t('devDashboard.governance.backupProgress.phase')}</dt>
                <dd>{phase}</dd>
              </div>
            ) : null}
            {compressor ? (
              <div className="sm:col-span-2 flex flex-wrap gap-x-2">
                <dt className="text-slate-500">{t('devDashboard.governance.backupProgress.compressor')}</dt>
                <dd>
                  {compressor}
                  {job.compression_threads != null ? ` (${job.compression_threads} threads)` : ''}
                </dd>
              </div>
            ) : null}
            {job.notification_status ? (
              <div className="flex flex-wrap gap-x-2">
                <dt className="text-slate-500">{t('devDashboard.governance.backupProgress.notification')}</dt>
                <dd>{job.notification_status}</dd>
              </div>
            ) : null}
            {job.unit_name ? (
              <div className="sm:col-span-2 flex flex-wrap gap-x-2">
                <dt className="text-slate-500">{t('devDashboard.governance.backupProgress.unit')}</dt>
                <dd className="font-mono text-[11px] break-all">{job.unit_name}</dd>
              </div>
            ) : null}
          </dl>

          <div className="mb-3">
            <p className="text-[10px] uppercase tracking-wide text-slate-500 mb-1">
              {t('devDashboard.governance.backupProgress.phaseTrack')}
            </p>
            <div className="flex flex-wrap gap-1">
              {['preflight', 'archiving', 'finalizing', 'sha256', 'verify_deep', 'notification'].map((step, i) => {
                const active = phaseIndex >= i || phase === step
                return (
                  <span
                    key={step}
                    className={`px-1.5 py-0.5 rounded text-[10px] ${
                      active ? 'bg-emerald-800/50 text-emerald-100' : 'bg-slate-800/80 text-slate-500'
                    }`}
                  >
                    {step}
                  </span>
                )
              })}
            </div>
          </div>

          {(longGzipWarn || staleWarning) && (
            <div className="flex gap-2 items-start text-amber-200 text-xs mb-2 p-2 rounded bg-amber-950/40 border border-amber-800/40">
              <AlertTriangle size={14} className="shrink-0 mt-0.5" />
              <div>
                {longGzipWarn ? <p>{t('devDashboard.governance.backupProgress.warnLongGzip')}</p> : null}
                {staleWarning ? <p>{t('devDashboard.governance.backupProgress.warnStaleProgress')}</p> : null}
              </div>
            </div>
          )}

          {(isFailed || job.tar_warning_classification || job.abort_reason) && (
            <div className="text-xs rounded border border-rose-900/50 bg-rose-950/40 p-2 text-rose-100 space-y-1">
              <p className="font-semibold">{t('devDashboard.governance.backupProgress.errorsTitle')}</p>
              {job.abort_reason ? <p>abort_reason: {job.abort_reason}</p> : null}
              {job.tar_warning_classification ? <p>tar_warning: {job.tar_warning_classification}</p> : null}
              {job.subprocess_returncode != null ? <p>tar_return_code: {job.subprocess_returncode}</p> : null}
              {job.last_error_code ? <p>code: {job.last_error_code}</p> : null}
              {job.partial_path && !job.final_archive_exists ? (
                <p>{t('devDashboard.governance.backupProgress.partialCleanupHint')}</p>
              ) : null}
              {job.fatal_patterns_found ? <p>fatal_patterns_found: true</p> : null}
              {Array.isArray(job.volatile_warning_paths) && job.volatile_warning_paths.length > 0 ? (
                <p className="truncate" title={job.volatile_warning_paths.slice(0, 5).join(', ')}>
                  volatile_paths: {job.volatile_warning_paths.length}
                </p>
              ) : null}
            </div>
          )}

          {isRunning && (
            <p className="text-[10px] text-slate-500 mt-2">{t('devDashboard.governance.backupProgress.greenRule')}</p>
          )}
        </>
      )}
    </section>
  )
}
