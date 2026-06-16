/**
 * PartitionsDashboardCard – Dev-Dashboard-Kachel für Partitions Phase 2.1.
 */

import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { HardDrive, RefreshCw } from 'lucide-react'
import {
  fetchDisks,
  fetchManifestLayoutPreview,
  fetchPartitionHardstopPreview,
  fetchRestoreHandoffPreview,
  type HardstopPreviewResult,
  type ManifestLayoutPreviewResult,
  type RestoreHandoffPreviewResult,
} from '../../api/partitionApi'
import { diskToTargetDevice } from '../../lib/partition/partitionRoleUtils'
import { toneClass } from '../../pages/devDashboardFilters'

type CheckState = 'ok' | 'warn' | 'fail' | 'pending'

type PartitionDashState = {
  overall: string
  checks: Record<string, CheckState>
  diskCount: number
  error: string | null
}

function worstTone(checks: Record<string, CheckState>): string {
  const vals = Object.values(checks)
  if (vals.includes('fail')) return 'red'
  if (vals.includes('warn') || vals.includes('pending')) return 'yellow'
  return 'green'
}

export function PartitionsDashboardCard({ refreshSec = 30 }: { refreshSec?: number }) {
  const { t } = useTranslation()
  const [state, setState] = useState<PartitionDashState>({
    overall: 'gray',
    checks: {
      devices: 'pending',
      smart: 'pending',
      hardstops: 'pending',
      layout: 'pending',
      handoff: 'pending',
    },
    diskCount: 0,
    error: null,
  })
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    const checks: Record<string, CheckState> = {
      devices: 'fail',
      smart: 'warn',
      hardstops: 'warn',
      layout: 'warn',
      handoff: 'warn',
    }
    let diskCount = 0
    let error: string | null = null

    try {
      const scan = await fetchDisks()
      diskCount = scan.disks.length
      checks.devices = diskCount > 0 ? 'ok' : 'fail'

      const targetDisk = scan.disks[0]
      if (!targetDisk) {
        setState({ overall: worstTone(checks), checks, diskCount, error: null })
        return
      }

      const target = diskToTargetDevice(targetDisk)
      let hardstop: HardstopPreviewResult | null = null
      let manifest: ManifestLayoutPreviewResult | null = null
      let handoff: RestoreHandoffPreviewResult | null = null

      try {
        hardstop = await fetchPartitionHardstopPreview(target)
        const smart = String(hardstop.context?.smart_status ?? 'missing')
        checks.smart = smart === 'ok' ? 'ok' : smart === 'warning' || smart === 'unknown' ? 'warn' : 'fail'
        checks.hardstops = (hardstop.evaluation?.hardstops.length ?? 0) > 0 ? 'fail' : 'ok'
      } catch (e) {
        checks.smart = 'fail'
        checks.hardstops = 'fail'
        error = e instanceof Error ? e.message : t('partition.phase2.error')
      }

      try {
        manifest = await fetchManifestLayoutPreview({ manifest: null, target_device: target })
        checks.layout =
          manifest.status === 'ok' ? 'ok' : manifest.status === 'unavailable' ? 'warn' : 'fail'
      } catch {
        checks.layout = 'fail'
      }

      try {
        handoff = await fetchRestoreHandoffPreview({
          target_device: target,
          hardstop_result: hardstop?.evaluation ?? null,
          manifest_layout_preview: manifest,
        })
        checks.handoff =
          handoff.status === 'ready' ? 'ok' : handoff.status === 'review_required' ? 'warn' : 'fail'
      } catch {
        checks.handoff = 'fail'
      }
    } catch (e) {
      error = e instanceof Error ? e.message : t('partition.scan.error')
      checks.devices = 'fail'
    }

    setState({
      overall: worstTone(checks),
      checks,
      diskCount,
      error,
    })
    setLoading(false)
  }, [t])

  useEffect(() => {
    load()
    const id = window.setInterval(load, refreshSec * 1000)
    return () => window.clearInterval(id)
  }, [load, refreshSec])

  const checkIcon = (s: CheckState) => {
    if (s === 'ok') return '✓'
    if (s === 'warn') return '⚠'
    if (s === 'fail') return '✖'
    return '…'
  }

  return (
    <div
      className={`rounded-xl border p-4 ${toneClass(state.overall)}`}
      data-testid="partitions-dashboard-card"
    >
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-2">
          <HardDrive className="w-5 h-5 opacity-80" />
          <span className="text-xs font-bold uppercase tracking-wide">{t('partitionManager.devDashboard.title')}</span>
        </div>
        <button
          type="button"
          onClick={() => load()}
          disabled={loading}
          className="p-1.5 rounded-md hover:bg-black/20 disabled:opacity-50"
          aria-label={t('backup.ui.refresh')}
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      <p className="text-lg font-bold mb-3" data-testid="partitions-dashboard-overall">
        {t(`partitionManager.devDashboard.overall.${state.overall}`)}
      </p>

      <ul className="space-y-1 text-xs">
        {(['devices', 'smart', 'hardstops', 'layout', 'handoff'] as const).map((key) => (
          <li key={key} className="flex items-center gap-2" data-testid={`partitions-dash-check-${key}`}>
            <span className="w-4 text-center font-bold">{checkIcon(state.checks[key])}</span>
            <span>{t(`partitionManager.devDashboard.checks.${key}`)}</span>
            {key === 'devices' && state.diskCount > 0 && (
              <span className="text-slate-500 ml-auto">({state.diskCount})</span>
            )}
          </li>
        ))}
      </ul>

      {state.error && (
        <p className="text-[11px] text-red-300 mt-2 truncate" title={state.error}>
          {state.error}
        </p>
      )}
    </div>
  )
}
