import React, { useCallback, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { RefreshCw } from 'lucide-react'
import { fetchApi } from '../../api'
import { toneClass } from '../../pages/devDashboardFilters'

type UpdateStatus = {
  status?: string
  local_version?: string | null
  workspace_head?: string | null
  runtime_head?: string | null
  deploy_required?: boolean
  update_available?: string
  automatic_update_allowed?: boolean
  package_manager_update_allowed?: boolean
  next_action?: string
}

export function UpdateStatusCard({ refreshSec = 30 }: { refreshSec?: number }) {
  const { t } = useTranslation()
  const [data, setData] = useState<UpdateStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const load = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await fetchApi('/api/dev-dashboard/update/status')
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      const body = (await res.json()) as UpdateStatus
      setData(body)
    } catch {
      setError('fetch_failed')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
    const id = window.setInterval(() => void load(), Math.max(10, refreshSec) * 1000)
    return () => window.clearInterval(id)
  }, [load, refreshSec])

  const tone =
    data?.status === 'ok'
      ? 'green'
      : data?.status === 'deploy_required'
        ? 'yellow'
        : data?.status === 'blocked'
          ? 'red'
          : 'gray'

  return (
    <section className={`rounded-xl border p-4 space-y-2 ${toneClass(tone)}`} data-testid="update-status-card">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-white">{t('devDashboard.update.title')}</h2>
          <p className="text-xs text-slate-400">{t('devDashboard.update.subtitle')}</p>
        </div>
        <button type="button" className="btn-secondary inline-flex items-center gap-1 text-xs" onClick={() => void load()} disabled={loading}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          {t('backup.ui.refresh')}
        </button>
      </div>

      {error ? <p className="text-xs text-rose-200">{error}</p> : null}

      <div className="grid sm:grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-200">
        <div>
          <span className="text-slate-400">{t('devDashboard.update.status')}</span>
          <div className="font-mono text-slate-100">{String(data?.status || 'unknown')}</div>
        </div>
        <div>
          <span className="text-slate-400">{t('devDashboard.update.localVersion')}</span>
          <div className="font-mono text-slate-100">{String(data?.local_version || '—')}</div>
        </div>
        <div>
          <span className="text-slate-400">{t('devDashboard.update.workspaceHead')}</span>
          <div className="font-mono text-slate-100 break-all">{String(data?.workspace_head || '—')}</div>
        </div>
        <div>
          <span className="text-slate-400">{t('devDashboard.update.runtimeHead')}</span>
          <div className="font-mono text-slate-100 break-all">{String(data?.runtime_head || '—')}</div>
        </div>
        <div>
          <span className="text-slate-400">{t('devDashboard.update.deployRequired')}</span>
          <div className="font-mono text-slate-100">{data?.deploy_required ? 'true' : 'false'}</div>
        </div>
        <div>
          <span className="text-slate-400">{t('devDashboard.update.remoteAvailability')}</span>
          <div className="font-mono text-slate-100">{String(data?.update_available || 'unknown')}</div>
        </div>
        <div>
          <span className="text-slate-400">{t('devDashboard.update.automaticUpdateAllowed')}</span>
          <div className="font-mono text-slate-100">{String(Boolean(data?.automatic_update_allowed))}</div>
        </div>
        <div>
          <span className="text-slate-400">{t('devDashboard.update.packageManagerAllowed')}</span>
          <div className="font-mono text-slate-100">{String(Boolean(data?.package_manager_update_allowed))}</div>
        </div>
      </div>

      <p className="text-xs text-slate-300">
        {t('devDashboard.update.nextAction')}: <span className="font-mono">{String(data?.next_action || 'none')}</span>
      </p>
    </section>
  )
}
