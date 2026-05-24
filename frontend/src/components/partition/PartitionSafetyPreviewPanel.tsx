/**
 * PartitionSafetyPreviewPanel – Phase-2 read-only Safety-Contracts (keine Schreibaktionen).
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { ShieldAlert, ShieldCheck, AlertTriangle, RefreshCw, Ban } from 'lucide-react'
import type {
  HardstopPreviewResult,
  ManifestLayoutPreviewResult,
  RestoreHandoffPreviewResult,
} from '../../api/partitionApi'

interface Props {
  selectedDevice: string | null
  hardstopPreview: HardstopPreviewResult | null
  manifestLayoutPreview: ManifestLayoutPreviewResult | null
  restoreHandoffPreview: RestoreHandoffPreviewResult | null
  loading: boolean
  error: string | null
  onRefreshSafetyPreview: () => void
}

const statusBadgeClass = (status: string) => {
  if (status === 'blocked') return 'bg-red-500/20 text-red-300 border-red-500/40'
  if (status === 'review_required' || status === 'unavailable') {
    return 'bg-amber-500/20 text-amber-200 border-amber-500/40'
  }
  return 'bg-emerald-500/20 text-emerald-200 border-emerald-500/40'
}

const riskBadgeClass = (risk: string) => {
  if (risk === 'red') return 'text-red-300'
  if (risk === 'yellow') return 'text-amber-300'
  return 'text-emerald-300'
}

const PartitionSafetyPreviewPanel: React.FC<Props> = ({
  selectedDevice,
  hardstopPreview,
  manifestLayoutPreview,
  restoreHandoffPreview,
  loading,
  error,
  onRefreshSafetyPreview,
}) => {
  const { t } = useTranslation()
  const evaluation = hardstopPreview?.evaluation
  const smartStatus = String(hardstopPreview?.context?.smart_status ?? '—')

  const codeLabel = (code: string): string => {
    const key = `partition.phase2.code.${code}`
    const translated = t(key)
    return translated !== key ? translated : code
  }

  if (!selectedDevice) {
    return (
      <div className="rounded-xl border border-slate-700/50 bg-slate-900/40 p-4 text-sm text-slate-500">
        {t('partition.phase2.selectDeviceHint')}
      </div>
    )
  }

  return (
    <div className="rounded-xl border border-teal-500/30 bg-slate-900/50 p-4 space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h3 className="text-sm font-semibold text-teal-300 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4" />
            {t('partition.phase2.title')}
          </h3>
          <p className="text-xs text-slate-400 mt-1">{t('partition.phase2.subtitle')}</p>
          <p className="text-xs font-mono text-slate-500 mt-0.5">{selectedDevice}</p>
        </div>
        <button
          type="button"
          onClick={onRefreshSafetyPreview}
          disabled={loading}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-slate-700/60 hover:bg-slate-700 text-slate-300 text-xs disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          {t('partition.phase2.refresh')}
        </button>
      </div>

      <div className="rounded-lg border border-amber-500/35 bg-amber-950/30 px-3 py-2 text-xs text-amber-100 flex gap-2">
        <Ban className="w-4 h-4 shrink-0 mt-0.5" />
        <span>{t('partition.phase2.noWriteBanner')}</span>
      </div>

      {error && (
        <div className="text-xs text-red-300 bg-red-950/40 border border-red-500/30 rounded-lg px-3 py-2">
          {error}
        </div>
      )}

      {loading && !hardstopPreview && (
        <div className="text-xs text-slate-500 animate-pulse">{t('partition.phase2.loading')}</div>
      )}

      {evaluation && (
        <>
          <section className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
              {t('partition.phase2.overview')}
            </h4>
            <div className="flex flex-wrap gap-2 text-xs">
              <span
                className={`px-2 py-0.5 rounded border ${statusBadgeClass(evaluation.status)}`}
              >
                {t(`partition.phase2.status.${evaluation.status}`)}
              </span>
              <span className={`px-2 py-0.5 ${riskBadgeClass(evaluation.risk_level)}`}>
                {t('partition.phase2.risk')}: {t(`partition.phase2.riskLevel.${evaluation.risk_level}`)}
              </span>
              <span className="px-2 py-0.5 text-slate-400">
                {t('partition.phase2.writeAccess')}:{' '}
                <strong className="text-red-300">{t('partition.phase2.writeBlocked')}</strong>
              </span>
            </div>
            {evaluation.codes.length > 0 && (
              <ul className="text-xs text-slate-400 list-disc list-inside space-y-0.5">
                {evaluation.codes.map((c) => (
                  <li key={c}>{codeLabel(c)}</li>
                ))}
              </ul>
            )}
          </section>

          <section className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
              {t('partition.phase2.hardstops')}
            </h4>
            {evaluation.hardstops.length === 0 ? (
              <p className="text-xs text-slate-500">{t('partition.phase2.hardstopsEmpty')}</p>
            ) : (
              <ul className="space-y-1">
                {evaluation.hardstops.map((h) => (
                  <li
                    key={h.code}
                    className="text-xs text-red-200 bg-red-950/30 border border-red-500/25 rounded px-2 py-1"
                  >
                    {codeLabel(h.code)}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="space-y-2">
            <h4 className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              {t('partition.phase2.smartGate')}
            </h4>
            <p className="text-xs text-slate-400">
              {t('partition.phase2.smartStatus')}:{' '}
              <span className="text-slate-200 font-medium">{smartStatus}</span>
            </p>
            <p className="text-xs text-slate-500">{t('partition.phase2.smartHint')}</p>
          </section>
        </>
      )}

      {manifestLayoutPreview && (
        <section className="space-y-2">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
            {t('partition.phase2.manifestTitle')}
          </h4>
          <span
            className={`inline-block text-xs px-2 py-0.5 rounded border ${statusBadgeClass(manifestLayoutPreview.status)}`}
          >
            {t(`partition.phase2.manifestStatus.${manifestLayoutPreview.status}`)}
          </span>
          {manifestLayoutPreview.suggested_layout.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="text-slate-500 border-b border-slate-700/50">
                    <th className="py-1 pr-2">{t('partition.partition.device')}</th>
                    <th className="py-1 pr-2">{t('partition.partition.size')}</th>
                    <th className="py-1 pr-2">{t('partition.partition.filesystem')}</th>
                    <th className="py-1">{t('partition.partition.mountpoint')}</th>
                  </tr>
                </thead>
                <tbody>
                  {manifestLayoutPreview.suggested_layout.map((row, i) => (
                    <tr key={i} className="border-b border-slate-800/60 text-slate-300">
                      <td className="py-1 pr-2 font-mono">{row.device ?? '—'}</td>
                      <td className="py-1 pr-2">{row.size ?? '—'}</td>
                      <td className="py-1 pr-2">{row.fs_type ?? '—'}</td>
                      <td className="py-1">{row.mountpoint ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-slate-500">{t('partition.phase2.manifestEmpty')}</p>
          )}
          {manifestLayoutPreview.manifest_path && (
            <p className="text-[11px] text-slate-500 font-mono truncate">
              {manifestLayoutPreview.manifest_path}
            </p>
          )}
        </section>
      )}

      {hardstopPreview?.storage_safety && (
        <section className="space-y-1">
          <h4 className="text-xs font-semibold text-slate-300">{t('partition.phase2.facadeTitle')}</h4>
          <span
            className={`inline-block text-xs px-2 py-0.5 rounded border ${statusBadgeClass(
              hardstopPreview.storage_safety.status
            )}`}
          >
            {t(`partition.phase2.status.${hardstopPreview.storage_safety.status}`)}
          </span>
        </section>
      )}

      {restoreHandoffPreview && (
        <section className="space-y-2">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wide">
            {t('partition.phase2.handoffTitle')}
          </h4>
          <span
            className={`inline-block text-xs px-2 py-0.5 rounded border ${statusBadgeClass(restoreHandoffPreview.status)}`}
          >
            {t(`partition.phase2.handoffStatus.${restoreHandoffPreview.status}`)}
          </span>
          <p className="text-xs text-slate-400">
            {t('partition.phase2.restoreExecution')}:{' '}
            <strong className="text-red-300">{t('partition.phase2.writeBlocked')}</strong>
          </p>
          {restoreHandoffPreview.required_next_gates?.length > 0 && (
            <ul className="text-xs text-slate-400 list-disc list-inside">
              {restoreHandoffPreview.required_next_gates.map((g) => (
                <li key={g}>{g}</li>
              ))}
            </ul>
          )}
          {restoreHandoffPreview.status === 'ready' && (
            <p className="text-xs text-teal-300/90">{t('partition.phase2.restorePreviewRecommended')}</p>
          )}
        </section>
      )}

      {(evaluation || restoreHandoffPreview) && (
        <section className="rounded-lg border border-slate-600/40 bg-slate-800/40 px-3 py-2">
          <h4 className="text-xs font-semibold text-slate-300 mb-1">
            {t('partition.phase2.nextSafeAction')}
          </h4>
          <p className="text-xs text-slate-400">
            {evaluation?.status === 'blocked' || restoreHandoffPreview?.status === 'blocked'
              ? t('partition.phase2.nextSafeActionBlocked')
              : evaluation?.status === 'review_required' ||
                  restoreHandoffPreview?.status === 'review_required' ||
                  manifestLayoutPreview?.status === 'unavailable'
                ? t('partition.phase2.nextSafeActionReview')
                : t('partition.phase2.nextSafeActionOk')}
          </p>
        </section>
      )}
    </div>
  )
}

export default PartitionSafetyPreviewPanel
