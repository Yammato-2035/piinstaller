/**
 * PartitionManager.tsx – Partitionshelfer Workbench (read-only).
 */

import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { RefreshCw, Info } from 'lucide-react'
import toast from 'react-hot-toast'
import type { ExperienceLevel } from '../components/Sidebar'
import PartitionWorkbenchShell from '../components/partitions/PartitionWorkbenchShell'
import PartitionDeviceSidebar, { type DiskLoadState } from '../components/partitions/PartitionDeviceSidebar'
import PartitionGraphicLayout from '../components/PartitionGraphicLayout'
import PartitionSafetyStatusPanel from '../components/PartitionSafetyStatusPanel'
import PartitionHardstopCenter from '../components/partitions/PartitionHardstopCenter'
import PartitionRestorePreviewPanel from '../components/PartitionRestorePreviewPanel'
import PartitionExpertModePanel from '../components/partitions/PartitionExpertModePanel'
import PartitionPageDevStrip from '../components/PartitionPageDevStrip'
import { TOOL_SHELL } from '../lib/theme/setuphelferToolTheme'
import { diskToTargetDevice } from '../lib/partition/partitionRoleUtils'
import { API_BASE_STORAGE_KEY, getApiBase } from '../api'
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

function describeLoadError(err: unknown, t: (k: string, o?: Record<string, string>) => string): DiskLoadState {
  const apiBase = getApiBase() || t('partitionWorkbench.load.apiDefault')
  if (err instanceof DOMException && err.name === 'AbortError') {
    return {
      kind: 'error',
      message: t('partitionWorkbench.load.timeout'),
      hint: t('partitionWorkbench.load.apiHint', { base: apiBase }),
    }
  }
  const msg = err instanceof Error ? err.message : String(err)
  if (msg.includes('404')) {
    return {
      kind: 'error',
      message: t('partitionWorkbench.load.wrongEndpoint'),
      hint: t('partitionWorkbench.load.apiHint', { base: apiBase }),
    }
  }
  return {
    kind: 'error',
    message: t('partitionWorkbench.load.backendUnreachable'),
    hint: t('partitionWorkbench.load.apiHint', { base: apiBase }),
  }
}

const PartitionManager: React.FC<Props> = ({ experienceLevel = 'beginner' }) => {
  const { t } = useTranslation()
  const [disks, setDisks] = useState<DiskInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [loadState, setLoadState] = useState<DiskLoadState>({ kind: 'loading' })
  const [selectedDisk, setSelectedDisk] = useState<DiskInfo | null>(null)
  const [selectedPartition, setSelectedPartition] = useState<PartitionInfo | null>(null)
  const [hardstopPreview, setHardstopPreview] = useState<HardstopPreviewResult | null>(null)
  const [manifestPreview, setManifestPreview] = useState<ManifestLayoutPreviewResult | null>(null)
  const [restoreHandoff, setRestoreHandoff] = useState<RestoreHandoffPreviewResult | null>(null)
  const [safetyLoading, setSafetyLoading] = useState(false)
  const [safetyError, setSafetyError] = useState<string | null>(null)
  const [manifestPathInput, setManifestPathInput] = useState('')
  const [showTechnicalDetails, setShowTechnicalDetails] = useState(false)

  const selectedDevice = selectedDisk ? diskToTargetDevice(selectedDisk) : null

  const loadDisks = useCallback(async () => {
    setLoading(true)
    setLoadState({ kind: 'loading' })
    try {
      const r = await fetchDisks()
      if (!r.disks || r.disks.length === 0) {
        setDisks([])
        setSelectedDisk(null)
        setSelectedPartition(null)
        const storedBase =
          typeof localStorage !== 'undefined' ? localStorage.getItem(API_BASE_STORAGE_KEY) : null
        if (storedBase) {
          setLoadState({
            kind: 'error',
            message: t('partitionWorkbench.load.emptyResponse'),
            hint: t('partitionWorkbench.load.staleApiBase'),
          })
        } else {
          setLoadState({ kind: 'empty' })
        }
        return
      }
      setDisks(r.disks)
      setLoadState({ kind: 'ok' })
      setSelectedDisk((prev) => {
        if (prev) {
          const updated = r.disks.find((d) => d.name === prev.name)
          if (updated) return updated
        }
        const first = r.disks[0]
        setSelectedPartition(first.partitions[0] ?? null)
        return first
      })
    } catch (err) {
      setDisks([])
      setSelectedDisk(null)
      setSelectedPartition(null)
      const state = describeLoadError(err, t)
      setLoadState(state)
      toast.error(state.kind === 'error' ? state.message : t('partition.scan.error'))
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
    setShowTechnicalDetails(false)
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

  const sidebarLoadState: DiskLoadState = useMemo(() => {
    if (loading) return { kind: 'loading' }
    return loadState
  }, [loading, loadState])

  return (
    <PartitionWorkbenchShell>
      <div className="flex flex-col min-h-0 gap-4 h-full" data-testid="partition-manager-page">
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={loadDisks}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded border border-slate-600/60 bg-slate-800 hover:bg-slate-700 text-slate-100 text-sm font-semibold transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            {t('partition.scan.button')}
          </button>
        </div>

        <div
          className="flex flex-col xl:flex-row gap-4 flex-1 min-h-0"
          data-testid="partition-workbench-layout"
        >
          <PartitionDeviceSidebar
            disks={disks}
            selectedDiskName={selectedDisk?.name ?? null}
            onSelectDisk={handleSelectDisk}
            loadState={sidebarLoadState}
          />

          <div className="flex-1 min-w-0 flex flex-col gap-4 overflow-y-auto">
            <section className={`${TOOL_SHELL.panel} p-4 sm:p-5 space-y-5`}>
              <PartitionGraphicLayout
                disk={selectedDisk}
                selectedPartition={selectedPartition}
                onSelectPartition={setSelectedPartition}
                experienceLevel={experienceLevel}
              />
              <div className="flex items-start gap-3 rounded border border-sky-600/30 bg-sky-950/25 px-4 py-3 text-sm text-sky-100">
                <Info className="w-5 h-5 shrink-0 mt-0.5" />
                <span>{t('partitionManager.readOnlyInfo')}</span>
              </div>
            </section>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <PartitionSafetyStatusPanel
                selectedDevice={selectedDevice}
                hardstopPreview={hardstopPreview}
                manifestLayoutPreview={manifestPreview}
                restoreHandoffPreview={restoreHandoff}
                loading={safetyLoading}
                error={safetyError}
                onRefresh={loadSafetyPreview}
              />
              <PartitionHardstopCenter
                disk={selectedDisk}
                hardstops={hardstopPreview?.evaluation?.hardstops ?? []}
                warnings={hardstopPreview?.evaluation?.warnings ?? []}
              />
            </div>

            {selectedDevice && (
              <PartitionRestorePreviewPanel
                restoreHandoff={restoreHandoff}
                manifestLayout={manifestPreview}
                loading={safetyLoading}
                onRefresh={handleRestorePreviewRefresh}
              />
            )}
          </div>
        </div>

        <PartitionExpertModePanel
          disk={selectedDisk}
          selectedPartition={selectedPartition}
          onSelectPartition={setSelectedPartition}
          experienceLevel={experienceLevel}
          manifestPathInput={manifestPathInput}
          onManifestPathChange={setManifestPathInput}
          expanded={showTechnicalDetails}
          onToggle={() => setShowTechnicalDetails((v) => !v)}
        />

        <PartitionPageDevStrip safetyChecksOk={safetyChecksOk} />
      </div>
    </PartitionWorkbenchShell>
  )
}

export default PartitionManager
