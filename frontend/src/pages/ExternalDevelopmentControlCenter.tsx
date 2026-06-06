import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { Activity, Copy, RefreshCw, Terminal } from 'lucide-react'
import { fetchControlCenterSummary, type ControlCenterSummary } from '../api/devDashboardApi'
import { StandaloneModeBanner } from '../components/dev-dashboard/StandaloneModeBanner'
import { RuntimeGatePanel } from '../components/dev-dashboard/RuntimeGatePanel'
import { BackendHealthPanel } from '../components/dev-dashboard/BackendHealthPanel'
import { CockpitBackupProgressPanel } from '../components/dev-dashboard/CockpitBackupProgressPanel'
import { CockpitBackupTargetPanel } from '../components/dev-dashboard/CockpitBackupTargetPanel'
import { DeployStatusPanel } from '../components/dev-dashboard/DeployStatusPanel'
import { RescueStickBoard } from '../components/dev-dashboard/RescueStickBoard'
import { RescueUsbOperatorToolbox } from '../components/dev-dashboard/RescueUsbOperatorToolbox'
import { RescueBuildPanel } from '../components/dev-dashboard/RescueBuildPanel'
import { WindowsRescueInspectCard } from '../components/dev-dashboard/WindowsRescueInspectCard'
import { NotificationPanel } from '../components/dev-dashboard/NotificationPanel'
import { DevelopmentServerPanel } from '../components/devserver/DevelopmentServerPanel'
import { LabSessionsPanel } from '../components/dev-dashboard/LabSessionsPanel'
import { DeployDriftPanel } from '../components/dev-dashboard/DeployDriftPanel'
import { RoadmapDrawer } from '../components/dev-dashboard/RoadmapDrawer'
import { ReadyStableSection } from '../components/dev-dashboard/ReadyStableSection'
import { SafeTestModePanel } from '../components/dev-dashboard/SafeTestModePanel'
import { UpdateStatusCard } from '../components/dev-dashboard/UpdateStatusCard'
import { ControlCenterOverviewHeader } from '../components/dev-dashboard/ControlCenterOverviewHeader'
import { DocumentationDiagnosticsCard } from '../components/dev-dashboard/DocumentationDiagnosticsCard'
import { RescueDeveloperPipelineCard } from '../components/dev-dashboard/RescueDeveloperPipelineCard'
import {
  ControlCenterEvidenceSection,
  ControlCenterSectionTabs,
  type ControlCenterTab,
} from '../components/dev-dashboard/ControlCenterSectionTabs'
import { EvidencePanel } from '../components/dev-dashboard/EvidencePanel'
import { writeCockpitRefreshSec } from '../lib/devDashboard/cockpitWindow'
import { AREA_LABELS } from '../lib/devDashboard/governanceMatrix'
import { clearGovernanceHistory } from '../lib/devDashboard/governanceHistory'
import type { CockpitViewMode, GovernanceAreaStatus, Traffic } from '../lib/devDashboard/governanceTypes'
import { useGovernanceMonitor } from '../lib/devDashboard/useGovernanceMonitor'
import { API_STATUS_PATH } from '../lib/devDashboard/constants'
import { buildFullApiUrl, extractDccPortsFromVersion, type DccGateVersionInfo } from '../lib/devDashboard/dccGate'
import {
  classifyDccBootState,
  hasDccBundleMarkers,
  type DccBootClassification,
  type DccBootProbeResult,
} from '../lib/devDashboard/dccBootState'
import { DccBootDiagnosticsPanel } from '../components/dev-dashboard/DccBootDiagnosticsPanel'
import { DccErrorBoundary } from '../components/dev-dashboard/DccErrorBoundary'
import { fetchApi, getApiBase, getDefaultApiBase } from '../api'
import { toneClass } from './devDashboardFilters'
import {
  internalLabWarning,
  buildProfileMeta,
  buildId,
  frontendBuildProfile,
} from '../config/buildProfile'
import { DccCompactStatusBar } from '../components/dev-dashboard/DccCompactStatusBar'
import { DccCompactOverviewPanel } from '../components/dev-dashboard/DccCompactOverviewPanel'
import {
  fetchDccCompactStatus,
  type DccCompactStatus,
} from '../lib/devDashboard/dccCompactStatus'
import {
  fetchDccLiveStatus,
  type DccLiveStatusSnapshot,
} from '../lib/devDashboard/dccLiveStatus'
import {
  fetchDccApi,
  readStoredDccDeveloperToken,
  writeStoredDccDeveloperToken,
} from '../lib/devDashboard/dccDeveloperToken'

