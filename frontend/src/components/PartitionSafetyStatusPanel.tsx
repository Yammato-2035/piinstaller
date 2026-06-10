/**
 * PartitionSafetyStatusPanel – dominanter Sicherheitsbereich (Mockup Phase 2.3).
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import {
  ShieldCheck,
  RefreshCw,
  Ban,
  CheckCircle,
  AlertTriangle,
  XCircle,
  HardDrive,
  Database,
} from 'lucide-react'
import type {
  HardstopPreviewResult,
  ManifestLayoutPreviewResult,
  RestoreHandoffPreviewResult,
} from '../api/partitionApi'
import {
  MOCKUP_RISK_BADGE,
  MOCKUP_SECTION,
  MOCKUP_STATUS,
  statusLevelToTone,
} from '../lib/partition/partitionMockupTheme'

interface Props {
  selectedDevice: string | null
  hardstopPreview: HardstopPreviewResult | null
  manifestLayoutPreview: ManifestLayoutPreviewResult | null
  restoreHandoffPreview: RestoreHandoffPreviewResult | null
  loading: boolean
  error: string | null
  onRefresh: () => void
}

type StatusLevel = 'ok' | 'warning' | 'blocked'

const levelIcon: Record<StatusLevel, React.ReactNode> = {
  ok: <CheckCircle className="w-5 h-5" />,
  warning: <AlertTriangle className="w-5 h-5" />,
  blocked: <XCircle className="w-5 h-5" />,
}

const PartitionSafetyStatusPanel: React.FC<Props> = ({
  selectedDevice,
  hardstopPreview,
  manifestLayoutPreview,
  restoreHandoffPreview,
  loading,
  error,
  onRefresh,
}) => {
  const { t } = useTranslation()
  const evaluation = hardstopPreview?.evaluation
  const smartStatus = String(hardstopPreview?.context?.smart_status ?? 'missing')
  const risk = evaluation?.risk_level ?? 'yellow'
  const hardstopCount = evaluation?.hardstops.length ?? 0

  const smartLevel: StatusLevel =
    smartStatus === 'ok' ? 'ok' : smartStatus === 'warning' || smartStatus === 'unknown' ? 'warning' : 'blocked'

  const systemDiskLevel: StatusLevel = evaluation?.codes.some((c) => c.includes('system_disk'))
    ? 'blocked'
    : selectedDevice
      ? 'warning'
      : 'ok'

  const backupFound =
    manifestLayoutPreview?.status === 'ok' || (manifestLayoutPreview?.suggested_layout.length ?? 0) > 0
  const backupLevel: StatusLevel = backupFound ? 'ok' : manifestLayoutPreview ? 'warning' : 'blocked'

  const hardstopLevel: StatusLevel = hardstopCount > 0 ? 'blocked' : evaluation ? 'ok' : 'warning'

  const handoffLevel: StatusLevel =
    restoreHandoffPreview?.status === 'ready'
      ? 'ok'
      : restoreHandoffPreview?.status === 'review_required'
        ? 'warning'
        : restoreHandoffPreview
          ? 'blocked'
          : 'warning'

  const cards: Array<{ key: string; level: StatusLevel; icon: React.ReactNode }> = [
    { key: 'smart', level: smartLevel, icon: <HardDrive className="w-5 h-5" /> },
    { key: 'bootable', level: systemDiskLevel === 'blocked' ? 'blocked' : evaluation ? 'ok' : 'warning', icon: <ShieldCheck className="w-5 h-5" /> },
    { key: 'hardstops', level: hardstopLevel, icon: <AlertTriangle className="w-5 h-5" /> },
    { key: 'backupFound', level: backupLevel, icon: <Database className="w-5 h-5" /> },
    { key: 'restoreHandoff', level: handoffLevel, icon: <RefreshCw className="w-5 h-5" /> },
    { key: 'writeAllowed', level: 'blocked', icon: <Ban className="w-5 h-5" /> },
  ]

  const secureLabel =
    risk === 'green'
      ? t('partitionSafety.secureBadge.safe')
      : risk === 'yellow'
        ? t('partitionSafety.secureBadge.review')
        : t('partitionSafety.secureBadge.blocked')

  const cockpitRows: Array<{ key: string; label: string; level: StatusLevel }> = [
    { key: 'smart', label: t('partitionSafety.items.smart'), level: smartLevel },
    { key: 'boot', label: t('partitionSafety.items.bootable'), level: systemDiskLevel === 'blocked' ? 'blocked' : evaluation ? 'ok' : 'warning' },
    { key: 'role', label: t('partitionWorkbench.cockpit.diskRole'), level: systemDiskLevel },
    { key: 'write', label: t('partitionSafety.items.writeAllowed'), level: 'blocked' },
    { key: 'hardstops', label: t('partitionSafety.items.hardstops'), level: hardstopLevel },
    { key: 'restore', label: t('partitionSafety.items.restoreHandoff'), level: handoffLevel },
  ]

  return (
    <aside
      className={`${MOCKUP_SECTION} flex flex-col gap-4 min-h-0 border-teal-500/30`}
      data-testid="partition-safety-status-panel"
    >
      <div className="border-b border-teal-500/25 pb-3">
        <div className="flex items-start justify-between gap-2">
        <h2 className="text-base font-black text-teal-200 flex items-center gap-2 uppercase tracking-[0.18em]">
          <ShieldCheck className="w-5 h-5" />
          {t('partitionSafety.title')}
        </h2>
        <button
          type="button"
          onClick={onRefresh}
          disabled={loading || !selectedDevice}
          className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 disabled:opacity-40"
          aria-label={t('partition.phase2.refresh')}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
        </div>
        <p className="text-xs text-slate-500 mt-1">{t('partitionWorkbench.cockpit.subtitle')}</p>
      </div>

      <div className="space-y-2" data-testid="partition-safety-cockpit-rows">
        {cockpitRows.map((row) => {
          const tone = statusLevelToTone(row.level)
          const styles = MOCKUP_STATUS[tone]
          return (
            <div
              key={row.key}
              className={`flex items-center justify-between gap-3 rounded-lg border px-3 py-2.5 ${styles.card}`}
              data-testid={`partition-cockpit-row-${row.key}`}
            >
              <span className={`text-xs font-bold uppercase tracking-wide ${styles.text}`}>{row.label}</span>
              <span className={`flex items-center gap-1.5 text-sm font-bold ${styles.text}`}>
                {levelIcon[row.level]}
                {t(`partitionSafety.level.${row.level}`)}
              </span>
            </div>
          )
        })}
      </div>

      <div
        className={`rounded-lg border px-5 py-6 text-center shadow-lg ${MOCKUP_RISK_BADGE[risk] ?? MOCKUP_RISK_BADGE.yellow}`}
        data-testid="partition-secure-badge"
      >
        <p className="text-3xl sm:text-4xl font-black tracking-wider">{secureLabel}</p>
        <p className="text-xs mt-2 opacity-85 uppercase tracking-[0.2em] font-semibold">
          {t('partitionSafety.overallRisk')}: {t(`partition.phase2.riskLevel.${risk}`)}
        </p>
      </div>

      {error && (
        <div
          className="text-sm text-red-200 bg-red-950/50 border border-red-500/40 rounded-xl px-4 py-3"
          data-testid="partition-safety-error"
        >
          {error}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        {cards.map(({ key, level, icon }) => {
          const tone = statusLevelToTone(level)
          const styles = MOCKUP_STATUS[tone]
          return (
            <div
              key={key}
              className={`rounded-xl border p-3 flex flex-col gap-2 min-h-[88px] ${styles.card}`}
              data-testid={`partition-safety-item-${key}`}
            >
              <div className={`flex items-center gap-2 ${styles.text}`}>
                {icon}
                <span className="text-[11px] font-bold uppercase tracking-wide leading-tight">
                  {t(`partitionSafety.items.${key}`)}
                </span>
              </div>
              <div className={`flex items-center gap-1.5 mt-auto text-sm font-bold ${styles.text}`}>
                {levelIcon[level]}
                <span>{t(`partitionSafety.level.${level}`)}</span>
              </div>
            </div>
          )
        })}
      </div>

      {hardstopCount > 0 && (
        <div
          className={`rounded-xl border px-4 py-4 text-sm ${MOCKUP_STATUS.review.card} ${MOCKUP_STATUS.review.text}`}
          data-testid="partition-hardstop-summary"
        >
          <p className="font-bold">{t('partitionSafety.hardstopBox.title')}</p>
          <p className="mt-1 opacity-90">{t('partitionSafety.hardstopBox.body')}</p>
        </div>
      )}

      <div
        className={`rounded-xl border px-4 py-4 text-center ${MOCKUP_STATUS.blocked.card}`}
        data-testid="partition-write-allowed-false"
      >
        <p className="text-xs uppercase tracking-[0.15em] text-red-300/90 font-semibold">
          {t('partitionSafety.writeAllowedLabel')}
        </p>
        <p className="text-2xl font-black text-red-100 font-mono mt-1">false</p>
      </div>

      <div
        className={`rounded-xl border px-4 py-3 text-sm flex gap-3 ${MOCKUP_STATUS.info.card} ${MOCKUP_STATUS.info.text}`}
      >
        <Ban className="w-5 h-5 shrink-0" />
        <span data-testid="partition-write-blocked-banner">{t('partitionSafety.writeBlockedBanner')}</span>
      </div>
    </aside>
  )
}

export default PartitionSafetyStatusPanel
