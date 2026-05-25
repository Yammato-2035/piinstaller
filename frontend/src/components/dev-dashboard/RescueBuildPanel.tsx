import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronDown, ChevronRight, ClipboardCopy, HardDriveDownload, ShieldOff } from 'lucide-react'
import { fetchApi } from '../../api'
import { toneClass } from '../../pages/devDashboardFilters'

type ToolEntry = {
  present?: boolean
  path?: string | null
}

type RescueIsoState = {
  status?: string
  summary?: string
  code?: string
  generated_at?: string
  repo?: {
    head?: string | null
    branch?: string | null
    runtime_gate?: string
    runtime_gate_exit?: number | null
    runtime_gate_summary?: string
  }
  tools?: Record<string, ToolEntry>
  build_tree?: {
    path?: string
    exists?: boolean
    validator_status?: string
    auto_config_noauto?: boolean
    auto_build_blocked?: boolean
    missing_paths?: string[]
  }
  stale_state?: {
    present?: boolean
    root_owned_stage_files?: string[]
    skipped_live_build_stages?: string[]
    needs_sudo_clean?: boolean
    indicators?: string[]
  }
  temp_runtime_bundle?: {
    status?: string
    files_count?: number
    manifest_sha256?: string | null
  }
  iso_build?: {
    status?: string
    last_exit_code?: number | null
    last_error?: string | null
    iso_found?: boolean
    iso_path?: string | null
    iso_size_bytes?: number | null
    iso_sha256?: string | null
  }
  usb_write?: {
    allowed?: boolean
    status?: string
    reason?: string
  }
  logs?: {
    latest_log_path?: string
    last_80_lines?: string[]
    last_error?: string | null
  }
  next_operator_action?: {
    type?: string
    label?: string
    commands?: string[]
  }
  forbidden_actions?: {
    dd_allowed?: boolean
    mkfs_allowed?: boolean
    parted_write_allowed?: boolean
    restore_allowed?: boolean
    backup_allowed?: boolean
    usb_write_allowed?: boolean
  }
}

type StepResponse = {
  action_id?: string
  status?: string
  code?: string
  exit_code?: number | null
  errors?: string[]
  warnings?: string[]
  details?: Record<string, unknown>
}

type OperatorCommandsResponse = {
  status?: string
  code?: string
  commands?: string[]
  warnings?: string[]
}

function FlagRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-2 text-xs">
      <span className="text-slate-300">{label}</span>
      <span className="font-mono text-slate-100">{value}</span>
    </div>
  )
}