function trafficDot(status: Traffic): string {
  if (status === 'green') return 'bg-emerald-500'
  if (status === 'yellow') return 'bg-amber-400'
  if (status === 'red') return 'bg-red-500'
  return 'bg-slate-500'
}

function GovernanceMatrixGrid({ areas, t }: { areas: GovernanceAreaStatus[]; t: (k: string) => string }) {
  return (
    <div className="grid sm:grid-cols-2 xl:grid-cols-3 gap-2" data-testid="governance-matrix">
      {areas.map((a) => (
        <div
          key={a.id}
          className={`rounded-lg border px-3 py-2 text-sm ${toneClass(a.status)}`}
          data-testid={`governance-area-${a.id}`}
        >
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full shrink-0 ${trafficDot(a.status)}`} aria-hidden />
            <span className="font-medium text-white">{t(AREA_LABELS[a.id])}</span>
            {a.changedToGreen ? (
              <span className="ml-auto text-[10px] uppercase tracking-wide text-emerald-300">
                {t('devDashboard.governance.becameGreen')}
              </span>
            ) : null}
            {a.regressed ? (
              <span className="ml-auto text-[10px] uppercase tracking-wide text-red-300">
                {t('devDashboard.governance.regressed')}
              </span>
            ) : null}
          </div>
          {a.blockers[0] ? <p className="text-xs text-slate-300 mt-1 truncate">{a.blockers[0]}</p> : null}
        </div>
      ))}
    </div>
  )
}

type DevControlDisabledDebug = {
  lastVersionUrl?: string
  lastVersionHttpStatus?: number
  lastDevDashboardStatusUrl?: string
  lastDevDashboardStatusHttpStatus?: number
  lastDevDashboardStatusCode?: string | null
  versionPayload?: {
    install_profile?: string | null
    runtime_ports?: unknown
  } | null
  liveStatus?: DccLiveStatusSnapshot | null
}

export const DccLocalTokenInline: React.FC<{ onSaved?: () => void }> = ({ onSaved }) => {
  const { t } = useTranslation()
  const [tokenDraft, setTokenDraft] = useState(() => readStoredDccDeveloperToken() ?? '')
  const saveToken = () => {
    writeStoredDccDeveloperToken(tokenDraft.trim() || null)
    onSaved?.()
  }
  return (
    <div className="mt-3 flex flex-wrap items-end gap-2" data-testid="dcc-local-token-inline">
      <label className="block text-left text-slate-300 text-xs flex-1 min-w-[200px]">
        <span className="text-[10px] uppercase tracking-wide">
          {t('devDashboard.profileDisabled.localToken', 'Lokaler DCC-Token (nur Browser)')}
        </span>
        <input
          type="password"
          autoComplete="off"
          className="mt-1 w-full rounded border border-slate-600 bg-slate-950 px-2 py-1 text-xs text-white"
          value={tokenDraft}
          onChange={(e) => setTokenDraft(e.target.value)}
          data-testid="dcc-local-token-input"
        />
      </label>
      <button
        type="button"
        className="rounded bg-violet-700/80 px-3 py-1.5 text-xs text-white"
        onClick={saveToken}
        data-testid="dcc-local-token-save"
      >
        {t('devDashboard.profileDisabled.saveToken', 'Token speichern')}
      </button>
    </div>
  )
}

export const DevControlDisabledPage: React.FC<{
  debug: DevControlDisabledDebug
  onRetry: () => void
  retryDisabled?: boolean
  onTokenSaved?: () => void
}> = ({ debug, onRetry, retryDisabled, onTokenSaved }) => {
  const { t } = useTranslation()
  const [tokenDraft, setTokenDraft] = useState(() => readStoredDccDeveloperToken() ?? '')
  const ports = extractDccPortsFromVersion((debug.versionPayload as any) ?? null)
  const profile = debug.versionPayload?.install_profile ?? buildProfileMeta.frontend_build_profile
  const cap = debug.liveStatus?.capability ?? null
  const blockReason =
    debug.lastDevDashboardStatusCode ??
    cap?.reason ??
    'PROFILE_ROUTE_BLOCKED'
  const telemetryReachable = (debug.liveStatus?.telemetryHttp ?? 0) === 200

  const saveToken = () => {
    writeStoredDccDeveloperToken(tokenDraft.trim() || null)
    onTokenSaved?.()
    onRetry()
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-start p-8 bg-slate-950" data-testid="dev-control-disabled">
      <div className="max-w-3xl w-full">
        <DccCompactStatusBar
          live={debug.liveStatus ?? null}
          statusHttp={debug.lastDevDashboardStatusHttpStatus ?? 0}
          versionPayload={(debug.versionPayload as any) ?? null}
        />

        <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-6 text-center">
        <h1 className="text-lg font-semibold text-white mb-2">
          {t('devDashboard.profileDisabled.blockedTitle', 'DCC blockiert')}
        </h1>

        <p className="text-sm text-slate-400">
          {t('devDashboard.profileDisabled.blockedBody', 'Grund: {{reason}}', { reason: blockReason })}
        </p>

        <p className="text-xs text-slate-500 mt-3 font-mono">profile={profile}</p>

        <div className="mt-4 text-left text-xs text-slate-400 space-y-2 border-t border-slate-700 pt-4">
          <p>
            {t(
              'devDashboard.profileDisabled.telemetryReachable',
              'Telemetrie-Health: {{state}}',
              { state: telemetryReachable ? 'erreichbar' : 'nicht erreichbar' },
            )}
          </p>
          <p>{t('devDashboard.profileDisabled.portHint', 'Dies ist kein Portfehler. Interne Dev-Routen sind blockiert (siehe Debug-Status), nicht „Backend down“.')}</p>

          <ul className="font-mono text-slate-500 list-disc pl-4 space-y-1">
            <li>API: {ports.api}</li>
            <li>UI/DCC: {ports.ui}</li>
            <li>nginx/default: {ports.nginx}</li>
            {ports.qemu_host_proxy ? <li>QEMU host proxy: {ports.qemu_host_proxy}</li> : null}
            {ports.qemu_guest_devserver ? <li>QEMU guest devserver: {ports.qemu_guest_devserver}</li> : null}
          </ul>

          <div className="space-y-1">
            <p className="text-slate-500">
              {t('devDashboard.profileDisabled.lastVersion', 'GET {{url}} => HTTP {{code}}', {
                url: debug.lastVersionUrl ?? '/api/version',
                code: debug.lastVersionHttpStatus ?? '—',
              })}
            </p>
            <p className="text-slate-500">
              {t('devDashboard.profileDisabled.lastDccStatus', 'GET {{url}} => HTTP {{code}} (backend code={{bcode}})', {
                url: debug.lastDevDashboardStatusUrl ?? API_STATUS_PATH,
                code: debug.lastDevDashboardStatusHttpStatus ?? '—',
                bcode: debug.lastDevDashboardStatusCode ?? '—',
              })}
            </p>
            <p className="text-slate-400">{t('devDashboard.profileDisabled.gatingErrorHint', 'Wenn /api/dev-dashboard/status HTTP 200 liefert, ist dies ein Frontend-Gating-Fehler.')}</p>
          </div>

          <div className="rounded border border-slate-700 bg-slate-950/40 p-3 space-y-2" data-testid="dcc-operator-token-hint">
            <p className="text-slate-300 font-semibold">
              {t('devDashboard.profileDisabled.operatorAction', 'Nächste lokale Operator-Aktion')}
            </p>
            <ol className="list-decimal pl-4 space-y-1 text-slate-400">
              <li>{t('devDashboard.profileDisabled.operatorEnv', 'Optional /etc/setuphelfer/developer.env: DCC_DEVELOPER_ENABLED=1')}</li>
              <li>{t('devDashboard.profileDisabled.operatorTokenFile', 'Token-Datei /etc/setuphelfer/dcc_developer.token (nicht ins Repo)')}</li>
              <li>{t('devDashboard.profileDisabled.operatorHeader', 'Header X-Setuphelfer-Developer-Token oder unten lokal speichern')}</li>
              <li>{t('devDashboard.profileDisabled.operatorRestart', 'Backend-Restart nur mit Operator-Freigabe nach Konfigurationsänderung')}</li>
            </ol>
            <label className="block text-left text-slate-400">
              <span className="text-[10px] uppercase tracking-wide">{t('devDashboard.profileDisabled.localToken', 'Lokaler DCC-Token (nur Browser)')}</span>
              <input
                type="password"
                autoComplete="off"
                className="mt-1 w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 text-slate-200 font-mono text-xs"
                value={tokenDraft}
                onChange={(e) => setTokenDraft(e.target.value)}
                data-testid="dcc-local-token-input"
              />
            </label>
            <button
              type="button"
              className="btn-secondary text-xs"
              onClick={saveToken}
              data-testid="dcc-local-token-save"
            >
              {t('devDashboard.profileDisabled.saveTokenRetry', 'Token speichern & erneut prüfen')}
            </button>
          </div>

          <p className="text-slate-500">{t('devDashboard.profileDisabled.docsHint', 'Siehe docs/dev-dashboard/PORTS_AND_PROFILES.md')}</p>
        </div>

        <div className="mt-5">
          <button
            type="button"
            className="btn-secondary inline-flex items-center gap-2 text-xs"
            onClick={onRetry}
            disabled={retryDisabled}
            data-testid="dev-control-disabled-retry"
          >
            {t('devDashboard.profileDisabled.retry', 'DCC-Status erneut prüfen')}
          </button>
        </div>
        </div>
      </div>
    </div>
  )
}

export const ExternalDevelopmentControlCenter: React.FC = () => {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<ControlCenterTab>('overview')

  // Used to bust any potential caching layers for `/api/dev-dashboard/status`.
  const [statusT, setStatusT] = useState(() => Date.now())
  const [bootProbe, setBootProbe] = useState<DccBootProbeResult | null>(null)
  const [bootClassification, setBootClassification] = useState<DccBootClassification>({
    state: 'boot_loading',
    shouldShowDcc: false,
    dccExpectedVisible: false,
    reason: 'probe_pending',
  })
  const [gateLoading, setGateLoading] = useState(true)
  const [liveStatus, setLiveStatus] = useState<DccLiveStatusSnapshot | null>(null)
  const [compactStatus, setCompactStatus] = useState<DccCompactStatus | null>(null)
  const [compactLoading, setCompactLoading] = useState(false)
  const bundleMarkers = useMemo(() => hasDccBundleMarkers(), [])

  const [summary, setSummary] = useState<ControlCenterSummary | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(false)

  const statusQuery = useMemo(() => {
    const params = new URLSearchParams()
    const fv =
      typeof __APP_VERSION__ !== 'undefined' && String(__APP_VERSION__).trim() ? String(__APP_VERSION__).trim() : ''
    if (fv) params.set('frontend_build_version', fv)
    params.set('frontend_runtime_source', import.meta.env.DEV ? 'dev' : 'build')
    params.set('t', String(statusT))
    return params.toString()
  }, [statusT])

  const mon = useGovernanceMonitor(statusQuery)

  const retryGate = () => setStatusT(Date.now())

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      setGateLoading(true)
      if (!bundleMarkers.ok) {
        setBootProbe(null)
        setBootClassification(classifyDccBootState(null, false))
        setGateLoading(false)
        return
      }

      const apiBase = getApiBase()
      const lastVersionUrl = buildFullApiUrl(apiBase, '/api/version')
      const lastDevDashboardStatusUrl = buildFullApiUrl(apiBase, `${API_STATUS_PATH}?${statusQuery}`)

      let versionPayload: Record<string, unknown> | null = null
      let versionHttpStatus = 0
      let versionFetchFailed = false
      try {
        const r = await fetchApi('/api/version', { cache: 'no-store' })
        versionHttpStatus = r.status
        if (r.ok) versionPayload = (await r.json().catch(() => null)) as Record<string, unknown> | null
      } catch {
        versionHttpStatus = 0
        versionFetchFailed = true
      }

      let statusHttpStatus = 0
      let statusCode: string | null = null
      let statusFetchFailed = false
      try {
        const r = await fetchDccApi(`${API_STATUS_PATH}?${statusQuery}`, { cache: 'no-store' })
        statusHttpStatus = r.status
        if (!r.ok) {
          const body = await r.json().catch(() => ({}))
          statusCode = typeof body?.code === 'string' ? body.code : null
        }
      } catch {
        statusHttpStatus = 0
        statusFetchFailed = true
      }

      const versionInfo = versionPayload as DccGateVersionInfo | null
      const live = await fetchDccLiveStatus(versionInfo)
      let compact: DccCompactStatus | null = null
      setCompactLoading(true)
      const compactResp = await fetchDccCompactStatus()
      compact = compactResp.body
      setCompactLoading(false)

      const probe: DccBootProbeResult = {
        versionHttp: versionHttpStatus,
        statusHttp: statusHttpStatus,
        statusCode,
        versionPayload,
        versionFetchFailed,
        statusFetchFailed,
        versionUrl: lastVersionUrl,
        statusUrl: lastDevDashboardStatusUrl,
        loadedUrl: typeof window !== 'undefined' ? window.location.href : '',
        apiBaseUrl: apiBase || getDefaultApiBase() || 'http://127.0.0.1:8000',
        buildVersion:
          typeof __APP_VERSION__ !== 'undefined' && String(__APP_VERSION__).trim()
            ? String(__APP_VERSION__).trim()
            : buildProfileMeta.project_version ?? 'unknown',
        buildId: buildId || 'unknown',
        frontendBuildProfile,
      }

      if (cancelled) return
      setBootProbe(probe)
      setLiveStatus(live)
      setCompactStatus(compact)
      setBootClassification(classifyDccBootState(probe, bundleMarkers.ok))
      setGateLoading(false)
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [statusQuery, bundleMarkers.ok])

  const loadSummary = useCallback(async () => {
    if (!mon.apiReachable) {
      setSummary(null)
      return
    }
    setSummaryLoading(true)
    try {
      const data = await fetchControlCenterSummary()
      setSummary(data)
    } finally {
      setSummaryLoading(false)
    }
  }, [mon.apiReachable])

  useEffect(() => {
    void loadSummary()
    const id = window.setInterval(() => void loadSummary(), mon.refreshSec * 1000)
    return () => window.clearInterval(id)
  }, [loadSummary, mon.refreshSec])

  const viewBtn = (mode: CockpitViewMode, label: string) => (
    <button
      type="button"
      data-testid={`cockpit-view-${mode}`}
      onClick={() => mon.setViewMode(mode)}
      className={`px-3 py-1.5 rounded-md text-xs font-medium border ${
        mon.viewMode === mode
          ? 'bg-violet-900/70 border-violet-500/60 text-white'
          : 'border-slate-600 text-slate-300 hover:bg-slate-800/60'
      }`}
    >
      {label}
    </button>
  )

  const copyPrompt = async () => {
    if (!mon.governancePrompt) {
      toast.error(t('devDashboard.noData'))
      return
    }
    try {
      await navigator.clipboard.writeText(mon.governancePrompt)
      toast.success(t('devDashboard.governance.promptCopied'))
    } catch {
      toast.error(t('devDashboard.noData'))
    }
  }

  const onRefreshInterval = (sec: number) => {
    writeCockpitRefreshSec(sec)
    mon.setRefreshSec(sec)
  }

  const refreshAll = () => {
    void mon.refresh()
    void loadSummary()
  }

  const tabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <>
            <ControlCenterOverviewHeader summary={summary} loading={summaryLoading} apiReachable={mon.apiReachable} />
            {mon.dashboard ? <ReadyStableSection dashboard={mon.dashboard} t={t} /> : null}
            <section className="mb-4">
              <h2 className="text-sm font-semibold text-slate-300 mb-2">{t('devDashboard.governance.matrixTitle')}</h2>
              <GovernanceMatrixGrid areas={mon.areas} t={t} />
            </section>
            <DocumentationDiagnosticsCard summary={summary} />
            <RescueDeveloperPipelineCard summary={summary} />
          </>
        )
      case 'roadmap':
        return mon.dashboard ? (
          <RoadmapDrawer dashboard={mon.dashboard} t={t} apiReachable={mon.apiReachable} />
        ) : (
          <section className="rounded-xl border border-amber-700/40 bg-amber-950/20 p-4" data-testid="roadmap-unavailable">
            <p className="text-sm text-amber-100">{t('devDashboard.roadmap.unavailable')}</p>
          </section>
        )
      case 'telemetry':
        return (
          <>
            <LabSessionsPanel refreshSec={mon.refreshSec} />
            <DevelopmentServerPanel refreshSec={mon.refreshSec} />
          </>
        )
      case 'rescue':
        return (
          <>
            <WindowsRescueInspectCard planningOnly />
            <RescueUsbOperatorToolbox
              compactUsbOperator={compactStatus?.rescue?.usb_operator}
              developerCapabilityValid={compactStatus?.developer_capability?.valid}
              dccVisible={compactStatus?.dcc_visible}
            />
            <RescueDeveloperPipelineCard summary={summary} />
            <RescueStickBoard dashboard={mon.dashboard} />
            <RescueBuildPanel refreshSec={mon.refreshSec} />
          </>
        )
      case 'documentation':
        return (
          <>
            <DocumentationDiagnosticsCard summary={summary} />
            {mon.dashboard ? <EvidencePanel dashboard={mon.dashboard} t={t} /> : null}
          </>
        )
      case 'evidence':
        return (
          <>
            <ControlCenterEvidenceSection summary={summary} t={t} />
            {mon.dashboard ? <EvidencePanel dashboard={mon.dashboard} t={t} /> : null}
          </>
        )
      case 'operations':
        return (
          <section className="space-y-4" data-testid="cockpit-operations-panels">
            {mon.dashboard ? (
              <>
                <BackendHealthPanel dashboard={mon.dashboard} t={t} />
                <RuntimeGatePanel dashboard={mon.dashboard} t={t} />
                <SafeTestModePanel dashboard={mon.dashboard} t={t} />
                <DeployDriftPanel dashboard={mon.dashboard} t={t} />
              </>
            ) : null}
            <UpdateStatusCard refreshSec={Math.max(mon.refreshSec, 15)} />
            <DeployStatusPanel refreshSec={Math.max(mon.refreshSec, 10)} />
            <NotificationPanel refreshSec={Math.max(mon.refreshSec, 10)} />
            <CockpitBackupTargetPanel refreshSec={mon.refreshSec} />
            <CockpitBackupProgressPanel refreshSec={mon.refreshSec} />
          </section>
        )
      default:
        return null
    }
  }

  const disabledDebug: DevControlDisabledDebug | null = bootProbe
    ? {
        lastVersionUrl: bootProbe.versionUrl,
        lastVersionHttpStatus: bootProbe.versionHttp,
        lastDevDashboardStatusUrl: bootProbe.statusUrl,
        lastDevDashboardStatusHttpStatus: bootProbe.statusHttp,
        lastDevDashboardStatusCode: bootProbe.statusCode,
        versionPayload: bootProbe.versionPayload,
        liveStatus,
      }
    : null

  const renderBlockedShell = (testId: string, title: string, body: string) => (
    <div className="flex items-center justify-center p-8" data-testid={testId}>
      <div className="max-w-lg rounded-xl border border-slate-700 bg-slate-900/80 p-6 text-center">
        <h1 className="text-lg font-semibold text-white mb-2">{title}</h1>
        <p className="text-sm text-slate-400">{body}</p>
      </div>
    </div>
  )

  const renderMainContent = () => {
    const state = bootClassification.state

    if (state === 'stale_or_wrong_bundle') {
      return renderBlockedShell(
        'dcc-stale-bundle',
        t('devDashboard.bootDiagnostics.state.staleBundle', 'stale_or_wrong_bundle'),
        t(
          'devDashboard.bootDiagnostics.staleBundleBody',
          'Das ausgelieferte Frontend-Bundle enthält nicht den erwarteten DCC-Diagnose-Marker. Deploy nach /opt prüfen.',
        ),
      )
    }

    if (state === 'boot_loading' || gateLoading) {
      return (
        <div className="flex items-center justify-center p-8" data-testid="dev-control-gate-loading">
          <div className="text-sm text-slate-300">
            {t('devDashboard.profileDisabled.gateLoading', 'Prüfe DCC-Status…')}
          </div>
        </div>
      )
    }

    if (state === 'profile_blocked_release' && disabledDebug) {
      return <DevControlDisabledPage debug={disabledDebug} onRetry={retryGate} retryDisabled={gateLoading} />
    }

    const tokenRequired = state === 'dcc_token_required'

    if (state === 'api_unreachable') {
      return renderBlockedShell(
        'dcc-api-unreachable',
        t('devDashboard.bootDiagnostics.state.apiUnreachable', 'api_unreachable'),
        t(
          'devDashboard.bootDiagnostics.apiUnreachableBody',
          'Backend/API unter :8000 nicht erreichbar. Dies ist kein Portfehler an :3001 — API-Base und Netzwerk prüfen.',
        ),
      )
    }

    if (state === 'api_error') {
      return renderBlockedShell(
        'dcc-api-error',
        t('devDashboard.bootDiagnostics.state.apiError', 'api_error'),
        t(
          'devDashboard.bootDiagnostics.apiErrorBody',
          'Die Statusroute lieferte einen unerwarteten HTTP-Code. Siehe Boot-Diagnose oben.',
        ),
      )
    }

    if (state === 'unknown_dcc_boot_failure') {
      return renderBlockedShell(
        'dcc-unknown-boot-failure',
        t('devDashboard.bootDiagnostics.state.unknown', 'unknown_dcc_boot_failure'),
        t(
          'devDashboard.bootDiagnostics.unknownBody',
          'DCC-Boot konnte nicht klassifiziert werden. Debugdaten oben — kein leerer Zustand.',
        ),
      )
    }

    if (!bootClassification.shouldShowDcc) {
      return renderBlockedShell(
        'dcc-boot-blocked-fallback',
        t('devDashboard.profileDisabled.title', 'Development Control nicht verfügbar'),
        t('devDashboard.profileDisabled.errorBody', 'DCC-Verfügbarkeit ist inkonsistent (bitte erneut prüfen).'),
      )
    }

    return (
    <div className="max-w-[1600px] mx-auto px-4 py-5" data-testid="external-development-control-center">
      {tokenRequired ? (
        <div
          className="mb-4 rounded-xl border border-amber-700/50 bg-amber-950/25 p-4"
          data-testid="dcc-token-required-banner"
        >
          <p className="text-sm font-semibold text-amber-100">
            {t('devDashboard.tokenRequired.title', 'Developer-Token erforderlich')}
          </p>
          <p className="mt-1 text-xs text-amber-200/90">
            {t(
              'devDashboard.tokenRequired.body',
              'Lokalen DCC-Token speichern (Header X-Setuphelfer-Developer-Token), dann erneut laden. USB-Toolbox und Status-Routen bleiben ohne Token blockiert.',
            )}
          </p>
          <DccLocalTokenInline onSaved={retryGate} />
        </div>
      ) : null}
      <DccCompactOverviewPanel
        compact={compactStatus}
        loading={compactLoading}
        rawDetailsJson={
          compactStatus
            ? JSON.stringify({ compact: compactStatus, live: liveStatus }, null, 2)
            : null
        }
      />
      <DccCompactStatusBar
        live={liveStatus}
        statusHttp={bootProbe?.statusHttp ?? 0}
        versionPayload={(bootProbe?.versionPayload as DccGateVersionInfo | null) ?? null}
      />
      <header className="flex flex-wrap items-start justify-between gap-4 mb-4 border-b border-slate-700 pb-4">
        <div>
          <h1 className="text-xl font-semibold text-white flex items-center gap-2">
            <Terminal className="text-violet-400" size={24} aria-hidden />
            {t('devDashboard.governance.title')}
          </h1>
          <p className="text-sm text-slate-400 mt-1">{t('devDashboard.governance.subtitle')}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {viewBtn('operations', t('devDashboard.governance.view.operations'))}
          {viewBtn('compact', t('devDashboard.governance.view.compact'))}
          {viewBtn('timeline', t('devDashboard.governance.view.timeline'))}
          <button
            type="button"
            className="px-3 py-1.5 rounded-md text-xs font-medium border border-violet-600/60 text-violet-100 hover:bg-violet-950/40"
            data-testid="cockpit-scroll-roadmap"
            onClick={() => setActiveTab('roadmap')}
          >
            {t('devDashboard.nav.roadmap')}
          </button>
          <label className="text-xs text-slate-400 flex items-center gap-1">
            {t('devDashboard.governance.refreshSec')}
            <select
              className="bg-slate-900 border border-slate-600 rounded px-1 py-0.5 text-slate-200"
              value={mon.refreshSec}
              onChange={(e) => onRefreshInterval(Number(e.target.value))}
              data-testid="cockpit-refresh-interval"
            >
              {[5, 8, 10, 12, 15].map((n) => (
                <option key={n} value={n}>
                  {n}s
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            className="btn-secondary inline-flex items-center gap-1 text-xs"
            onClick={() => void refreshAll()}
            disabled={mon.loading}
            data-testid="cockpit-refresh"
          >
            <RefreshCw className={mon.loading ? 'animate-spin' : ''} size={14} />
            {t('backup.ui.refresh')}
          </button>
          <button
            type="button"
            className="btn-primary inline-flex items-center gap-1 text-xs"
            onClick={() => void copyPrompt()}
            data-testid="cockpit-copy-prompt"
          >
            <Copy size={14} />
            {t('devDashboard.governance.copyPrompt')}
          </button>
        </div>
      </header>

      {internalLabWarning ? (
        <p
          className="mb-3 rounded-lg border border-amber-700/50 bg-amber-950/30 px-3 py-2 text-sm text-amber-100"
          data-testid="internal-lab-warning"
          role="status"
        >
          {internalLabWarning}
        </p>
      ) : null}

      <StandaloneModeBanner
        source={mon.source}
        apiReachable={mon.apiReachable}
        capabilities={mon.capabilities}
        workspaceRoot={mon.workspaceRoot}
        offlineReason={mon.offlineReason}
      />

      {mon.alerts.length > 0 ? (
        <ul className="mb-4 space-y-1" data-testid="cockpit-alerts">
          {mon.alerts.slice(0, 8).map((a) => (
            <li
              key={a.id}
              className={`text-xs px-3 py-2 rounded border ${
                a.severity === 'critical'
                  ? 'border-red-700/60 bg-red-950/40 text-red-100'
                  : a.severity === 'warning'
                    ? 'border-amber-700/50 bg-amber-950/30 text-amber-100'
                    : 'border-sky-700/40 bg-sky-950/20 text-sky-100'
              }`}
            >
              {a.message}
            </li>
          ))}
        </ul>
      ) : null}

      {mon.viewMode === 'timeline' ? (
        <section className="rounded-xl border border-slate-700 bg-slate-900/50 p-4" data-testid="cockpit-timeline">
          <div className="flex justify-between items-center mb-3">
            <h2 className="text-base font-semibold text-white">{t('devDashboard.governance.timeline')}</h2>
            <button
              type="button"
              className="text-xs text-slate-400 hover:text-slate-200"
              onClick={() => {
                clearGovernanceHistory()
                void mon.refresh()
              }}
            >
              {t('devDashboard.governance.clearHistory')}
            </button>
          </div>
          <ul className="space-y-2 max-h-[70vh] overflow-y-auto text-xs">
            {mon.timeline.length ? (
              mon.timeline.map((e) => (
                <li key={e.id} className="border-l-2 border-slate-600 pl-3 py-1">
                  <span className="text-slate-500">{e.at}</span> — {e.message}
                </li>
              ))
            ) : (
              <li className="text-slate-400">{t('devDashboard.governance.timelineEmpty')}</li>
            )}
          </ul>
        </section>
      ) : (
        <>
          <ControlCenterSectionTabs active={activeTab} onChange={setActiveTab} t={t} />
          {tabContent()}
        </>
      )}

      {(mon.changedToGreen.length > 0 || mon.regressed.length > 0) && mon.viewMode !== 'timeline' ? (
        <div className="grid md:grid-cols-2 gap-3 mt-4" data-testid="cockpit-transitions">
          <div className="rounded-lg border border-emerald-700/40 bg-emerald-950/20 p-3">
            <h2 className="text-sm font-semibold text-emerald-200 flex items-center gap-1">
              <Activity size={14} />
              {t('devDashboard.governance.greenTransitions')}
            </h2>
            <ul className="text-xs text-emerald-100/90 mt-2 space-y-1">
              {mon.changedToGreen.length
                ? mon.changedToGreen.map((a) => (
                    <li key={a.id}>
                      {t(AREA_LABELS[a.id])} ({a.previousStatus} → green)
                    </li>
                  ))
                : [{ key: 'none', text: t('devDashboard.governance.noGreenTransitions') }].map((x) => (
                    <li key={x.key}>{x.text}</li>
                  ))}
            </ul>
          </div>
          <div className="rounded-lg border border-red-700/40 bg-red-950/20 p-3">
            <h2 className="text-sm font-semibold text-red-200">{t('devDashboard.governance.regressions')}</h2>
            <ul className="text-xs text-red-100/90 mt-2 space-y-1">
              {mon.regressed.length
                ? mon.regressed.map((a) => (
                    <li key={a.id}>
                      {t(AREA_LABELS[a.id])} ({a.previousStatus} → {a.status})
                    </li>
                  ))
                : [{ key: 'none', text: t('devDashboard.governance.noRegressions') }].map((x) => (
                    <li key={x.key}>{x.text}</li>
                  ))}
            </ul>
          </div>
        </div>
      ) : null}

      <p className="text-[11px] text-slate-500 mt-6 border-t border-slate-800 pt-3">
        {t('devDashboard.governance.readOnlyFooter')}
      </p>
    </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100" data-testid="dcc-cockpit-shell">
      <DccBootDiagnosticsPanel
        classification={bootClassification}
        probe={bootProbe}
        onRetry={retryGate}
        retryDisabled={gateLoading}
      />
      <DccErrorBoundary probe={bootProbe} baseClassification={bootClassification} onRetry={retryGate}>
        {renderMainContent()}
      </DccErrorBoundary>
    </div>
  )
}
