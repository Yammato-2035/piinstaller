import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ClipboardCopy, RefreshCw, ShieldCheck } from 'lucide-react'
import { fetchApi } from '../../api'
import { toneClass } from '../../pages/devDashboardFilters'

type DeployState = {
  status?: string
  code?: string
  generated_at?: string
  workspace?: string
  runtime_path?: string
  workspace_head?: string | null
  workspace_branch?: string | null
  workspace_dirty_count?: number | null
  message?: string
  errors?: string[]
  runtime_gate?: {
    exit_code?: number | null
    status?: string
    summary?: string
  }
  deploy_drift?: {
    status?: string
    raw_status?: string
    files?: string[]
    suggested_actions?: string[]
    manifest_match?: boolean | null
  }
  last_job?: {
    id?: string | null
    started_at?: string | null
    ended_at?: string | null
    exit_code?: number | null
    status?: string
    log_tail?: string[]
  }
  helper?: {
    systemd_unit_present?: boolean
    can_start_without_password?: boolean | string
    requires_operator_setup?: boolean
  }
  next_action?: {
    type?: string
    label?: string
    commands?: string[]
  }
  operator_setup?: {
    commands?: string[]
    warnings?: string[]
  }
}

type DeployLogsResponse = {
  lines?: string[]
}

type OperatorSetupResponse = {
  commands?: string[]
  warnings?: string[]
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-3 text-xs">
      <span className="text-slate-400">{label}</span>
      <span className="text-right font-mono text-slate-100 break-all">{value}</span>
    </div>
  )
}

