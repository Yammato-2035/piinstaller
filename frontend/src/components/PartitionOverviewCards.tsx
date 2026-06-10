/**
 * Datenträgerkarten – professionelles Tool-Design mit Backend-Klassifikation.
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { Lock, AlertTriangle } from 'lucide-react'
import type { DiskInfo } from '../api/partitionApi'
import {
  classifyDiskRole,
  detectOsHint,
  diskRoleLabel,
  diskToTargetDevice,
  isFallbackClassification,
  roleBadgeForDisk,
  type DiskRole,
} from '../lib/partition/partitionRoleUtils'
import {
  deviceIconForKind,
  filesystemSummary,
  inferDeviceIconKind,
  transportLabel,
} from '../lib/partition/deviceIconUtils'
import { TOOL_DISK_ROLE, TOOL_SHELL, TOOL_STATUS } from '../lib/theme/setuphelferToolTheme'

interface Props {
  disks: DiskInfo[]
  selectedDiskName: string | null
  onSelectDisk: (disk: DiskInfo) => void
  loading?: boolean
}

const ROLE_ORDER: DiskRole[] = ['system', 'windows_system', 'rescue', 'backup', 'other']

const badgeTone: Record<string, keyof typeof TOOL_STATUS> = {
  ok: 'safe',
  warning: 'review',
  blocked: 'blocked',
  readonly: 'info',
}

const PartitionOverviewCards: React.FC<Props> = ({
  disks,
  selectedDiskName,
  onSelectDisk,
  loading = false,
}) => {
  const { t, i18n } = useTranslation()
  const lang = i18n.language.startsWith('de') ? 'de' : 'en'

  if (loading) {
    return (
      <div className="grid gap-3" data-testid="partition-overview-cards-loading">
        {[1, 2].map((i) => (
          <div key={i} className={`h-44 ${TOOL_SHELL.panel} animate-pulse`} />
        ))}
      </div>
    )
  }

  const sorted = [...disks].sort((a, b) => {
    const ra = ROLE_ORDER.indexOf(classifyDiskRole(a))
    const rb = ROLE_ORDER.indexOf(classifyDiskRole(b))
    return ra - rb
  })

  if (sorted.length === 0) {
    return (
      <div className={`${TOOL_SHELL.panel} p-8 text-center text-slate-500`} data-testid="partition-overview-cards-empty">
        {t('partitionManager.cards.empty')}
      </div>
    )
  }

  return (
    <div className="grid gap-3" data-testid="partition-overview-cards">
      {sorted.map((disk) => {
        const role = classifyDiskRole(disk)
        const badge = roleBadgeForDisk(role, disk)
        const osHint = detectOsHint(disk)
        const isSelected = selectedDiskName === disk.name
        const backendLabel = diskRoleLabel(disk, lang)
        const storageRole = disk.storage_role
        const toneKey = storageRole ? TOOL_DISK_ROLE[storageRole.role] ?? 'unknown' : badgeTone[badge] ?? 'unknown'
        const tone = TOOL_STATUS[toneKey]
        const Icon = deviceIconForKind(inferDeviceIconKind(disk, storageRole))
        const devicePath = diskToTargetDevice(disk)

        return (
          <article
            key={disk.name}
            data-testid={`partition-disk-card-${disk.name}`}
            data-disk-role={role}
            data-storage-role={storageRole?.role ?? 'fallback'}
            className={`${TOOL_SHELL.panel} p-4 sm:p-5 flex flex-col gap-3 transition-all ${
              isSelected ? `ring-2 ${tone.border} shadow-md` : ''
            }`}
          >
            <div className="flex items-start gap-4">
              <div
                className={`w-14 h-14 rounded-lg flex items-center justify-center shrink-0 border ${tone.border} ${tone.panel}`}
              >
                <Icon className={`w-7 h-7 ${tone.text}`} />
              </div>
              <div className="min-w-0 flex-1 space-y-1">
                <p className={`text-xs font-bold uppercase tracking-wider ${tone.text}`}>
                  {backendLabel || t(`partitionManager.cards.role.${role === 'windows_system' ? 'windows' : role}`)}
                </p>
                <h3 className="text-lg font-bold text-slate-50 truncate">{disk.model || disk.display_name}</h3>
                <p className={TOOL_SHELL.mono}>{devicePath}</p>
                <p className="text-sm text-slate-300">
                  {disk.size_human}
                  {disk.vendor ? ` · ${disk.vendor.trim()}` : ''}
                </p>
                <p className="text-xs text-slate-500">
                  {transportLabel(disk)} · {filesystemSummary(disk)}
                </p>
              </div>
            </div>

            {osHint && (
              <p className="text-sm text-slate-400">{t(`partitionManager.cards.osHint.${osHint}`)}</p>
            )}

            {isFallbackClassification(disk) && (
              <p className="text-xs text-amber-300/90 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                {t('partitionManager.cards.fallbackClassification')}
              </p>
            )}

            <span className={`inline-flex items-center gap-2 self-start text-xs font-bold px-3 py-1.5 rounded-md border ${tone.badge}`}>
              {(badge === 'blocked' || storageRole?.write_allowed === false) && <Lock className="w-3.5 h-3.5" />}
              {t(`partitionManager.cards.badge.${badge}`)}
            </span>

            <button
              type="button"
              onClick={() => onSelectDisk(disk)}
              className="mt-auto w-full py-2.5 rounded-md border border-slate-600/60 bg-slate-800 hover:bg-slate-700 text-slate-100 text-sm font-semibold transition-colors"
              data-testid={`partition-disk-details-${disk.name}`}
            >
              {t('partitionManager.cards.details')}
            </button>
          </article>
        )
      })}
    </div>
  )
}

export default PartitionOverviewCards
