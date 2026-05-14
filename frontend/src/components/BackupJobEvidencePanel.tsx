import React, { useCallback, useState } from 'react'
import type { TFunction } from 'i18next'
import { fetchApi } from '../api'
import toast from 'react-hot-toast'

export type EvidenceApiPayload = {
  evidence_status?: string
  evidence_dir?: string | null
  manifest_path?: string | null
  collected_sources?: unknown[]
  permission_denied_sources?: unknown[]
  errors?: string[]
}

type Props = {
  jobId: string
  t: TFunction
  /** Wenn true: kompakter Textstil (Modal) */
  compact?: boolean
}

export const BackupJobEvidencePanel: React.FC<Props> = ({ jobId, t, compact }) => {
  const [loading, setLoading] = useState(false)
  const [evidence, setEvidence] = useState<EvidenceApiPayload | null>(null)

  const loadGet = useCallback(async () => {
    if (!jobId) return
    setLoading(true)
    try {
      const r = await fetchApi(`/api/backup/jobs/${encodeURIComponent(jobId)}/evidence`)
      const d = await r.json()
      if (d.status === 'success' && d.evidence) {
        setEvidence(d.evidence as EvidenceApiPayload)
      } else {
        setEvidence(null)
        toast.error(d.message || t('runningBackup.evidence.loadError'))
      }
    } catch {
      toast.error(t('runningBackup.evidence.loadError'))
      setEvidence(null)
    } finally {
      setLoading(false)
    }
  }, [jobId, t])

  const runCollect = useCallback(async () => {
    if (!jobId) return
    setLoading(true)
    try {
      const r = await fetchApi(`/api/backup/jobs/${encodeURIComponent(jobId)}/evidence`, { method: 'POST' })
      const d = await r.json()
      if (d.status === 'success' && d.evidence) {
        const evp = d.evidence as EvidenceApiPayload
        setEvidence(evp)
        if (evp.evidence_status === 'error') {
          toast.error(t('runningBackup.evidence.collectError'))
        } else {
          toast.success(t('runningBackup.evidence.collectOk'))
        }
      } else {
        toast.error(d.message || t('runningBackup.evidence.collectError'))
      }
    } catch {
      toast.error(t('runningBackup.evidence.collectError'))
    } finally {
      setLoading(false)
    }
  }, [jobId, t])

  const textCls = compact ? 'text-[11px] text-slate-300' : 'text-xs text-sky-100/90'

  return (
    <div className={`mt-2 space-y-2 border-t border-slate-600/40 pt-2 ${textCls}`}>
      <div className="font-semibold">{t('runningBackup.evidence.heading')}</div>
      <div className="flex flex-wrap gap-2">
        <button
          type="button"
          disabled={loading}
          onClick={runCollect}
          className="px-2 py-1 rounded bg-sky-700/40 hover:bg-sky-600/50 border border-sky-500/40 text-xs disabled:opacity-50"
        >
          {loading ? t('runningBackup.evidence.working') : t('runningBackup.evidence.create')}
        </button>
        <button
          type="button"
          disabled={loading}
          onClick={loadGet}
          className="px-2 py-1 rounded bg-slate-700/60 hover:bg-slate-600/60 border border-slate-500/40 text-xs disabled:opacity-50"
        >
          {t('runningBackup.evidence.refresh')}
        </button>
      </div>
      <p className="text-[10px] opacity-80">{t('runningBackup.evidence.hintPaths')}</p>
      {evidence ? (
        <div className="space-y-1 rounded bg-slate-900/50 p-2 font-mono text-[10px] break-all">
          <div>
            <span className="font-sans font-semibold">{t('runningBackup.evidence.statusLabel')}</span> {evidence.evidence_status}
          </div>
          {evidence.evidence_dir ? (
            <div>
              <span className="font-sans font-semibold">{t('runningBackup.evidence.dirLabel')}</span> {evidence.evidence_dir}
            </div>
          ) : null}
          {evidence.manifest_path ? (
            <div>
              <span className="font-sans font-semibold">{t('runningBackup.evidence.manifestLabel')}</span> {evidence.manifest_path}
            </div>
          ) : null}
          {(evidence.permission_denied_sources?.length ?? 0) > 0 ? (
            <div className="text-amber-300">
              {t('runningBackup.evidence.permissionDenied')}: {(evidence.permission_denied_sources || []).join(', ')}
            </div>
          ) : null}
          {(evidence.errors?.length ?? 0) > 0 ? (
            <div className="text-red-300">{t('runningBackup.evidence.errors')}: {(evidence.errors || []).join(' | ')}</div>
          ) : null}
          {evidence.evidence_status === 'not_available' ? (
            <div className="text-slate-400">{t('runningBackup.evidence.notAvailable')}</div>
          ) : null}
        </div>
      ) : null}
    </div>
  )
}

export default BackupJobEvidencePanel