export function DeployStatusPanel({ refreshSec = 15 }: { refreshSec?: number }) {
  const { t } = useTranslation()
  const [data, setData] = useState<DeployState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [logsOpen, setLogsOpen] = useState(false)
  const [logs, setLogs] = useState<string[]>([])
  const [setupCommands, setSetupCommands] = useState<string[]>([])
  const [setupWarnings, setSetupWarnings] = useState<string[]>([])
  const [copyState, setCopyState] = useState<string | null>(null)
  const [requestResult, setRequestResult] = useState<string | null>(null)

  const loadStatus = useCallback(async () => {
    try {
      setError(null)
      const res = await fetchApi('/api/dev-dashboard/deploy/status')
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      const body = (await res.json()) as DeployState
      setData(body)
    } catch {
      setError('fetch_failed')
    }
  }, [])

  useEffect(() => {
    void loadStatus()
    const id = window.setInterval(() => void loadStatus(), Math.max(5, refreshSec) * 1000)
    return () => window.clearInterval(id)
  }, [loadStatus, refreshSec])

  const loadLogs = useCallback(async () => {
    try {
      setBusy('logs')
      const res = await fetchApi('/api/dev-dashboard/deploy/logs')
      const body = (await res.json()) as DeployLogsResponse
      setLogs(body.lines || [])
      setLogsOpen(true)
    } catch {
      setLogs([])
      setLogsOpen(true)
    } finally {
      setBusy(null)
    }
  }, [])

  const loadSetupCommands = useCallback(async () => {
    try {
      setBusy('setup')
      const res = await fetchApi('/api/dev-dashboard/deploy/operator-setup-commands', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: '{}',
      })
      const body = (await res.json()) as OperatorSetupResponse
      setSetupCommands(body.commands || [])
      setSetupWarnings(body.warnings || [])
    } catch {
      setSetupCommands([])
      setSetupWarnings([])
    } finally {
      setBusy(null)
    }
  }, [])

  const requestDeploy = useCallback(async () => {
    const confirmed = window.confirm(
      'Ich bestaetige den kontrollierten Deploy nach /opt/setuphelfer. Keine Backup-/Restore-/USB-Aktion wird ausgefuehrt.',
    )
    if (!confirmed) return
    try {
      setBusy('deploy')
      setRequestResult(null)
      const res = await fetchApi('/api/dev-dashboard/deploy/request', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ operator_confirm: true }),
      })
      const body = (await res.json()) as DeployState
      if (body.operator_setup?.commands?.length) {
        setSetupCommands(body.operator_setup.commands)
        setSetupWarnings(body.operator_setup.warnings || [])
      }
      setRequestResult([body.status, body.code, body.message].filter(Boolean).join(' · '))
      await loadStatus()
      if (logsOpen) {
        await loadLogs()
      }
    } catch {
      setRequestResult('deploy_request_failed')
    } finally {
      setBusy(null)
    }
  }, [loadLogs, loadStatus, logsOpen])

  const copyCommands = useCallback(async () => {
    if (!setupCommands.length || !navigator.clipboard) return
    try {
      await navigator.clipboard.writeText(setupCommands.join('\n'))
      setCopyState('copied')
      window.setTimeout(() => setCopyState(null), 1600)
    } catch {
      setCopyState('failed')
      window.setTimeout(() => setCopyState(null), 1600)
    }
  }, [setupCommands])

  const overall = String(data?.status || 'gray')
  const driftFiles = data?.deploy_drift?.files || []
  const helper = data?.helper || {}
  const lastJobLogs = data?.last_job?.log_tail || []
  const shownLogs = logsOpen ? logs : lastJobLogs
  const canStart = String(helper.can_start_without_password ?? 'unknown')
  const buttonClass =
    'rounded-md border border-slate-700 bg-slate-900/70 px-2.5 py-1.5 text-xs text-slate-100 hover:border-slate-500 disabled:opacity-50 disabled:cursor-not-allowed'
  const sectionClass = 'rounded-lg border border-slate-700/70 bg-slate-950/30 p-3 space-y-2'
  const manifestMatch =
    data?.deploy_drift?.manifest_match === true
      ? 'true'
      : data?.deploy_drift?.manifest_match === false
        ? 'false'
        : 'unknown'
  const suggestedActions = useMemo(() => data?.deploy_drift?.suggested_actions || [], [data?.deploy_drift?.suggested_actions])

  return (
    <section className={`rounded-xl border p-4 space-y-3 ${toneClass(overall)}`} data-testid="deploy-status-panel">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <ShieldCheck size={18} className="shrink-0" />
            {t('devDashboard.deployHelper.title')}
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">{t('devDashboard.deployHelper.subtitle')}</p>
        </div>
        <span className="text-xs uppercase tracking-wide font-mono">{overall}</span>
      </div>

      {error ? <p className="text-xs text-rose-200">{error}</p> : null}
      {requestResult ? <p className="text-xs text-sky-100">{requestResult}</p> : null}
      {data?.message ? <p className="text-xs text-slate-300">{data.message}</p> : null}

      <div className="flex flex-wrap gap-2">
        <button type="button" className={buttonClass} onClick={() => void loadStatus()} disabled={busy !== null}>
          <RefreshCw size={14} className={busy === 'refresh' ? 'animate-spin' : ''} />
          {t('devDashboard.deployHelper.refreshStatus')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void loadLogs()} disabled={busy !== null}>
          {t('devDashboard.deployHelper.showLogs')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void loadSetupCommands()} disabled={busy !== null}>
          {t('devDashboard.deployHelper.showOperatorSetup')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void requestDeploy()} disabled={busy !== null}>
          {t('devDashboard.deployHelper.requestDeploy')}
        </button>
      </div>

      <div className="grid lg:grid-cols-2 gap-3">
        <div className={sectionClass}>
          <p className="text-xs font-semibold text-slate-100">{t('devDashboard.deployHelper.overview')}</p>
          <InfoRow label={t('devDashboard.deployHelper.runtimeGate')} value={String(data?.runtime_gate?.status || 'unknown')} />
          <InfoRow label={t('devDashboard.deployHelper.runtimeGateExit')} value={String(data?.runtime_gate?.exit_code ?? '—')} />
          <InfoRow label={t('devDashboard.deployHelper.workspaceHead')} value={String(data?.workspace_head || '—')} />
          <InfoRow label={t('devDashboard.deployHelper.runtimePath')} value={String(data?.runtime_path || '—')} />
          <InfoRow label={t('devDashboard.deployHelper.manifestMatch')} value={manifestMatch} />
        </div>

        <div className={sectionClass}>
          <p className="text-xs font-semibold text-slate-100">{t('devDashboard.deployHelper.helperState')}</p>
          <InfoRow
            label={t('devDashboard.deployHelper.helperInstalled')}
            value={helper.systemd_unit_present ? t('devDashboard.deployHelper.yes') : t('devDashboard.deployHelper.no')}
          />
          <InfoRow label={t('devDashboard.deployHelper.operatorSetupNeeded')} value={helper.requires_operator_setup ? t('devDashboard.deployHelper.yes') : t('devDashboard.deployHelper.no')} />
          <InfoRow label={t('devDashboard.deployHelper.passwordlessStart')} value={canStart} />
          <InfoRow label={t('devDashboard.deployHelper.nextStep')} value={String(data?.next_action?.label || '—')} />
          <InfoRow label={t('devDashboard.deployHelper.workspaceDirtyCount')} value={String(data?.workspace_dirty_count ?? '—')} />
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-3">
        <div className={sectionClass}>
          <p className="text-xs font-semibold text-slate-100">{t('devDashboard.deployHelper.deployDrift')}</p>
          <InfoRow label={t('devDashboard.deployHelper.deployDriftStatus')} value={String(data?.deploy_drift?.status || 'unknown')} />
          <div className="text-xs">
            <div className="font-semibold text-slate-200 mb-1">{t('devDashboard.deployHelper.affectedFiles')}</div>
            <div className="text-slate-300 break-all">{driftFiles.length ? driftFiles.join(', ') : '—'}</div>
          </div>
          <div className="text-xs">
            <div className="font-semibold text-slate-200 mb-1">{t('devDashboard.deployHelper.suggestedActions')}</div>
            <div className="text-slate-300 break-all">{suggestedActions.length ? suggestedActions.join(', ') : '—'}</div>
          </div>
        </div>

        <div className={sectionClass}>
          <p className="text-xs font-semibold text-slate-100">{t('devDashboard.deployHelper.lastJob')}</p>
          <InfoRow label="id" value={String(data?.last_job?.id || '—')} />
          <InfoRow label={t('devDashboard.deployHelper.lastStatus')} value={String(data?.last_job?.status || '—')} />
          <InfoRow label={t('devDashboard.deployHelper.lastExitCode')} value={String(data?.last_job?.exit_code ?? '—')} />
          <InfoRow label={t('devDashboard.deployHelper.startedAt')} value={String(data?.last_job?.started_at || '—')} />
          <InfoRow label={t('devDashboard.deployHelper.endedAt')} value={String(data?.last_job?.ended_at || '—')} />
        </div>
      </div>

      {(setupCommands.length > 0 || setupWarnings.length > 0) && (
        <div className={sectionClass}>
          <div className="flex items-center justify-between gap-3">
            <p className="text-xs font-semibold text-slate-100">{t('devDashboard.deployHelper.operatorSetupCommands')}</p>
            <button type="button" className={buttonClass} onClick={() => void copyCommands()} disabled={!setupCommands.length}>
              <ClipboardCopy size={14} />
              {copyState === 'copied'
                ? t('devDashboard.deployHelper.copied')
                : copyState === 'failed'
                  ? t('devDashboard.deployHelper.copyFailed')
                  : t('devDashboard.deployHelper.copyCommands')}
            </button>
          </div>
          {setupWarnings.length > 0 ? (
            <ul className="list-disc pl-4 text-xs text-amber-100/90">
              {setupWarnings.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : null}
          {setupCommands.length > 0 ? (
            <pre className="overflow-x-auto rounded-md border border-slate-800 bg-slate-950/70 p-3 text-xs text-slate-200 whitespace-pre-wrap">
              {setupCommands.join('\n')}
            </pre>
          ) : null}
        </div>
      )}

      <div className={sectionClass}>
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-semibold text-slate-100">{t('devDashboard.deployHelper.logs')}</p>
          <button
            type="button"
            className={buttonClass}
            onClick={() => {
              if (logsOpen) {
                setLogsOpen(false)
                return
              }
              void loadLogs()
            }}
            disabled={busy !== null}
          >
            {logsOpen ? t('devDashboard.deployHelper.hideLogs') : t('devDashboard.deployHelper.showLogs')}
          </button>
        </div>
        {shownLogs.length ? (
          <pre className="max-h-64 overflow-auto rounded-md border border-slate-800 bg-slate-950/70 p-3 text-xs text-slate-200 whitespace-pre-wrap">
            {shownLogs.join('\n')}
          </pre>
        ) : (
          <p className="text-xs text-slate-400">{t('devDashboard.deployHelper.noLogs')}</p>
        )}
      </div>
    </section>
  )
}
