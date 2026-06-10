/**
 * Expertenmodus – technische Details aufklappbar (read-only).
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronDown, ChevronUp, Cpu } from 'lucide-react'
import type { DiskInfo, PartitionInfo } from '../../api/partitionApi'
import PartitionDetailTable from '../PartitionDetailTable'
import { TOOL_SHELL } from '../../lib/theme/setuphelferToolTheme'
import type { ExperienceLevel } from '../Sidebar'

interface Props {
  disk: DiskInfo | null
  selectedPartition: PartitionInfo | null
  onSelectPartition: (part: PartitionInfo) => void
  experienceLevel: ExperienceLevel
  manifestPathInput: string
  onManifestPathChange: (value: string) => void
  expanded: boolean
  onToggle: () => void
}

const PartitionExpertModePanel: React.FC<Props> = ({
  disk,
  selectedPartition,
  onSelectPartition,
  experienceLevel,
  manifestPathInput,
  onManifestPathChange,
  expanded,
  onToggle,
}) => {
  const { t } = useTranslation()
  const isExpert = experienceLevel === 'advanced' || experienceLevel === 'developer'

  return (
    <section className={`${TOOL_SHELL.panel} overflow-hidden`} data-testid="partition-expert-mode-panel">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left hover:bg-slate-800/50 transition-colors"
        data-testid="partition-expert-mode-toggle"
      >
        <span className="flex items-center gap-2 text-sm font-bold text-slate-300 uppercase tracking-wide">
          <Cpu className="w-4 h-4 text-slate-500" />
          {t('partitionManager.sections.showTechnicalDetails')}
        </span>
        {expanded ? <ChevronUp className="w-4 h-4 text-slate-500" /> : <ChevronDown className="w-4 h-4 text-slate-500" />}
      </button>

      {expanded && (
        <div className="border-t border-slate-700/50 px-4 py-4 space-y-4" data-testid="partition-expert-mode-content">
          {disk ? (
            <>
              <PartitionDetailTable
                disk={disk}
                selectedPartition={selectedPartition}
                onSelectPartition={onSelectPartition}
                experienceLevel={isExpert ? experienceLevel : 'advanced'}
              />
              {disk.storage_role && (
                <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
                  <div className="rounded border border-slate-700/50 bg-slate-950/50 px-3 py-2">
                    <p className="text-slate-500 uppercase tracking-wider text-[10px]">{t('partitionWorkbench.expert.transport')}</p>
                    <p className="font-mono text-slate-300 mt-1">{disk.storage_role.transport ?? disk.tran ?? '—'}</p>
                  </div>
                  <div className="rounded border border-slate-700/50 bg-slate-950/50 px-3 py-2">
                    <p className="text-slate-500 uppercase tracking-wider text-[10px]">{t('partitionWorkbench.expert.confidence')}</p>
                    <p className="font-mono text-slate-300 mt-1">{disk.storage_role.confidence}</p>
                  </div>
                  <div className="rounded border border-slate-700/50 bg-slate-950/50 px-3 py-2">
                    <p className="text-slate-500 uppercase tracking-wider text-[10px]">{t('partitionWorkbench.expert.source')}</p>
                    <p className="font-mono text-slate-300 mt-1">{disk.storage_role.classification_source ?? '—'}</p>
                  </div>
                </div>
              )}
              {disk.storage_role?.evidence && disk.storage_role.evidence.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-slate-400 mb-1">{t('partitionManager.sections.evidence')}</p>
                  <ul className="list-disc list-inside space-y-0.5 font-mono text-xs text-slate-500">
                    {disk.storage_role.evidence.map((e) => (
                      <li key={e}>{e}</li>
                    ))}
                  </ul>
                </div>
              )}
              <div className="max-w-xl">
                <label className="block text-[11px] text-slate-500 mb-1" htmlFor="workbench-manifest-path">
                  {t('partition.phase2.manifestPathLabel')}
                </label>
                <input
                  id="workbench-manifest-path"
                  type="text"
                  value={manifestPathInput}
                  onChange={(e) => onManifestPathChange(e.target.value)}
                  placeholder="/media/…/MANIFEST.json"
                  className="w-full text-xs font-mono rounded border border-slate-600/60 bg-slate-950/60 px-3 py-2 text-slate-300"
                />
              </div>
            </>
          ) : (
            <p className="text-sm text-slate-500">{t('partitionWorkbench.expert.selectDisk')}</p>
          )}
        </div>
      )}
    </section>
  )
}

export default PartitionExpertModePanel
