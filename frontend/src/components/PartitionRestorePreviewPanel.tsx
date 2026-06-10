/**
 * PartitionRestorePreviewPanel – Restore-Handoff-Vorschau (Phase 2.3 Mockup, read-only).
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { ArrowRightLeft, Ban, CheckCircle, XCircle, RefreshCw } from 'lucide-react'
import type { ManifestLayoutPreviewResult, RestoreHandoffPreviewResult } from '../api/partitionApi'
import { MOCKUP_SECTION, MOCKUP_STATUS } from '../lib/partition/partitionMockupTheme'

interface Props {
  restoreHandoff: RestoreHandoffPreviewResult | null
  manifestLayout: ManifestLayoutPreviewResult | null
  loading?: boolean
  onRefresh?: () => void
}

const statusTone: Record<string, keyof typeof MOCKUP_STATUS> = {
  ready: 'safe',
  review_required: 'review',
  blocked: 'blocked',
}

function layoutRoleLabel(
  row: { mountpoint?: string | null; fs_type?: string | null; label?: string | null },
  t: (k: string) => string,
): string {
  const mp = (row.mountpoint ?? '').toLowerCase()
  if (mp === '/boot/efi' || mp === '/efi') return t('partitionManager.layoutPreview.roles.efi')
  if (mp === '/') return t('partitionManager.layoutPreview.roles.root')
  if (mp.startsWith('/home')) return t('partitionManager.layoutPreview.roles.home')
  if (row.fs_type === 'swap') return t('partitionManager.layoutPreview.roles.swap')
  return t('restorePreview.planned.otherMedia')
}

const PartitionRestorePreviewPanel: React.FC<Props> = ({
  restoreHandoff,
  manifestLayout,
  loading = false,
  onRefresh,
}) => {
  const { t } = useTranslation()

  if (!restoreHandoff && !manifestLayout) {
    return null
  }

  const status = restoreHandoff?.status ?? 'blocked'
  const tone = statusTone[status] ?? 'blocked'
  const plannedRows = manifestLayout?.suggested_layout ?? []

  return (
    <section
      className={`${MOCKUP_SECTION} space-y-5 border-sky-500/25`}
      data-testid="partition-restore-preview-panel"
    >
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-black text-sky-100 flex items-center gap-3">
            <ArrowRightLeft className="w-6 h-6" />
            {t('restorePreview.title')}
          </h3>
          <p className="text-sm text-slate-400 mt-1">{t('restorePreview.subtitle')}</p>
        </div>
        {restoreHandoff && (
          <span
            className={`text-sm font-bold px-4 py-2 rounded-xl border ${MOCKUP_STATUS[tone].pill}`}
            data-testid="partition-restore-handoff-status"
          >
            {t(`restorePreview.status.${status}`)}
          </span>
        )}
      </div>

      <div
        className={`flex items-center gap-4 rounded-xl border px-5 py-4 ${MOCKUP_STATUS.blocked.card}`}
        data-testid="partition-restore-execution-blocked"
      >
        <Ban className="w-7 h-7 text-red-300 shrink-0" />
        <div>
          <p className="text-xs text-red-300/90 uppercase tracking-[0.12em] font-semibold">
            {t('restorePreview.executionLabel')}
          </p>
          <p className="text-xl font-black font-mono text-red-100 mt-0.5">restore_execution_allowed=false</p>
        </div>
      </div>

      {plannedRows.length > 0 ? (
        <div className="grid sm:grid-cols-2 gap-3">
          {plannedRows.map((row, i) => {
            const label = layoutRoleLabel(row, t)
            const allowed = label !== t('restorePreview.planned.otherMedia')
            const itemTone = allowed ? 'safe' : 'blocked'
            return (
              <div
                key={i}
                className={`flex items-center gap-3 rounded-xl border px-4 py-3 ${MOCKUP_STATUS[itemTone].card}`}
                data-testid={`partition-restore-planned-${i}`}
              >
                {allowed ? (
                  <CheckCircle className="w-6 h-6 text-emerald-400 shrink-0" />
                ) : (
                  <XCircle className="w-6 h-6 text-red-400 shrink-0" />
                )}
                <div className="min-w-0">
                  <p className="font-bold text-slate-100">{label}</p>
                  {row.size != null && (
                    <p className="text-xs text-slate-500">{String(row.size)}</p>
                  )}
                </div>
              </div>
            )
          })}
          <div
            className={`flex items-center gap-3 rounded-xl border px-4 py-3 sm:col-span-2 ${MOCKUP_STATUS.blocked.card}`}
          >
            <XCircle className="w-6 h-6 text-red-400 shrink-0" />
            <p className="font-semibold text-red-100">{t('restorePreview.planned.otherMediaBlocked')}</p>
          </div>
        </div>
      ) : (
        <p className="text-sm text-slate-500">{t('restorePreview.plannedEmpty')}</p>
      )}

      {restoreHandoff?.required_next_gates && restoreHandoff.required_next_gates.length > 0 && (
        <div className="text-sm text-slate-400">
          <h4 className="font-semibold text-slate-300 mb-1">{t('restorePreview.nextGates')}</h4>
          <ul className="list-disc list-inside space-y-0.5">
            {restoreHandoff.required_next_gates.map((g) => (
              <li key={g}>{g}</li>
            ))}
          </ul>
        </div>
      )}

      {restoreHandoff?.recommended_next_step && (
        <p className="text-sm text-sky-200/90">{restoreHandoff.recommended_next_step}</p>
      )}

      {onRefresh && (
        <button
          type="button"
          disabled={loading}
          onClick={onRefresh}
          className="w-full flex items-center justify-center gap-3 py-4 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-base font-bold transition-colors shadow-lg shadow-sky-900/35"
          data-testid="partition-restore-preview-refresh"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          {t('partitionManager.restorePreviewRefresh')}
        </button>
      )}
    </section>
  )
}

export default PartitionRestorePreviewPanel
