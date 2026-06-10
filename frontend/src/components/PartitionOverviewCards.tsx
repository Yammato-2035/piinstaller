/**
 * PartitionOverviewCards – Datenträgerkarten (Phase 2.3 Mockup, read-only).
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { HardDrive, ShieldAlert, ShieldCheck, LifeBuoy, Lock } from 'lucide-react'
import type { DiskInfo } from '../api/partitionApi'
import {
  classifyDiskRole,
  detectOsHint,
  roleBadgeForDisk,
  type DiskRole,
} from '../lib/partition/partitionRoleUtils'
import { MOCKUP_DISK_ROLE, MOCKUP_STATUS } from '../lib/partition/partitionMockupTheme'

interface Props {
  disks: DiskInfo[]
  selectedDiskName: string | null
  onSelectDisk: (disk: DiskInfo) => void
  loading?: boolean
}

const ROLE_ORDER: DiskRole[] = ['system', 'backup', 'rescue', 'other']

const badgeTone: Record<string, keyof typeof MOCKUP_STATUS> = {
  ok: 'safe',
  warning: 'review',
  blocked: 'blocked',
  readonly: 'info',
}

const roleIcons: Record<DiskRole, React.ReactNode> = {
  system: <ShieldAlert className="w-9 h-9" />,
  backup: <ShieldCheck className="w-9 h-9" />,
  rescue: <LifeBuoy className="w-9 h-9" />,
  other: <HardDrive className="w-9 h-9" />,
}

const PartitionOverviewCards: React.FC<Props> = ({
  disks,
  selectedDiskName,
  onSelectDisk,
  loading = false,
}) => {
  const { t } = useTranslation()

  if (loading) {
    return (
      <div className="grid gap-4" data-testid="partition-overview-cards-loading">
        {[1, 2].map((i) => (
          <div key={i} className="h-52 rounded-2xl border border-slate-700/50 bg-slate-800/40 animate-pulse" />
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
      <div
        className="rounded-2xl border border-slate-700/50 bg-slate-900/40 p-10 text-center text-slate-500"
        data-testid="partition-overview-cards-empty"
      >
        {t('partitionManager.cards.empty')}
      </div>
    )
  }

  return (
    <div className="grid gap-4" data-testid="partition-overview-cards">
      {sorted.map((disk) => {
        const role = classifyDiskRole(disk)
        const badge = roleBadgeForDisk(role, disk)
        const osHint = detectOsHint(disk)
        const isSelected = selectedDiskName === disk.name
        const theme = MOCKUP_DISK_ROLE[role]
        const tone = badgeTone[badge] ?? 'info'

        return (
          <article
            key={disk.name}
            data-testid={`partition-disk-card-${disk.name}`}
            data-disk-role={role}
            className={`rounded-2xl border p-5 sm:p-6 flex flex-col gap-4 min-h-[200px] transition-all duration-200 ${
              isSelected ? theme.selected : `${theme.shell} hover:border-slate-500/60`
            }`}
          >
            <div className="flex items-start gap-4">
              <div
                className={`w-16 h-16 rounded-2xl flex items-center justify-center shrink-0 ${theme.iconWrap} ${theme.icon}`}
              >
                {roleIcons[role]}
              </div>
              <div className="min-w-0 flex-1 space-y-1">
                <p className={`text-xs font-bold uppercase tracking-[0.14em] ${theme.label}`}>
                  {t(`partitionManager.cards.role.${role}`)}
                </p>
                <h3 className="text-xl sm:text-2xl font-black text-slate-50 truncate leading-tight">
                  {disk.display_name}
                </h3>
                <p className="text-base font-semibold text-slate-300">{disk.size_human}</p>
              </div>
            </div>

            {osHint && (
              <p className="text-sm text-slate-400 font-medium">
                {t(`partitionManager.cards.osHint.${osHint}`)}
              </p>
            )}

            <span
              className={`inline-flex items-center gap-2 self-start text-sm font-bold px-3 py-1.5 rounded-xl border ${MOCKUP_STATUS[tone].pill}`}
            >
              {badge === 'blocked' && <ShieldAlert className="w-4 h-4 shrink-0" />}
              {badge === 'readonly' && <Lock className="w-4 h-4 shrink-0" />}
              {t(`partitionManager.cards.badge.${badge}`)}
            </span>

            <button
              type="button"
              onClick={() => onSelectDisk(disk)}
              className="mt-auto w-full py-3.5 rounded-xl bg-slate-700/80 hover:bg-slate-600 text-slate-50 text-sm font-bold tracking-wide transition-colors"
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
