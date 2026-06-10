/**
 * Datenträger-Seitenleiste – dauerhaft links, Workbench-Navigation.
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { AlertTriangle, Loader2 } from 'lucide-react'
import type { DiskInfo } from '../../api/partitionApi'
import {
  classifyDiskRole,
  diskRoleLabel,
  diskToTargetDevice,
  roleBadgeForDisk,
} from '../../lib/partition/partitionRoleUtils'
import {
  deviceIconForKind,
  inferDeviceIconKind,
} from '../../lib/partition/deviceIconUtils'
import { TOOL_SHELL } from '../../lib/theme/setuphelferToolTheme'

export type DiskLoadState =
  | { kind: 'loading' }
  | { kind: 'ok' }
  | { kind: 'empty' }
  | { kind: 'error'; message: string; hint?: string }

const ROLE_ACCENT: Record<string, { border: string; bg: string; text: string; dot: string }> = {
  windows_system_disk: {
    border: 'border-blue-500/70',
    bg: 'bg-blue-950/45',
    text: 'text-blue-100',
    dot: 'bg-blue-400',
  },
  linux_system_disk: {
    border: 'border-emerald-500/70',
    bg: 'bg-emerald-950/45',
    text: 'text-emerald-100',
    dot: 'bg-emerald-400',
  },
  mixed_system_disk: {
    border: 'border-emerald-500/70',
    bg: 'bg-emerald-950/45',
    text: 'text-emerald-100',
    dot: 'bg-emerald-400',
  },
  backup_target: {
    border: 'border-teal-500/70',
    bg: 'bg-teal-950/45',
    text: 'text-teal-100',
    dot: 'bg-teal-400',
  },
  backup_source: {
    border: 'border-teal-500/60',
    bg: 'bg-teal-950/35',
    text: 'text-teal-100',
    dot: 'bg-teal-400',
  },
  rescue_stick: {
    border: 'border-orange-500/70',
    bg: 'bg-orange-950/45',
    text: 'text-orange-100',
    dot: 'bg-orange-400',
  },
  default: {
    border: 'border-slate-600/60',
    bg: 'bg-slate-900/60',
    text: 'text-slate-200',
    dot: 'bg-slate-400',
  },
}

const ROLE_ORDER = ['windows_system_disk', 'linux_system_disk', 'mixed_system_disk', 'backup_target', 'rescue_stick', 'other'] as const

function roleSortKey(disk: DiskInfo): number {
  const role = disk.storage_role?.role ?? classifyDiskRole(disk)
  const map: Record<string, number> = {
    windows_system_disk: 0,
    windows_system: 0,
    linux_system_disk: 1,
    mixed_system_disk: 1,
    system: 1,
    backup_target: 2,
    backup_source: 2,
    backup: 2,
    rescue_stick: 3,
    rescue: 3,
  }
  return map[role] ?? 4
}

interface Props {
  disks: DiskInfo[]
  selectedDiskName: string | null
  onSelectDisk: (disk: DiskInfo) => void
  loadState: DiskLoadState
}

const PartitionDeviceSidebar: React.FC<Props> = ({
  disks,
  selectedDiskName,
  onSelectDisk,
  loadState,
}) => {
  const { t, i18n } = useTranslation()
  const lang = i18n.language.startsWith('de') ? 'de' : 'en'

  const sorted = [...disks].sort((a, b) => roleSortKey(a) - roleSortKey(b))

  return (
    <aside
      className={`${TOOL_SHELL.panel} flex flex-col min-h-0 w-full xl:w-64 xl:shrink-0`}
      data-testid="partition-device-sidebar"
    >
      <div className="px-4 py-3 border-b border-slate-700/50">
        <h2 className={TOOL_SHELL.panelHeader}>{t('partitionWorkbench.sidebar.title')}</h2>
        <p className="text-xs text-slate-500 mt-1">{t('partitionWorkbench.sidebar.hint')}</p>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {loadState.kind === 'loading' && (
          <div className="flex items-center gap-2 px-3 py-8 text-slate-400 text-sm justify-center" data-testid="partition-sidebar-loading">
            <Loader2 className="w-5 h-5 animate-spin" />
            {t('partition.scan.loading')}
          </div>
        )}

        {loadState.kind === 'error' && (
          <div
            className="rounded-lg border border-red-500/40 bg-red-950/35 px-3 py-4 text-sm space-y-2"
            data-testid="partition-sidebar-error"
          >
            <p className="font-bold text-red-100 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              {loadState.message}
            </p>
            {loadState.hint && <p className="text-xs text-red-200/80">{loadState.hint}</p>}
          </div>
        )}

        {loadState.kind === 'empty' && (
          <div className="px-3 py-8 text-center text-sm text-slate-500" data-testid="partition-sidebar-empty">
            {t('partitionWorkbench.sidebar.empty')}
          </div>
        )}

        {loadState.kind === 'ok' &&
          sorted.map((disk) => {
            const storageRole = disk.storage_role?.role
            const accent = ROLE_ACCENT[storageRole ?? ''] ?? ROLE_ACCENT.default
            const Icon = deviceIconForKind(inferDeviceIconKind(disk, disk.storage_role))
            const isSelected = selectedDiskName === disk.name
            const label = diskRoleLabel(disk, lang) || t(`partitionManager.cards.role.${classifyDiskRole(disk)}`)
            const badge = roleBadgeForDisk(classifyDiskRole(disk), disk)
            const statusKey =
              badge === 'blocked' ? 'blocked' : badge === 'readonly' ? 'readonly' : badge === 'ok' ? 'ok' : 'review'

            return (
              <button
                key={disk.name}
                type="button"
                onClick={() => onSelectDisk(disk)}
                data-testid={`partition-sidebar-disk-${disk.name}`}
                data-storage-role={storageRole ?? 'fallback'}
                className={`w-full text-left rounded-lg border px-3 py-3 transition-all ${accent.bg} ${
                  isSelected
                    ? `ring-2 ring-offset-2 ring-offset-slate-950 ${accent.border} shadow-lg`
                    : `border-slate-700/40 hover:border-slate-600/70`
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 w-9 h-9 rounded flex items-center justify-center border ${accent.border} ${accent.bg}`}>
                    <Icon className={`w-5 h-5 ${accent.text}`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className={`text-[10px] font-bold uppercase tracking-wider ${accent.text}`}>{label}</p>
                    <p className="text-sm font-semibold text-slate-50 truncate mt-0.5">
                      {disk.model || disk.display_name}
                    </p>
                    <p className={`${TOOL_SHELL.mono} truncate`}>{diskToTargetDevice(disk)}</p>
                    <div className="mt-2 flex items-center gap-1.5">
                      <span className={`w-2 h-2 rounded-full ${accent.dot}`} />
                      <span className="text-[10px] font-semibold text-slate-400 uppercase">
                        {t(`partitionWorkbench.sidebar.status.${statusKey}`)}
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            )
          })}
      </div>
    </aside>
  )
}

export default PartitionDeviceSidebar