export function RescueBuildPanel({ refreshSec = 12 }: { refreshSec?: number }) {
  const { t } = useTranslation()
  const [data, setData] = useState<RescueIsoState | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [logsOpen, setLogsOpen] = useState(false)
  const [busyStep, setBusyStep] = useState<string | null>(null)
  const [stepResult, setStepResult] = useState<StepResponse | null>(null)
  const [operatorCommands, setOperatorCommands] = useState<string[]>([])
  const [operatorCommandsTitle, setOperatorCommandsTitle] = useState<string | null>(null)
  const [copyState, setCopyState] = useState<string | null>(null)

  const loadStatus = useCallback(async () => {
    try {
      setError(null)
      const res = await fetchApi('/api/dev-dashboard/rescue-iso/status')
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      const body = (await res.json()) as RescueIsoState
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

  const runStep = useCallback(
    async (step: string) => {
      try {
        setBusyStep(step)
        setStepResult(null)
        const res = await fetchApi('/api/dev-dashboard/rescue-iso/step', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ step, operator_confirm: false }),
        })
        const body = (await res.json()) as StepResponse
        setStepResult(body)
        await loadStatus()
      } catch {
        setStepResult({ status: 'blocked', code: 'FETCH_FAILED', errors: ['fetch_failed'] })
      } finally {
        setBusyStep(null)
      }
    },
    [loadStatus],
  )

  const loadOperatorCommands = useCallback(
    async (kind: 'sudo-clean' | 'build') => {
      try {
        setBusyStep(kind)
        const title =
          kind === 'sudo-clean'
            ? t('devDashboard.rescueIso.operatorSudoCleanRequired')
            : t('devDashboard.rescueIso.operatorBuildCommand')
        const res = await fetchApi(`/api/dev-dashboard/rescue-iso/operator-commands/${kind}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: '{}',
        })
        const body = (await res.json()) as OperatorCommandsResponse
        setOperatorCommands(body.commands || [])
        setOperatorCommandsTitle(title)
        await loadStatus()
      } catch {
        setOperatorCommands([])
        setOperatorCommandsTitle(null)
      } finally {
        setBusyStep(null)
      }
    },
    [loadStatus, t],
  )

  const copyCommands = useCallback(async () => {
    if (!operatorCommands.length || !navigator.clipboard) return
    try {
      await navigator.clipboard.writeText(operatorCommands.join('\n'))
      setCopyState('copied')
      window.setTimeout(() => setCopyState(null), 1600)
    } catch {
      setCopyState('failed')
      window.setTimeout(() => setCopyState(null), 1600)
    }
  }, [operatorCommands])

  const overall = String(data?.status || 'gray')
  const logs = data?.logs?.last_80_lines || []
  const lastErr = data?.iso_build?.last_error || data?.logs?.last_error || data?.summary
  const toolRows = Object.entries(data?.tools || {})
  const nextCommands = useMemo(
    () => (data?.next_operator_action?.commands || []).join('\n'),
    [data?.next_operator_action?.commands],
  )

  const buttonClass =
    'rounded-md border border-slate-700 bg-slate-900/70 px-2.5 py-1.5 text-xs text-slate-100 hover:border-slate-500 disabled:opacity-50 disabled:cursor-not-allowed'
  const sectionClass = 'rounded-lg border border-slate-700/70 bg-slate-950/30 p-3 space-y-2'

  return (
    <section
      className={`rounded-xl border p-4 space-y-3 ${toneClass(overall)}`}
      data-testid="rescue-build-panel"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <HardDriveDownload size={18} className="shrink-0" />
            {t('devDashboard.rescueIso.title')}
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">{t('devDashboard.rescueIso.subtitle')}</p>
        </div>
        <span className="text-xs uppercase tracking-wide font-mono">{overall}</span>
      </div>

      {error ? <p className="text-xs text-rose-200">{error}</p> : null}

      <div className="flex flex-wrap gap-2">
        <button type="button" className={buttonClass} onClick={() => void loadStatus()} disabled={busyStep !== null}>
          {t('devDashboard.rescueIso.refreshStatus')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void runStep('toolcheck')} disabled={busyStep !== null}>
          {t('devDashboard.rescueIso.runToolcheck')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void runStep('detect_stale_state')} disabled={busyStep !== null}>
          {t('devDashboard.rescueIso.checkStaleState')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void runStep('clean_user_state')} disabled={busyStep !== null}>
          {t('devDashboard.rescueIso.cleanUserState')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void runStep('prepare_bundle')} disabled={busyStep !== null}>
          {t('devDashboard.rescueIso.createBundle')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void runStep('validate_bundle')} disabled={busyStep !== null}>
          {t('devDashboard.rescueIso.validateBundle')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void runStep('prepare_tree')} disabled={busyStep !== null}>
          {t('devDashboard.rescueIso.createBuildTree')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void runStep('validate_tree')} disabled={busyStep !== null}>
          {t('devDashboard.rescueIso.validateBuildTree')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void runStep('prebuild_check')} disabled={busyStep !== null}>
          {t('devDashboard.rescueIso.prebuildCheck')}
        </button>
        <button
          type="button"
          className={buttonClass}
          onClick={() => void loadOperatorCommands('sudo-clean')}
          disabled={busyStep !== null}
        >
          {t('devDashboard.rescueIso.showSudoCleanCommand')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void loadOperatorCommands('build')} disabled={busyStep !== null}>
          {t('devDashboard.rescueIso.showOperatorBuildCommand')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void runStep('scan_iso')} disabled={busyStep !== null}>
          {t('devDashboard.rescueIso.scanIso')}
        </button>
        <button type="button" className={buttonClass} onClick={() => void runStep('summarize')} disabled={busyStep !== null}>
          {t('devDashboard.rescueIso.refreshSummary')}
        </button>
      </div>

      <div
        className="rounded-lg border border-red-800/50 bg-red-950/30 px-3 py-2 flex items-start gap-2"
        data-testid="rescue-build-usb-blocked"
      >
        <ShieldOff size={16} className="text-red-300 shrink-0 mt-0.5" />
        <div className="text-xs">
          <p className="font-semibold text-red-100">{t('devDashboard.rescueIso.usbWriteBlocked')}</p>
          <p className="text-red-200/90 mt-0.5">
            {data?.usb_write?.reason || t('devDashboard.rescueIso.noDdAllowed')}
          </p>
        </div>
      </div>

      {stepResult ? (
        <div className="rounded-lg border border-sky-800/40 bg-sky-950/20 px-3 py-2 text-xs" data-testid="rescue-build-step-result">
          <p className="font-semibold text-sky-100">
            {stepResult.status || 'unknown'} {stepResult.code ? `· ${stepResult.code}` : ''}
          </p>
          {stepResult.action_id ? <p className="mt-1 text-sky-100/80 font-mono">{stepResult.action_id}</p> : null}
          {stepResult.errors?.length ? <p className="mt-1 text-rose-200">{stepResult.errors.join(', ')}</p> : null}
        </div>
      ) : null}

      <div className="grid lg:grid-cols-2 gap-3">
        <div className={sectionClass}>
          <p className="text-xs font-semibold text-slate-100">{t('devDashboard.rescueIso.overallStatus')}</p>
          <FlagRow label={t('devDashboard.rescueIso.runtimeGate')} value={String(data?.repo?.runtime_gate || 'unknown')} />
          <FlagRow label="HEAD" value={String(data?.repo?.head || '—')} />
          <FlagRow label={t('devDashboard.runtimeWorkspace.gitBranch')} value={String(data?.repo?.branch || '—')} />
          <FlagRow label={t('devDashboard.rescueIso.isoBuild')} value={String(data?.iso_build?.status || 'not_started')} />
        </div>

        <div className={sectionClass}>
          <p className="text-xs font-semibold text-slate-100">{t('devDashboard.rescueIso.buildTree')}</p>
          <FlagRow label="path" value={String(data?.build_tree?.path || '—')} />
          <FlagRow
            label={t('devDashboard.rescueIso.autoConfigNoauto')}
            value={data?.build_tree?.auto_config_noauto ? 'true' : 'false'}
          />
          <FlagRow
            label={t('devDashboard.rescueIso.autoBuildBlocked')}
            value={data?.build_tree?.auto_build_blocked ? 'true' : 'false'}
          />
          <FlagRow
            label={t('devDashboard.rescueIso.validatorStatus')}
            value={String(data?.build_tree?.validator_status || 'unknown')}
          />
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-3">
        <div className={sectionClass}>
          <p className="text-xs font-semibold text-slate-100">{t('devDashboard.rescueIso.toolcheck')}</p>
          <div className="space-y-1">
            {toolRows.map(([name, tool]) => (
              <FlagRow key={name} label={name} value={tool.present ? tool.path || 'ok' : 'missing'} />
            ))}
          </div>
        </div>

        <div className={sectionClass}>
          <p className="text-xs font-semibold text-slate-100">{t('devDashboard.rescueIso.tempBundle')}</p>
          <FlagRow label={t('devDashboard.rescueIso.validatorStatus')} value={String(data?.temp_runtime_bundle?.status || 'unknown')} />
          <FlagRow label="files" value={String(data?.temp_runtime_bundle?.files_count ?? 0)} />
          <FlagRow
            label="sha256"
            value={data?.temp_runtime_bundle?.manifest_sha256 ? String(data.temp_runtime_bundle.manifest_sha256).slice(0, 16) : '—'}
          />
        </div>
      </div>

      <div
        className={`${sectionClass} ${
          data?.stale_state?.needs_sudo_clean
            ? 'border-red-700/50 bg-red-950/20'
            : data?.stale_state?.present
              ? 'border-amber-700/40 bg-amber-950/20'
              : ''
        }`}
      >
        <p className="text-xs font-semibold text-slate-100">{t('devDashboard.rescueIso.staleBuildState')}</p>
        <FlagRow
          label={t('devDashboard.rescueIso.sudoCleanRequired')}
          value={data?.stale_state?.needs_sudo_clean ? 'true' : 'false'}
        />
        {data?.stale_state?.indicators?.length ? (
          <div className="text-xs text-slate-300 space-y-1">
            {data.stale_state.indicators.map((indicator) => (
              <div key={indicator}>{indicator}</div>
            ))}
          </div>
        ) : null}
        {data?.stale_state?.root_owned_stage_files?.length ? (
          <div className="text-xs text-rose-200 space-y-1">
            <p className="font-semibold">{t('devDashboard.rescueIso.rootOwnedFilesDetected')}</p>
            {data.stale_state.root_owned_stage_files.slice(0, 8).map((item) => (
              <div key={item} className="font-mono break-all">
                {item}
              </div>
            ))}
          </div>
        ) : null}
        {data?.stale_state?.skipped_live_build_stages?.length ? (
          <div className="text-xs text-amber-100 space-y-1">
            <p className="font-semibold">{t('devDashboard.rescueIso.skippedStages')}</p>
            {data.stale_state.skipped_live_build_stages.map((item) => (
              <div key={item}>{item}</div>
            ))}
          </div>
        ) : null}
      </div>

      {lastErr ? (
        <div
          className="rounded-lg border border-amber-800/40 bg-amber-950/20 px-3 py-2"
          data-testid="rescue-build-last-error"
        >
          <p className="text-xs font-semibold text-amber-100">{t('devDashboard.rescueIso.lastError')}</p>
          <pre className="text-[10px] text-amber-100/90 mt-1 whitespace-pre-wrap font-mono">{lastErr}</pre>
        </div>
      ) : null}

      <div className={sectionClass} data-testid="rescue-build-artifacts">
        <p className="text-xs font-semibold text-slate-100">{t('devDashboard.rescueIso.isoArtifact')}</p>
        {data?.iso_build?.iso_path ? (
          <div className="font-mono text-slate-300 break-all space-y-0.5">
            <div>{data.iso_build.iso_path}</div>
            {data.iso_build.iso_size_bytes != null ? <div>{(data.iso_build.iso_size_bytes / (1024 * 1024)).toFixed(1)} MiB</div> : null}
            {data.iso_build.iso_sha256 ? <div className="text-[10px]">SHA256: {data.iso_build.iso_sha256}</div> : null}
            <div>
              exit:{' '}
              {data.iso_build.last_exit_code != null ? String(data.iso_build.last_exit_code) : '—'}
            </div>
          </div>
        ) : (
          <p className="text-slate-400">{t('devDashboard.rescueIso.noIsoFound')}</p>
        )}
      </div>

      {data?.next_operator_action?.label ? (
        <div className="rounded-lg border border-violet-800/40 bg-violet-950/20 px-3 py-2 space-y-2" data-testid="rescue-build-next-action">
          <p className="text-xs font-semibold text-violet-100">{t('devDashboard.rescueIso.nextOperatorAction')}</p>
          <p className="text-xs text-violet-100/90">{data.next_operator_action.label}</p>
          {nextCommands ? (
            <pre className="text-[10px] font-mono whitespace-pre-wrap text-violet-100/90">{nextCommands}</pre>
          ) : null}
        </div>
      ) : null}

      {operatorCommandsTitle && operatorCommands.length ? (
        <div className="rounded-lg border border-cyan-800/40 bg-cyan-950/20 px-3 py-2 space-y-2">
          <div className="flex items-center justify-between gap-2">
            <p className="text-xs font-semibold text-cyan-100">{operatorCommandsTitle}</p>
            <button type="button" className={buttonClass} onClick={() => void copyCommands()}>
              <span className="inline-flex items-center gap-1">
                <ClipboardCopy size={12} />
                {copyState === 'copied' ? t('devDashboard.rescueIso.copied') : t('devDashboard.rescueIso.copyCommands')}
              </span>
            </button>
          </div>
          <pre className="text-[10px] font-mono whitespace-pre-wrap text-cyan-100/90">{operatorCommands.join('\n')}</pre>
        </div>
      ) : null}

      <div>
        <button
          type="button"
          className="flex items-center gap-1 text-xs text-slate-300 hover:text-white"
          onClick={() => setLogsOpen((v) => !v)}
          data-testid="rescue-build-logs-toggle"
        >
          {logsOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          {t('devDashboard.rescueIso.lastLogLines')} ({logs.length})
        </button>
        {logsOpen ? (
          <pre
            className="mt-2 max-h-48 overflow-y-auto text-[10px] font-mono bg-slate-950/60 border border-slate-700 rounded p-2 text-slate-300"
            data-testid="rescue-build-log-lines"
          >
            {logs.length ? logs.join('\n') : t('devDashboard.rescueIso.noLogs')}
          </pre>
        ) : null}
      </div>

      <p className="text-[10px] text-slate-500">{t('devDashboard.rescueIso.noFakeGreen')}</p>
    </section>
  )
}
