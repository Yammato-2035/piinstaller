/**
 * Externes Backup-Ziel: Kandidaten, Mount-Vorbereitung, target-check (read-only + Hinweise).
 */
import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { FolderOpen } from 'lucide-react'
import { fetchApi } from '../../api'

type ExternalCandidate = {
  partition_id?: string
  uuid?: string
  existing_mount?: string
  transport?: string
  fstype?: string
}

type TargetCheckPayload = {
  status?: string
  diagnosis_id?: string
  backup_dir?: string
  auto_prepare?: { status?: string; diagnosis_id?: string }
  mount_inspection?: { would_block_diagnosis_id?: string }
}

function trafficFromCheck(tc: TargetCheckPayload | null): 'green' | 'yellow' | 'red' | 'gray' {
  if (!tc) return 'gray'
  if (tc.status === 'success') return 'green'
  const d = tc.diagnosis_id || tc.mount_inspection?.would_block_diagnosis_id || ''
  if (d === 'BACKUP-TARGET-AUTO-MOUNT-READY') return 'green'
  if (d === 'STORAGE-PROTECTION-007' || d === 'BACKUP-TARGET-EXTERNAL-MOUNT-004') return 'yellow'
  if (d === 'BACKUP-TARGET-AUTO-MOUNT-FAILED') return 'red'
  return 'red'
}

function TargetRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline gap-x-2 text-xs mb-1">
      <span className="text-slate-500 shrink-0">{label}</span>
      <span className="flex items-center flex-wrap">{children}</span>
    </div>
  )
}

export function CockpitBackupTargetPanel({
  refreshSec,
  defaultLabel = 'br001',
}: {
  refreshSec: number
  defaultLabel?: string
}) {
  const { t } = useTranslation()
  const [candidates, setCandidates] = useState<ExternalCandidate[]>([])
  const [targetCheck, setTargetCheck] = useState<TargetCheckPayload | null>(null)
  const [error, setError] = useState<string | null>(null)
  const backupDir = `/media/setuphelfer/${defaultLabel}`

  const poll = useCallback(async () => {
    try {
      setError(null)
      const extRes = await fetchApi('/api/backup/external-targets')
      const extJson = (await extRes.json()) as { status?: string; candidates?: ExternalCandidate[] }
      if (extJson.status === 'success' && Array.isArray(extJson.candidates)) {
        setCandidates(extJson.candidates)
      } else {
        setCandidates([])
      }
      const q = new URLSearchParams({
        backup_dir: backupDir,
        label: defaultLabel,
      })
      const tcRes = await fetchApi(`/api/backup/target-check?${q.toString()}`)
      const raw = (await tcRes.json()) as TargetCheckPayload & {
        details?: { diagnosis_id?: string; auto_prepare?: TargetCheckPayload['auto_prepare'] }
      }
      const det = raw.details
      setTargetCheck({
        ...raw,
        diagnosis_id: raw.diagnosis_id || det?.diagnosis_id,
        auto_prepare: raw.auto_prepare || det?.auto_prepare,
      })
    } catch {
      setError(t('devDashboard.governance.backupTarget.fetchError'))
      setCandidates([])
      setTargetCheck(null)
    }
  }, [backupDir, defaultLabel, t])

  useEffect(() => {
    void poll()
    const ms = Math.min(Math.max(refreshSec, 5), 60) * 1000
    const id = window.setInterval(() => void poll(), ms)
    return () => window.clearInterval(id)
  }, [poll, refreshSec])

  const traffic = trafficFromCheck(targetCheck)
  const dot =
    traffic === 'green'
      ? 'bg-emerald-500'
      : traffic === 'yellow'
        ? 'bg-amber-400'
        : traffic === 'red'
          ? 'bg-red-500'
          : 'bg-slate-500'

  return (
    <section
      className="rounded-lg border border-slate-700 bg-slate-900/40 p-4 mb-4"
      data-testid="cockpit-backup-target"
    >
      <h2 className="text-sm font-semibold text-white flex items-center gap-2 mb-1">
        <FolderOpen size={16} className="text-violet-400" aria-hidden />
        {t('devDashboard.governance.backupTarget.title')}
      </h2>
      <p className="text-xs text-slate-400 mb-3">{t('devDashboard.governance.backupTarget.subtitle')}</p>

      {error ? <p className="text-xs text-red-300 mb-2">{error}</p> : null}

      <TargetRow label={t('devDashboard.governance.backupTarget.status')}>
        <span className={`inline-block w-2.5 h-2.5 rounded-full ${dot}`} aria-hidden />
        <span className="text-slate-200 ml-2">{targetCheck?.status || '—'}</span>
        {targetCheck?.diagnosis_id ? (
          <span className="text-slate-400 ml-2 font-mono text-[11px]">{targetCheck.diagnosis_id}</span>
        ) : null}
      </TargetRow>

      <TargetRow label={t('devDashboard.governance.backupTarget.path')}>
        <code className="text-xs text-sky-200">{backupDir}</code>
      </TargetRow>

      <TargetRow label={t('devDashboard.governance.backupTarget.externalDetected')}>
        {candidates.length > 0
          ? t('devDashboard.governance.backupTarget.externalYes', { count: candidates.length })
          : t('devDashboard.governance.backupTarget.externalNo')}
      </TargetRow>

      {candidates[0] ? (
        <ul className="text-xs text-slate-300 mt-2 space-y-1 font-mono">
          <li>
            {candidates[0].partition_id} → {candidates[0].existing_mount || t('devDashboard.governance.backupTarget.notMounted')}
          </li>
        </ul>
      ) : null}

      {targetCheck?.status !== 'success' ? (
        <p className="text-xs text-amber-200/90 mt-3 border-t border-slate-700 pt-2">
          {t('devDashboard.governance.backupTarget.prepareHint')}
        </p>
      ) : null}
    </section>
  )
}
