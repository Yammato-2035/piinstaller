import React from 'react'
import type { TFunction } from 'i18next'
import {
  archivePercent,
  formatBytesBinary,
  formatEtaForDisplay,
  hasReliableBytesTotal,
  isStructuredProgressOptional,
  shouldShowCompressionBottleneckHint,
  shouldShowSlowButActiveHint,
  shouldShowTargetIoHint,
} from '../utils/backupJobProgressDisplay'

export type BackupJobLike = {
  job_id?: string
  status?: string
  code?: string
  message?: string
  progress_optional?: unknown
}

type Props = {
  job: BackupJobLike
  t: TFunction
  /** z. B. sky-100/80 im Tab, slate-300 im Modal */
  textClass?: string
  mutedClass?: string
}

function phaseLabel(t: TFunction, phase: string): string {
  const p = String(phase || 'unknown').toLowerCase().replace(/[^a-z0-9_-]/g, '_')
  const key = `runningBackup.progress.phase.${p}`
  const tr = t(key)
  return tr === key ? phase || '—' : tr
}

export const BackupJobProgressSection: React.FC<Props> = ({
  job,
  t,
  textClass = 'text-xs text-slate-300',
  mutedClass = 'text-slate-400',
}) => {
  const po = job.progress_optional
  if (!isStructuredProgressOptional(po)) {
    return (
      <div className={`${textClass} mt-1`}>
        <span className={mutedClass}>{t('runningBackup.progress.noStructuredProgress')}</span>
      </div>
    )
  }

  const pct = archivePercent(po)
  const eta = formatEtaForDisplay(po)
  const curStr = formatBytesBinary(typeof po.bytes_current === 'number' ? po.bytes_current : undefined)
  const totStr =
    hasReliableBytesTotal(po) && typeof po.bytes_total_estimate === 'number'
      ? formatBytesBinary(po.bytes_total_estimate)
      : null
  const thr =
    typeof po.throughput_mib_s === 'number' && Number.isFinite(po.throughput_mib_s)
      ? po.throughput_mib_s
      : null
  const elapsed =
    typeof po.elapsed_seconds === 'number' && Number.isFinite(po.elapsed_seconds) ? po.elapsed_seconds : null
  const freeStr =
    typeof po.target_free_bytes === 'number' && Number.isFinite(po.target_free_bytes)
      ? formatBytesBinary(po.target_free_bytes)
      : null

  const showSlow = shouldShowSlowButActiveHint(po, job.status)
  const showComp = shouldShowCompressionBottleneckHint(po)
  const showIo = shouldShowTargetIoHint(job.code, po)
  const pkgBlocked = String(job.code || '') === 'backup.blocked_package_activity'

  const health = po.health_flags && typeof po.health_flags === 'object' ? po.health_flags : null
  const warnings = Array.isArray(po.warning_codes) ? po.warning_codes : []

  return (
    <div className={`space-y-2 mt-2 border-t border-slate-600/40 pt-2 ${textClass}`}>
      <div>
        <span className="font-semibold">{t('runningBackup.progress.phaseLabel')}</span>{' '}
        {phaseLabel(t, String(po.phase || ''))}
      </div>

      {po.current_operation ? (
        <div>
          <span className="font-semibold">{t('runningBackup.progress.operationLabel')}</span> {po.current_operation}
        </div>
      ) : null}

      {po.compression_method ? (
        <div>
          <span className="font-semibold">{t('runningBackup.progress.compressionLabel')}</span> {po.compression_method}
        </div>
      ) : null}

      <div>
        <span className="font-semibold">{t('runningBackup.progress.bytesLabel')}</span>{' '}
        {curStr ?? '—'}
        {totStr ? (
          <>
            {' '}
            / {totStr}
          </>
        ) : (
          <span className={`ml-1 ${mutedClass}`}>({t('runningBackup.progress.totalUnknown')})</span>
        )}
      </div>

      {pct !== null ? (
        <div>
          <div className="flex justify-between text-[10px] uppercase tracking-wide mb-0.5">
            <span>{t('runningBackup.progress.percentLabel')}</span>
            <span>{pct}%</span>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-1.5">
            <div className="bg-sky-500 h-1.5 rounded-full transition-all" style={{ width: `${pct}%` }} />
          </div>
        </div>
      ) : (
        <div className={mutedClass}>{t('runningBackup.progress.activeNoPercent')}</div>
      )}

      <div className="flex flex-wrap gap-x-3 gap-y-1">
        {thr !== null ? (
          <span>
            <span className="font-semibold">{t('runningBackup.progress.throughputLabel')}</span> {thr} MiB/s
          </span>
        ) : null}
        {elapsed !== null ? (
          <span>
            <span className="font-semibold">{t('runningBackup.progress.elapsedLabel')}</span> {elapsed}s
          </span>
        ) : null}
        <span>
          <span className="font-semibold">{t('runningBackup.progress.etaLabel')}</span>{' '}
          {eta.kind === 'seconds'
            ? t('runningBackup.progress.etaSeconds', { sec: eta.sec })
            : t('backup.messages.eta_unknown')}
        </span>
      </div>

      {po.target_mount ? (
        <div>
          <span className="font-semibold">{t('runningBackup.progress.targetMountLabel')}</span> {po.target_mount}
        </div>
      ) : null}
      {freeStr ? (
        <div>
          <span className="font-semibold">{t('runningBackup.progress.targetFreeLabel')}</span> {freeStr}
        </div>
      ) : null}

      {showSlow ? (
        <div className="p-2 rounded bg-slate-700/50 text-[11px] leading-snug">{t('backup.messages.slow_but_active')}</div>
      ) : null}
      {showComp ? (
        <div className="p-2 rounded bg-amber-900/20 border border-amber-700/30 text-[11px] leading-snug">
          {t('backup.messages.compression_bottleneck')}
        </div>
      ) : null}
      {showIo ? (
        <div className="p-2 rounded bg-red-900/20 border border-red-700/30 text-[11px] leading-snug">
          {t('backup.messages.write_io_error')}
        </div>
      ) : null}
      {pkgBlocked ? (
        <div className="p-2 rounded bg-orange-900/20 border border-orange-700/30 text-[11px] leading-snug">
          {t('backup.messages.package_blocks_backup')}
        </div>
      ) : null}

      {warnings.length > 0 ? (
        <div>
          <div className="font-semibold mb-0.5">{t('runningBackup.progress.warningsTitle')}</div>
          <ul className="list-disc list-inside text-[11px] space-y-0.5">
            {warnings.map((w) => {
              const k = `runningBackup.progress.warningCode.${w}`
              const tr = t(k)
              return <li key={w}>{tr === k ? String(w) : tr}</li>
            })}
          </ul>
        </div>
      ) : null}

      {health && Object.keys(health).length > 0 ? (
        <div>
          <div className="font-semibold mb-0.5">{t('runningBackup.progress.healthTitle')}</div>
          <pre className="text-[10px] whitespace-pre-wrap break-all bg-slate-900/60 p-2 rounded max-h-24 overflow-y-auto">
            {JSON.stringify(health, null, 0)}
          </pre>
        </div>
      ) : null}
    </div>
  )
}

export default BackupJobProgressSection
