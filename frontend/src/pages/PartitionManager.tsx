/**
 * PartitionManager.tsx – Partitionshelfer im Setuphelfer-Frontend.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { HardDrive, RefreshCw, Compass } from 'lucide-react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
import PageHeader from '../components/layout/PageHeader'
import { PandaHelperStrip } from '../components/companions'
import type { ExperienceLevel } from '../components/Sidebar'
import DiskVisualizer from '../components/partition/DiskVisualizer'
import PartitionDetailPanel from '../components/partition/PartitionDetailPanel'
import PartitionWizardModal from '../components/partition/PartitionWizardModal'
import ActionQueueBar from '../components/partition/ActionQueueBar'
import PartitionSafetyPreviewPanel from '../components/partition/PartitionSafetyPreviewPanel'
import {
  fetchDisks,
  fetchManifestLayoutPreview,
  fetchPartitionHardstopPreview,
  fetchRestoreHandoffPreview,
  partitionNameToDevice,
  type DiskInfo,
  type HardstopPreviewResult,
  type ManifestLayoutPreviewResult,
  type PartitionInfo,
  type RestoreHandoffPreviewResult,
} from '../api/partitionApi'

interface Props {
  experienceLevel?: ExperienceLevel
}

const PartitionManager: React.FC<Props> = ({ experienceLevel = 'beginner' }) => {
  const { t } = useTranslation()
  const [disks, setDisks] = useState<DiskInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [selected, setSelected] = useState<PartitionInfo | null>(null)
  const [wizardOpen, setWizardOpen] = useState(false)
  const [hardstopPreview, setHardstopPreview] = useState<HardstopPreviewResult | null>(null)
  const [manifestPreview, setManifestPreview] = useState<ManifestLayoutPreviewResult | null>(null)
  const [restoreHandoff, setRestoreHandoff] = useState<RestoreHandoffPreviewResult | null>(null)
  const [safetyLoading, setSafetyLoading] = useState(false)
  const [safetyError, setSafetyError] = useState<string | null>(null)

  const selectedDevice = selected ? partitionNameToDevice(selected.name) : null

  const loadDisks = useCallback(async () => {
    setLoading(true)
    try {
      const r = await fetchDisks()
      setDisks(r.disks)
    } catch {
      toast.error(t('partition.scan.error'))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    loadDisks()
  }, [loadDisks])

  const loadSafetyPreview = useCallback(async () => {
    if (!selectedDevice) {
      setHardstopPreview(null)
      setManifestPreview(null)
      setRestoreHandoff(null)
      setSafetyError(null)
      return
    }
    setSafetyLoading(true)
    setSafetyError(null)
    try {
      const hardstop = await fetchPartitionHardstopPreview(selectedDevice)
      setHardstopPreview(hardstop)
      const manifest = await fetchManifestLayoutPreview({
        manifest: null,
        target_device: selectedDevice,
      })
      setManifestPreview(manifest)
      const handoff = await fetchRestoreHandoffPreview({
        target_device: selectedDevice,
        hardstop_result: hardstop.evaluation,
        manifest_layout_preview: manifest,
      })
      setRestoreHandoff(handoff)
    } catch (e) {
      setHardstopPreview(null)
      setManifestPreview(null)
      setRestoreHandoff(null)
      setSafetyError(e instanceof Error ? e.message : t('partition.phase2.error'))
    } finally {
      setSafetyLoading(false)
    }
  }, [selectedDevice, t])

  useEffect(() => {
    loadSafetyPreview()
  }, [loadSafetyPreview])

  const pandaText = selected?.is_system_critical
    ? 'Diese Partition gehört zu deinem laufenden System – bitte sehr vorsichtig sein.'
    : selected?.is_mounted
      ? `Diese Partition ist aktiv eingehängt unter ${selected.mountpoint}.`
      : selected
        ? 'Diese Partition kann sicher bearbeitet werden (Schreibaktionen folgen in Phase 2).'
        : t('partition.panda.helper')

  const isBeginner = experienceLevel === 'beginner'

  return (
    <div className="flex flex-col h-full min-h-0 space-y-4 animate-fade-in">
      <PageHeader
        visualStyle="hero-card"
        tone="backup"
        title={t('partition.page.title')}
        subtitle={t('partition.page.subtitle')}
      />

      <div className="flex flex-wrap items-center gap-2 -mt-2">
        <button
          type="button"
          onClick={() => setWizardOpen(true)}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-teal-500 hover:bg-teal-400 text-slate-900 text-sm font-semibold transition-colors"
        >
          <Compass className="w-4 h-4" />
          {t('partition.wizard.title')}
        </button>
        <button
          type="button"
          onClick={loadDisks}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-700/60 hover:bg-slate-700 text-slate-300 text-sm transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          {t('partition.scan.button')}
        </button>
      </div>

      {isBeginner && (
        <div className="rounded-xl border border-sky-500/35 bg-slate-900/50 p-4 space-y-2">
          <p className="text-sm font-semibold text-slate-100 flex items-center gap-2">
            <HardDrive className="w-4 h-4 text-teal-400" />
            {t('partition.page.title')}
          </p>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">{t('partition.beginner.intro')}</p>
        </div>
      )}

      <PandaHelperStrip experienceLevel={experienceLevel} variant="backup">
        {pandaText}
      </PandaHelperStrip>

      <div className="flex flex-1 min-h-0 rounded-xl border border-slate-700/50 overflow-hidden bg-slate-900/30">
        <div className="flex-1 overflow-y-auto min-w-0 p-4 space-y-3">
          {loading ? (
            <div className="space-y-3 animate-pulse">
              {[1, 2].map((i) => (
                <div key={i} className="bg-slate-800/60 rounded-xl border border-slate-700/50 p-4 h-48" />
              ))}
            </div>
          ) : (
            <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }}>
              <DiskVisualizer disks={disks} selectedPartition={selected} onSelect={setSelected} />
            </motion.div>
          )}
        </div>

        <div className="w-72 shrink-0 border-l border-slate-700/50 bg-slate-800/30 flex flex-col min-h-0">
          <div className="px-3 pt-3 pb-2 border-b border-slate-700/40">
            <span className="text-xs font-semibold text-teal-400">
              {selected ? `/dev/${selected.name}` : 'Details'}
            </span>
          </div>
          <div className="flex-1 min-h-0">
            <PartitionDetailPanel partition={selected} experienceLevel={experienceLevel} />
          </div>
        </div>
      </div>

      <PartitionSafetyPreviewPanel
        selectedDevice={selectedDevice}
        hardstopPreview={hardstopPreview}
        manifestLayoutPreview={manifestPreview}
        restoreHandoffPreview={restoreHandoff}
        loading={safetyLoading}
        error={safetyError}
        onRefreshSafetyPreview={loadSafetyPreview}
      />

      <ActionQueueBar onApplied={loadDisks} />
      {wizardOpen && <PartitionWizardModal onClose={() => setWizardOpen(false)} />}
    </div>
  )
}

export default PartitionManager
