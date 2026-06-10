/**
 * PartitionGraphicLayout – grafische Partitionsleiste (Phase 2.3 Mockup, read-only).
 */

import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { DiskInfo, PartitionInfo } from '../api/partitionApi'
import {
  classifyPartitionVisualRole,
  PARTITION_ROLE_COLORS,
  type PartitionVisualRole,
} from '../lib/partition/partitionRoleUtils'
import type { ExperienceLevel } from './Sidebar'

interface Props {
  disk: DiskInfo | null
  selectedPartition: PartitionInfo | null
  onSelectPartition: (part: PartitionInfo) => void
  experienceLevel?: ExperienceLevel
}

function roleLabelKey(role: PartitionVisualRole, part: PartitionInfo): string {
  if (role === 'efi') return 'partitionManager.layoutPreview.roles.efi'
  if (role === 'root') return 'partitionManager.layoutPreview.roles.root'
  if (role === 'home') return 'partitionManager.layoutPreview.roles.home'
  if (role === 'swap') return 'partitionManager.layoutPreview.roles.swap'
  if (part.fstype === 'ntfs') return 'partitionManager.layoutPreview.roles.data'
  return 'partitionManager.layoutPreview.roles.other'
}

const PartitionGraphicLayout: React.FC<Props> = ({
  disk,
  selectedPartition,
  onSelectPartition,
  experienceLevel = 'beginner',
}) => {
  const { t } = useTranslation()
  const [hovered, setHovered] = useState<PartitionInfo | null>(null)
  const isExpert = experienceLevel === 'advanced' || experienceLevel === 'developer'

  if (!disk) {
    return (
      <div
        className="rounded-2xl border border-dashed border-slate-700/50 p-12 text-center text-base text-slate-500"
        data-testid="partition-graphic-empty"
      >
        {t('partitionManager.layoutPreview.selectDisk')}
      </div>
    )
  }

  const parts = disk.partitions
  const total = disk.size_bytes || 1
  const activePart = hovered ?? selectedPartition

  return (
    <section className="space-y-5" data-testid="partition-graphic-layout">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <h3 className="text-lg font-bold text-slate-100">{t('partitionManager.layoutPreview.title')}</h3>
        {isExpert && (
          <span className="text-[11px] text-slate-500 font-mono">/dev/{disk.name}</span>
        )}
      </div>

      <div
        className="flex h-28 sm:h-32 lg:h-36 rounded-2xl overflow-hidden border-2 border-slate-600/50 shadow-inner"
        role="img"
        aria-label={t('partitionManager.layoutPreview.title')}
      >
        {parts.map((part) => {
          const share = part.size_bytes / total
          const role = classifyPartitionVisualRole(part)
          const color = PARTITION_ROLE_COLORS[role]
          const isSelected = selectedPartition?.name === part.name
          const isHovered = hovered?.name === part.name
          return (
            <button
              key={part.name}
              type="button"
              onClick={() => onSelectPartition(part)}
              onMouseEnter={() => setHovered(part)}
              onMouseLeave={() => setHovered(null)}
              style={{
                flex: share,
                background: color,
                minWidth: share < 0.03 ? 12 : 0,
                opacity: isSelected || isHovered ? 1 : 0.82,
                outline: isSelected ? '4px solid #38bdf8' : isHovered ? '3px solid #f8fafc' : 'none',
                outlineOffset: '-4px',
              }}
              className="relative flex flex-col items-center justify-center overflow-hidden transition-all duration-150 focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-400"
              data-testid={`partition-graphic-segment-${part.name}`}
              title={t(roleLabelKey(role, part))}
            >
              {share > 0.04 && (
                <>
                  <span className="text-white font-black text-xs sm:text-sm lg:text-base drop-shadow-md truncate px-1 uppercase tracking-wide">
                    {t(roleLabelKey(role, part))}
                  </span>
                  <span className="text-white/90 text-[10px] sm:text-xs font-semibold mt-0.5">
                    {part.size_human}
                  </span>
                </>
              )}
              {part.is_mounted && part.used_percent > 0 && (
                <div
                  className="absolute bottom-0 left-0 h-2 bg-black/45"
                  style={{ width: `${part.used_percent}%` }}
                />
              )}
            </button>
          )
        })}
      </div>

      {activePart && (
        <div
          className="rounded-xl border border-sky-500/35 bg-sky-950/25 px-4 py-3 flex flex-wrap gap-x-6 gap-y-1 text-sm"
          data-testid="partition-graphic-hover-detail"
        >
          <span className="font-bold text-sky-100">
            {t(roleLabelKey(classifyPartitionVisualRole(activePart), activePart))}
          </span>
          <span className="text-slate-300">
            {t('partition.partition.size')}: <strong>{activePart.size_human}</strong>
          </span>
          {activePart.fstype && (
            <span className="text-slate-300">
              FS: <strong>{activePart.fstype}</strong>
            </span>
          )}
          {activePart.is_mounted && activePart.used_percent > 0 && (
            <span className="text-slate-300">
              {t('partition.partition.used')}: <strong>{activePart.used_percent}%</strong>
            </span>
          )}
          {isExpert && activePart.mountpoint && (
            <span className="text-[11px] font-mono text-slate-500 w-full">{activePart.mountpoint}</span>
          )}
        </div>
      )}
    </section>
  )
}

export default PartitionGraphicLayout
