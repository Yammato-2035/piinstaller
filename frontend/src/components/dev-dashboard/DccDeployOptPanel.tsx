import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ArrowRight, Server } from 'lucide-react'
import { fetchApi } from '../../api'
import { fetchDccApi } from '../../lib/devDashboard/dccDeveloperToken'
import { buildProfileMeta } from '../../config/buildProfile'
import { toneClass } from '../../pages/devDashboardFilters'

type DeployOptSnapshot = {
  runtimeVersion: string
  runtimePath: string
  deployStatus: string
  workspaceHead: string
  driftStatus: string
  driftFiles: string[]
  manifestMatch: boolean | null
  deployMessage: string | null
  tokenRequired: boolean
}

type Props = {
  workspaceVersion?: string
  deployDrift?: Record<string, unknown> | null
  onOpenOperations?: () => void
}

const OPT_RUNTIME = '/opt/setuphelfer'

function workspaceVersionLabel(): string {
  if (typeof __APP_VERSION__ !== 'undefined' && String(__APP_VERSION__).trim()) {
    return String(__APP_VERSION__).trim()
  }
  return buildProfileMeta.project_version ?? 'unknown'
}

export function DccDeployOptPanel({ workspaceVersion, deployDrift, onOpenOperations }: Props) {
  const { t } = useTranslation()
  const [snap, setSnap] = useState<DeployOptSnapshot | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    const wsVer = workspaceVersion || workspaceVersionLabel()
    let runtimeVersion = '—'
    let runtimePath = OPT_RUNTIME
    try {
      const vr = await fetchApi('/api/version', { cache: 'no-store' })
      if (vr.ok) {
        const body = (await vr.json()) as Record<string, unknown>
        runtimeVersion = String(body.project_version || body.version || '—')
        runtimePath = String(body.backend_runtime_path || OPT_RUNTIME).replace(/\/backend$/, '')
      }
    } catch {
      /* ignore */
    }

    let deployStatus = 'unknown'
    let workspaceHead = '—'
    let deployMessage: string | null = null
    let tokenRequired = false
    const driftStatus = String(deployDrift?.status || 'unknown')
    const driftFiles = Array.isArray(deployDrift?.files) ? (deployDrift?.files as string[]) : []
    const manifestMatch =
      deployDrift?.manifest_match === true ? true : deployDrift?.manifest_match === false ? false : null

    try {
      const dr = await fetchDccApi('/api/dev-dashboard/deploy/status', { cache: 'no-store' })
      if (dr.ok) {
        const body = (await dr.json()) as Record<string, unknown>
        deployStatus = String(body.status || 'unknown')
        workspaceHead = String(body.workspace_head || '—')
        deployMessage = body.message ? String(body.message) : null
        const dd = (body.deploy_drift as Record<string, unknown>) || {}
        if (dd.status) deployStatus = String(body.status || deployStatus)
      } else {
        const err = (await dr.json().catch(() => ({}))) as Record<string, unknown>
        if (err.code === 'DEVELOPER_CAPABILITY_REQUIRED') tokenRequired = true
        deployMessage = String(err.code || `HTTP ${dr.status}`)
      }
    } catch {
      deployMessage = 'fetch_failed'
    }

    setSnap({
      runtimeVersion,
      runtimePath,
      deployStatus,
      workspaceHead,
      driftStatus,
      driftFiles,
      manifestMatch,
      deployMessage,
      tokenRequired,
    })
    setLoading(false)
  }, [deployDrift, workspaceVersion])

  useEffect(() => {
    void load()
  }, [load])

  const wsVer = workspaceVersion || workspaceVersionLabel()
  const uiStale =
    snap != null && wsVer !== 'unknown' && snap.runtimeVersion !== '—' && wsVer !== snap.runtimeVersion
  const tone = uiStale ? 'yellow' : snap?.driftStatus === 'green' ? 'green' : 'gray'

  return (
    <section
      className={`rounded-xl border p-4 mb-4 ${toneClass(tone)}`}
      data-testid="dcc-deploy-opt-panel"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold text-white flex items-center gap-2">
            <Server size={16} aria-hidden />
            {t('devDashboard.vis.deployOpt.title')}
          </h2>
          <p className="text-xs text-slate-400 mt-1">{t('devDashboard.vis.deployOpt.subtitle')}</p>
        </div>
        {uiStale ? (
          <span className="text-[10px] uppercase tracking-wide font-semibold text-amber-200 border border-amber-600/50 rounded px-2 py-1" data-testid="dcc-deploy-ui-stale">
            {t('devDashboard.vis.deployOpt.uiStale')}
          </span>
        ) : null}
      </div>

      {loading ? (
        <p className="text-xs text-slate-400 mt-3">{t('devDashboard.controlCenter.loading')}</p>
      ) : snap ? (
        <div className="mt-3 grid gap-3 md:grid-cols-2 text-xs">
          <div className="rounded-lg border border-slate-700/60 bg-slate-950/40 p-3 space-y-2">
            <div className="flex justify-between gap-2">
              <span className="text-slate-500">{t('devDashboard.vis.deployOpt.workspaceVersion')}</span>
              <span className="font-mono text-white" data-testid="dcc-deploy-workspace-version">{wsVer}</span>
            </div>
            <div className="flex justify-between gap-2">
              <span className="text-slate-500">{t('devDashboard.vis.deployOpt.runtimeVersion')}</span>
              <span className="font-mono text-slate-200" data-testid="dcc-deploy-runtime-version">{snap.runtimeVersion}</span>
            </div>
            <div className="flex justify-between gap-2">
              <span className="text-slate-500">{t('devDashboard.vis.deployOpt.runtimePath')}</span>
              <span className="font-mono text-slate-200">{snap.runtimePath}</span>
            </div>
            <div className="flex justify-between gap-2">
              <span className="text-slate-500">{t('devDashboard.vis.deployOpt.workspaceHead')}</span>
              <span className="font-mono text-slate-300">{snap.workspaceHead}</span>
            </div>
          </div>
          <div className="rounded-lg border border-slate-700/60 bg-slate-950/40 p-3 space-y-2">
            <div className="flex justify-between gap-2">
              <span className="text-slate-500">{t('devDashboard.vis.deployOpt.driftStatus')}</span>
              <span className="font-mono text-slate-200" data-testid="dcc-deploy-drift-status">{snap.driftStatus}</span>
            </div>
            <div className="flex justify-between gap-2">
              <span className="text-slate-500">{t('devDashboard.vis.deployOpt.deployStatus')}</span>
              <span className="font-mono text-slate-200">{snap.deployStatus}</span>
            </div>
            <div className="flex justify-between gap-2">
              <span className="text-slate-500">{t('devDashboard.vis.deployOpt.manifestMatch')}</span>
              <span className="font-mono text-slate-200">
                {snap.manifestMatch === true ? 'true' : snap.manifestMatch === false ? 'false' : '—'}
              </span>
            </div>
            {snap.driftFiles.length > 0 ? (
              <p className="text-[11px] text-slate-400 break-all">
                {t('devDashboard.vis.deployOpt.driftFiles')}: {snap.driftFiles.slice(0, 5).join(', ')}
                {snap.driftFiles.length > 5 ? '…' : ''}
              </p>
            ) : null}
          </div>
        </div>
      ) : null}

      {uiStale ? (
        <p className="mt-3 text-xs text-amber-100/90 rounded border border-amber-700/40 bg-amber-950/20 px-3 py-2" data-testid="dcc-deploy-opt-hint">
          {t('devDashboard.vis.deployOpt.staleHint', { workspace: wsVer, runtime: snap?.runtimeVersion || '—' })}
        </p>
      ) : null}

      {snap?.tokenRequired ? (
        <p className="mt-2 text-xs text-violet-200">{t('devDashboard.vis.deployOpt.tokenRequired')}</p>
      ) : null}

      <div className="mt-3 flex flex-wrap gap-2">
        <button type="button" className="rounded border border-slate-600 px-3 py-1.5 text-xs text-slate-200 hover:bg-slate-800/60" onClick={() => void load()}>
          {t('backup.ui.refresh')}
        </button>
        {onOpenOperations ? (
          <button
            type="button"
            className="rounded bg-violet-800/80 px-3 py-1.5 text-xs text-white inline-flex items-center gap-1"
            onClick={onOpenOperations}
            data-testid="dcc-deploy-open-operations"
          >
            {t('devDashboard.vis.deployOpt.openDeploy')}
            <ArrowRight size={12} />
          </button>
        ) : null}
      </div>

      <p className="mt-2 text-[11px] text-slate-500 font-mono">{t('devDashboard.vis.deployOpt.commandHint')}</p>
    </section>
  )
}
