/**
 * PartitionDetailTable – Tabellenansicht wie im UI-Entwurf (read-only).
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { CheckCircle, AlertTriangle, XCircle } from 'lucide-react'
import type { DiskInfo, PartitionInfo } from '../api/partitionApi'
import {
  classifyPartitionVisualRole,
  PARTITION_ROLE_COLORS,
} from '../lib/partition/partitionRoleUtils'
import type { ExperienceLevel } from './Sidebar'

interface Props {
  disk: DiskInfo | null
  selectedPartition: PartitionInfo | null
  onSelectPartition: (part: PartitionInfo) => void
  experienceLevel?: ExperienceLevel
}

function rowStatus(part: PartitionInfo): 'ok' | 'warn' | 'blocked' {
  if (part.is_system_critical) return 'blocked'
  if (part.is_mounted) return 'warn'
  return 'ok'
}

const statusIcon = {
  ok: <CheckCircle className="w-4 h-4 text-emerald-400" />,
  warn: <AlertTriangle className="w-4 h-4 text-amber-400" />,
  blocked: <XCircle className="w-4 h-4 text-red-400" />,
}

const PartitionDetailTable: React.FC<Props> = ({
  disk,
  selectedPartition,
  onSelectPartition,
  experienceLevel = 'beginner',
}) => {
  const { t } = useTranslation()
  const isExpert = experienceLevel === 'advanced' || experienceLevel === 'developer'

  if (!disk) return null

  return (
    <div className="overflow-x-auto rounded-xl border border-slate-700/50" data-testid="partition-detail-table">
      <table className="w-full min-w-[720px] text-left text-xs">
        <thead>
          <tr className="border-b border-slate-700/60 bg-slate-800/60 text-slate-500 uppercase tracking-wide text-[10px]">
            <th className="px-3 py-2.5 font-semibold">{t('partitionManager.table.nr')}</th>
            <th className="px-3 py-2.5 font-semibold">{t('partition.partition.device')}</th>
            <th className="px-3 py-2.5 font-semibold">{t('partition.partition.filesystem')}</th>
            <th className="px-3 py-2.5 font-semibold">{t('partition.partition.size')}</th>
            <th className="px-3 py-2.5 font-semibold">{t('partitionManager.table.usage')}</th>
            <th className="px-3 py-2.5 font-semibold">{t('partition.partition.mountpoint')}</th>
            <th className="px-3 py-2.5 font-semibold">{t('partitionManager.table.function')}</th>
            <th className="px-3 py-2.5 font-semibold">{t('partitionManager.table.status')}</th>
          </tr>
        </thead>
        <tbody>
          {disk.partitions.map((part, index) => {
            const role = classifyPartitionVisualRole(part)
            const st = rowStatus(part)
            const isSelected = selectedPartition?.name === part.name
            return (
              <tr
                key={part.name}
                onClick={() => onSelectPartition(part)}
                className={`cursor-pointer border-b border-slate-800/50 transition-colors ${
                  isSelected ? 'bg-teal-950/30' : index % 2 === 0 ? 'bg-slate-900/20' : 'bg-transparent'
                } hover:bg-slate-800/40`}
                data-testid={`partition-table-row-${part.name}`}
              >
                <td className="px-3 py-2.5 text-slate-400 font-mono">{index + 1}</td>
                <td className="px-3 py-2.5 font-mono text-slate-200">
                  <span className="inline-flex items-center gap-2">
                    <span
                      className="w-2 h-2 rounded-full shrink-0"
                      style={{ background: PARTITION_ROLE_COLORS[role] }}
                    />
                    /dev/{part.name}
                  </span>
                </td>
                <td className="px-3 py-2.5 text-slate-300">{part.fs_info.name}</td>
                <td className="px-3 py-2.5 text-slate-300">{part.size_human}</td>
                <td className="px-3 py-2.5 text-slate-400">
                  {part.is_mounted && part.used_percent > 0
                    ? `${part.used_percent.toFixed(0)}%`
                    : '—'}
                </td>
                <td className="px-3 py-2.5 text-slate-400">{part.mountpoint ?? '—'}</td>
                <td className="px-3 py-2.5 text-slate-300">
                  {t(`partitionManager.layoutPreview.roles.${role === 'other' ? 'other' : role}`)}
                </td>
                <td className="px-3 py-2.5">
                  <span className="inline-flex items-center gap-1.5">
                    {statusIcon[st]}
                    <span className="text-slate-400">{t(`partitionManager.table.status.${st}`)}</span>
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      {isExpert && selectedPartition?.uuid && (
        <p className="px-3 py-2 text-[10px] font-mono text-slate-600 border-t border-slate-800/50">
          UUID {selectedPartition.uuid}
        </p>
      )}
    </div>
  )
}

export default PartitionDetailTable
