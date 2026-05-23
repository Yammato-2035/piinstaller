/**
 * DiskVisualizer.tsx – Grafische Balkenansicht + Partitionstabelle.
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { HardDrive } from 'lucide-react'
import type { DiskInfo, PartitionInfo } from '../../api/partitionApi'
import { getFarbe } from '../../api/partitionApi'

interface DiskVisualizerProps {
  disks: DiskInfo[]
  selectedPartition: PartitionInfo | null
  onSelect: (partition: PartitionInfo) => void
}

const DiskVisualizer: React.FC<DiskVisualizerProps> = ({ disks, selectedPartition, onSelect }) => {
  const { t } = useTranslation()
  if (disks.length === 0) {
    return <div className="text-center py-12 text-slate-500 text-sm">{t('partition.scan.loading')}</div>
  }
  return (
    <div className="space-y-1">
      {disks.map((disk) => (
        <DiskCard key={disk.name} disk={disk} selectedPartition={selectedPartition} onSelect={onSelect} />
      ))}
    </div>
  )
}

const DiskCard: React.FC<{
  disk: DiskInfo
  selectedPartition: PartitionInfo | null
  onSelect: (p: PartitionInfo) => void
}> = ({ disk, selectedPartition, onSelect }) => {
  const { t } = useTranslation()
  return (
    <div className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-4">
      <div className="flex items-center gap-3 mb-3">
        <div className="w-8 h-8 rounded-lg bg-slate-700/60 flex items-center justify-center shrink-0">
          <HardDrive className="w-4 h-4 text-slate-400" />
        </div>
        <div className="min-w-0">
          <div className="font-semibold text-slate-200 text-sm truncate">{disk.display_name}</div>
          <div className="text-xs text-slate-500">
            {t('partition.disk.totalSize')}: {disk.size_human} · {disk.partitions.length}{' '}
            {t('partition.disk.partitions')}
          </div>
        </div>
      </div>

      <div className="flex h-14 rounded-lg overflow-hidden border border-slate-700/50 mb-3 cursor-pointer">
        {disk.partitions.map((part) => {
          const anteil = part.size_bytes / (disk.size_bytes || 1)
          const isSelected = selectedPartition?.name === part.name
          const farbe = getFarbe(part.fstype)
          return (
            <div
              key={part.name}
              onClick={() => onSelect(part)}
              title={`${part.name} – ${part.size_human} (${part.fs_info.name})`}
              style={{
                flex: anteil,
                background: farbe,
                minWidth: anteil < 0.02 ? 8 : 0,
                opacity: isSelected ? 1 : 0.72,
                outline: isSelected ? '2px solid #00D4AA' : 'none',
                outlineOffset: '-2px',
                position: 'relative',
                transition: 'opacity 0.15s',
              }}
              className="flex flex-col items-center justify-center overflow-hidden hover:opacity-90"
            >
              {anteil > 0.06 && (
                <>
                  <span className="text-white font-bold text-[10px] drop-shadow">{part.name}</span>
                  <span className="text-white/80 text-[9px]">{part.size_human}</span>
                </>
              )}
              {part.is_mounted && part.used_percent > 0 && (
                <div
                  style={{
                    position: 'absolute',
                    bottom: 0,
                    left: 0,
                    width: `${part.used_percent}%`,
                    height: 4,
                    background: 'rgba(0,0,0,0.35)',
                  }}
                />
              )}
              {part.is_system_critical && (
                <span className="absolute top-1 right-1 text-yellow-300 text-[9px]">⚠</span>
              )}
            </div>
          )
        })}
      </div>

      <div className="grid grid-cols-5 text-[10px] text-slate-500 px-1 pb-1 border-b border-slate-700/40 mb-1">
        <span>{t('partition.partition.device')}</span>
        <span>{t('partition.partition.size')}</span>
        <span>{t('partition.partition.filesystem')}</span>
        <span>{t('partition.partition.mountpoint')}</span>
        <span>Status</span>
      </div>
      {disk.partitions.map((part, i) => {
        const isSelected = selectedPartition?.name === part.name
        const farbe = getFarbe(part.fstype)
        const badge = part.is_system_critical
          ? { text: t('partition.partition.status.system'), cls: 'text-orange-400' }
          : part.is_mounted
            ? { text: t('partition.partition.status.active'), cls: 'text-emerald-400' }
            : { text: t('partition.partition.status.inactive'), cls: 'text-slate-500' }
        return (
          <div
            key={part.name}
            onClick={() => onSelect(part)}
            className={`grid grid-cols-5 items-center px-1 py-1.5 rounded cursor-pointer text-xs transition-colors ${
              isSelected
                ? 'bg-teal-500/10 border border-teal-500/30'
                : i % 2 === 0
                  ? 'bg-slate-700/20'
                  : 'bg-transparent'
            } hover:bg-slate-700/40`}
          >
            <span className="flex items-center gap-1.5 font-semibold text-slate-200">
              <span style={{ color: farbe }} className="text-[8px]">
                ●
              </span>
              {part.name}
            </span>
            <span className="text-slate-400">{part.size_human}</span>
            <span className="text-slate-400">{part.fs_info.name}</span>
            <span className="text-slate-400 truncate">{part.mountpoint ?? '–'}</span>
            <span className={`text-[10px] font-bold ${badge.cls}`}>{badge.text}</span>
          </div>
        )
      })}
    </div>
  )
}

export default DiskVisualizer
