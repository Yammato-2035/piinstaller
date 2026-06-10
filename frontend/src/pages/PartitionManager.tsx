/**
 * PartitionManager.tsx – Partitionshelfer Phase 2.3 (Mockup-Alignment, read-only).
 */

import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { RefreshCw, Info } from 'lucide-react'
import toast from 'react-hot-toast'
import PageHeader from '../components/layout/PageHeader'
import { PandaHelperStrip } from '../components/companions'
import type { ExperienceLevel } from '../components/Sidebar'
import PartitionSectionHeader from '../components/PartitionSectionHeader'
import PartitionOverviewCards from '../components/PartitionOverviewCards'
import PartitionGraphicLayout from '../components/PartitionGraphicLayout'
import PartitionDetailTable from '../components/PartitionDetailTable'
import PartitionSafetyStatusPanel from '../components/PartitionSafetyStatusPanel'
import PartitionHardstopPanel from '../components/PartitionHardstopPanel'
import PartitionRestorePreviewPanel from '../components/PartitionRestorePreviewPanel'
import PartitionPageDevStrip from '../components/PartitionPageDevStrip'
import { MOCKUP_SECTION } from '../lib/partition/partitionMockupTheme'
import { diskToTargetDevice } from '../lib/partition/partitionRoleUtils'
import {
  fetchDisks,
  fetchManifestLayoutPreview,
  fetchPartitionHardstopPreview,
  fetchRestoreHandoffPreview,
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
  const [selectedDisk, setSelectedDisk] = useState<DiskInfo | null>(null)
  const [selectedPartition, setSelectedPartition] = useState<PartitionInfo | null>(null)
  const [hardstopPreview, setHardstopPreview] = useState<HardstopPreviewResult | null>(null)
  const [manifestPreview, setManifestPreview] = useState<ManifestLayoutPreviewResult | null>(null)
  const [restoreHandoff, setRestoreHandoff] = useState<RestoreHandoffPreviewResult | null>(null)
  const [safetyLoading, setSafetyLoading] = useState(false)
  const [safetyError, setSafetyError] = useState<string | null>(null)
  const [manifestPathInput, setManifestPathInput] = useState('')

  const selectedDevice = selectedDisk ? diskToTargetDevice(selectedDisk) : null

  const loadDisks = useCallback(async () => {
    setLoading(true)
    try {
      const r = await fetchDisks()
      setDisks(r.disks)
      setSelectedDisk((prev) => {
        if (!prev) return null
        return r.disks.find((d) => d.name === prev.name) ?? null
      })
    } catch {
      toast.error(t('partition.scan.error'))
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    loadDisks()
  }, [loadDisks])

  const handleSelectDisk = (disk: DiskInfo) => {
    setSelectedDisk(disk)
    setSelectedPartition(disk.partitions[0] ?? null)
  }

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
        manifest_path: manifestPathInput.trim() || null,
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
  }, [selectedDevice, manifestPathInput, t])

  useEffect(() => {
    loadSafetyPreview()
  }, [loadSafetyPreview])

  const handleRestorePreviewRefresh = async () => {
    await loadSafetyPreview()
    toast.success(t('partitionManager.restorePreviewStarted'))
  }

  const safetyChecksOk = !safetyError && !!hardstopPreview
  const pandaText = selectedDisk
    ? t('partitionManager.panda.selected', { name: selectedDisk.display_name })
    : t('partitionManager.panda.intro')

  return (
    <div className="flex flex-col h-full min-h-0 gap-6 animate-fade-in" data-testid="partition-manager-page">
      <PageHeader
        visualStyle="hero-card"
        tone="backup"
        title={t('partitionManager.page.title')}
        subtitle={t('partitionManager.page.subtitle')}
      />

      <div className="flex flex-wrap items-center gap-3 -mt-1">
        <button
          type="button"
          onClick={loadDisks}
          disabled={loading}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-slate-700/60 hover:bg-slate-700 text-slate-100 text-sm font-bold transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {t('partition.scan.button')}
        </button>
      </div>

      <PandaHelperStrip experienceLevel={experienceLevel} variant="backup">
        {pandaText}
      </PandaHelperStrip>

      <div
        className="grid grid-cols-1 xl:grid-cols-12 gap-6 flex-1 min-h-0"
        data-testid="partition-manager-three-column"
      >
        <div className="xl:col-span-4 space-y-4 overflow-y-auto min-w-0">
          <PartitionSectionHeader
            step={1}
            title={t('partitionManager.sections.selectDisk')}
            subtitle={t('partitionManager.sections.selectDiskHint')}
          />
          <PartitionOverviewCards
            disks={disks}
            selectedDiskName={selectedDisk?.name ?? null}
            onSelectDisk={handleSelectDisk}
            loading={loading}
          />
        </div>

        <div className="xl:col-span-5 space-y-5 overflow-y-auto min-w-0">
          <section className={`${MOCKUP_SECTION} space-y-5`}>
            <PartitionSectionHeader
              step={2}
              title={
                selectedDisk
                  ? t('partitionManager.sections.partitionsOn', { name: selectedDisk.display_name })
                  : t('partitionManager.sections.partitionsEmpty')
              }
            />
            <PartitionGraphicLayout
              disk={selectedDisk}
              selectedPartition={selectedPartition}
              onSelectPartition={setSelectedPartition}
              experienceLevel={experienceLevel}
            />
            <div className="border-t border-slate-700/40 pt-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-3">
                {t('partitionManager.sections.detailTable')}
              </p>
              <PartitionDetailTable
                disk={selectedDisk}
                selectedPartition={selectedPartition}
                onSelectPartition={setSelectedPartition}
                experienceLevel={experienceLevel}
              />
            </div>

            {selectedDevice && (
              <div className="max-w-xl pt-1">
                <label className="block text-[11px] text-slate-500 mb-1" htmlFor="manifest-path-input">
                  {t('partition.phase2.manifestPathLabel')}
                </label>
                <input
                  id="manifest-path-input"
                  type="text"
                  value={manifestPathInput}
                  onChange={(e) => setManifestPathInput(e.target.value)}
                  placeholder="/media/…/MANIFEST.json"
                  className="w-full text-xs font-mono rounded-lg border border-slate-600/60 bg-slate-900/60 px-3 py-2 text-slate-300"
                />
              </div>
            )}

            <div className="flex items-start gap-3 rounded-xl border border-sky-500/30 bg-sky-950/20 px-4 py-3 text-sm text-sky-100">
              <Info className="w-5 h-5 shrink-0 mt-0.5" />
              <span>{t('partitionManager.readOnlyInfo')}</span>
            </div>
          </section>

          <PartitionHardstopPanel
            hardstops={hardstopPreview?.evaluation?.hardstops ?? []}
            warnings={hardstopPreview?.evaluation?.warnings ?? []}
          />
        </div>

        <div className="xl:col-span-3 min-w-0">
          <PartitionSafetyStatusPanel
            selectedDevice={selectedDevice}
            hardstopPreview={hardstopPreview}
            manifestLayoutPreview={manifestPreview}
            restoreHandoffPreview={restoreHandoff}
            loading={safetyLoading}
            error={safetyError}
            onRefresh={loadSafetyPreview}
          />
        </div>
      </div>

      {selectedDevice && (
        <PartitionRestorePreviewPanel
          restoreHandoff={restoreHandoff}
          manifestLayout={manifestPreview}
          loading={safetyLoading}
          onRefresh={handleRestorePreviewRefresh}
        />
      )}

      <PartitionPageDevStrip safetyChecksOk={safetyChecksOk} />
    </div>
  )
}

export default PartitionManager
