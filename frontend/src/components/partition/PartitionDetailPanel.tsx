/**
 * PartitionDetailPanel.tsx – Detailpanel (rechte Seite).
 */

import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Info, Shield, AlertTriangle } from 'lucide-react'
import RiskWarningCard from '../RiskWarningCard'
import type { PartitionInfo, SafetyWarning } from '../../api/partitionApi'
import { fetchSafetyCheck, getRiskLevel } from '../../api/partitionApi'
import type { ExperienceLevel } from '../Sidebar'

interface Props {
  partition: PartitionInfo | null
  experienceLevel?: ExperienceLevel
}

const PartitionDetailPanel: React.FC<Props> = ({ partition, experienceLevel = 'beginner' }) => {
  const { t } = useTranslation()
  const [warnings, setWarnings] = useState<SafetyWarning[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!partition) return
    setLoading(true)
    fetchSafetyCheck(partition.name, 'delete')
      .then((r) => setWarnings(r.warnungen))
      .catch(() => setWarnings([]))
      .finally(() => setLoading(false))
  }, [partition?.name])

  if (!partition) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-slate-500 text-sm px-6 text-center gap-2">
        <Info className="w-8 h-8 opacity-30" />
        <span>{t('partition.beginner.clickHint')}</span>
      </div>
    )
  }

  const infoRows: Array<[string, string] | null> = [
    [t('partition.partition.device'), `/dev/${partition.name}`],
    [t('partition.partition.size'), partition.size_human],
    [t('partition.partition.filesystem'), partition.fs_info.name],
    partition.mountpoint ? [t('partition.partition.mountpoint'), partition.mountpoint] : null,
    partition.label ? [t('partition.partition.label'), partition.label] : null,
    experienceLevel !== 'beginner' && partition.uuid
      ? [t('partition.partition.uuid'), `${partition.uuid.slice(0, 18)}...`]
      : null,
  ]

  return (
    <div className="h-full overflow-y-auto">
      <div className="px-4 pt-4 pb-3 border-b border-slate-700/50">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-teal-400 font-bold text-sm">/dev/{partition.name}</span>
          {partition.label && (
            <span className="text-xs text-slate-400 bg-slate-700/50 px-1.5 py-0.5 rounded">{partition.label}</span>
          )}
        </div>
        <div className="text-xs text-slate-500">
          {partition.fs_info.name} · {partition.size_human}
        </div>
      </div>

      <div className="px-4 py-3 space-y-4">
        <div className="space-y-1.5">
          {infoRows.filter(Boolean).map((row) => {
            const [label, value] = row as [string, string]
            return (
              <div key={label} className="flex gap-2 text-xs">
                <span className="text-slate-500 w-28 shrink-0">{label}:</span>
                <span className="text-slate-200 font-medium truncate">{value}</span>
              </div>
            )
          })}
        </div>

        {partition.is_mounted && partition.used_percent > 0 && (
          <div>
            <div className="flex justify-between text-xs text-slate-400 mb-1.5">
              <span>
                {t('partition.partition.used')}: {partition.used_human}
              </span>
              <span>
                {t('partition.partition.free')}: {partition.free_human}
              </span>
            </div>
            <div className="h-2 rounded-full bg-slate-700/50 overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${partition.used_percent}%`,
                  background:
                    partition.used_percent < 70
                      ? '#4CAF50'
                      : partition.used_percent < 90
                        ? '#FF9800'
                        : '#F44336',
                }}
              />
            </div>
            <div className="text-right text-[10px] text-slate-500 mt-0.5">
              {partition.used_percent.toFixed(0)}%
            </div>
          </div>
        )}

        <div>
          <div className="flex items-center gap-1.5 text-teal-400 text-xs font-semibold mb-2">
            <Info className="w-3.5 h-3.5" /> Was ist das?
          </div>
          <p className="text-xs text-slate-400 leading-relaxed">{partition.fs_info.beschreibung}</p>
          <p className="text-xs text-teal-400/80 italic mt-1">💡 {partition.fs_info.empfehlung}</p>
        </div>

        <div>
          <div className="flex items-center gap-1.5 text-teal-400 text-xs font-semibold mb-2">
            <Shield className="w-3.5 h-3.5" /> {t('partition.safety.title')}
          </div>
          {loading ? (
            <div className="text-xs text-slate-500 animate-pulse">Analysiere...</div>
          ) : (
            <div className="space-y-2">
              {warnings.map((w, i) => (
                <RiskWarningCard key={i} level={getRiskLevel(w.stufe)} title={w.titel}>
                  <span className="block text-xs">{w.erklaerung}</span>
                  <span className="block text-xs mt-1 text-slate-300 italic">→ {w.empfehlung}</span>
                  {w.blockiert && (
                    <span className="inline-flex items-center gap-1 mt-1.5 text-[10px] font-semibold text-red-400 bg-red-500/10 border border-red-500/20 px-1.5 py-0.5 rounded">
                      🛑 {t('partition.safety.blocked')}
                    </span>
                  )}
                </RiskWarningCard>
              ))}
            </div>
          )}
        </div>

        <div>
          <div className="flex items-center gap-1.5 text-teal-400 text-xs font-semibold mb-2">
            <AlertTriangle className="w-3.5 h-3.5" /> Aktionen
          </div>
          <div className="space-y-1.5">
            {(['delete', 'resize', 'format'] as const).map((action) => (
              <button
                key={action}
                type="button"
                disabled
                className="w-full flex justify-between items-center bg-slate-700/30 border border-slate-700/40 rounded-lg px-3 py-2 text-xs text-slate-500 cursor-not-allowed"
              >
                <span>{t(`partition.actions.${action}`)}</span>
                <span className="text-[10px] text-slate-600">{t('partition.actions.comingSoon')}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default PartitionDetailPanel
