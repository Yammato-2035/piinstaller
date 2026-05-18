import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { RefreshCw, Terminal } from 'lucide-react'
import { fetchApi } from '../api'
import PageHeader from '../components/layout/PageHeader'
import { DevDashboardBody, type DashboardPayload, type ModuleRow } from './DevDashboardBody'
import { RuntimeWorkspacePanel } from './DevDashboardBody'
import type { FilterKey } from './devDashboardFilters'
import { StatusCard } from '../components/dev-dashboard/StatusCard'
import { RuntimeGatePanel } from '../components/dev-dashboard/RuntimeGatePanel'
import { DeployDriftPanel } from '../components/dev-dashboard/DeployDriftPanel'
import { PackageGatePanel } from '../components/dev-dashboard/PackageGatePanel'
import { SafeTestModePanel } from '../components/dev-dashboard/SafeTestModePanel'
import { EvidencePanel } from '../components/dev-dashboard/EvidencePanel'
import { ReleaseGatePanel } from '../components/dev-dashboard/ReleaseGatePanel'
import { RecommendedActionsPanel } from '../components/dev-dashboard/RecommendedActionsPanel'
import { StructuralHealthPanel } from '../components/dev-dashboard/StructuralHealthPanel'
import { CommitHygienePanel } from '../components/dev-dashboard/CommitHygienePanel'
import { DocsConsistencyPanel } from '../components/dev-dashboard/DocsConsistencyPanel'
import { RoadmapDrawer } from '../components/dev-dashboard/RoadmapDrawer'
import { AIExportPanel } from '../components/dev-dashboard/AIExportPanel'
import { StandaloneModeBanner } from '../components/dev-dashboard/StandaloneModeBanner'
import { getApiBaseLabel, loadDevDashboard } from '../lib/devDashboard/loadDevDashboard'
import type { DevDashboardCapabilities, DevDashboardDataSource } from '../lib/devDashboard/types'

type SidebarSection = 'overview' | 'gates' | 'structure' | 'roadmap' | 'modules'

const DevelopmentDashboard: React.FC = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [section, setSection] = useState<SidebarSection>('overview')
  const [dashboard, setDashboard] = useState<DashboardPayload>(null)
  const [modules, setModules] = useState<ModuleRow[]>([])
  const [evidenceIndex, setEvidenceIndex] = useState<Record<string, unknown> | null>(null)
  const [filter, setFilter] = useState<FilterKey>('all')
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [apiBaseDisplay, setApiBaseDisplay] = useState('')
  const [dataSource, setDataSource] = useState<DevDashboardDataSource>('unavailable')
  const [apiReachable, setApiReachable] = useState(false)
  const [capabilities, setCapabilities] = useState<DevDashboardCapabilities>({
    runtimeApi: false,
    workspaceAnalysis: false,
    structureHealth: false,
    roadmap: false,
    promptExport: true,
    runtimeTests: false,
  })
  const [workspaceRoot, setWorkspaceRoot] = useState<string | undefined>()
  const [standaloneMetaPrompt, setStandaloneMetaPrompt] = useState<string | undefined>()

  const statusQuery = useMemo(() => {
    const params = new URLSearchParams()
    const fv =
      typeof __APP_VERSION__ !== 'undefined' && String(__APP_VERSION__).trim() ? String(__APP_VERSION__).trim() : ''
    if (fv) params.set('frontend_build_version', fv)
    params.set('frontend_runtime_source', import.meta.env.DEV ? 'dev' : 'build')
    return params.toString()
  }, [])

  const loadAll = useCallback(async () => {
    setLoading(true)
    try {
      setApiBaseDisplay(getApiBaseLabel())
      const result = await loadDevDashboard(statusQuery)
      setDashboard(result.dashboard)
      setModules(result.modules)
      setEvidenceIndex(result.evidenceIndex)
      setDataSource(result.source)
      setApiReachable(result.apiReachable)
      setCapabilities(result.capabilities)
      setWorkspaceRoot(result.workspaceRoot)
      setStandaloneMetaPrompt(result.metaPrompt)
      if (!result.apiReachable && result.source !== 'runtime_api') {
        toast(t('devDashboard.standalone.toastOffline'), { icon: '⚠️', duration: 6000 })
      }
    } catch {
      toast.error(t('devDashboard.noData'))
      setDashboard(null)
      setModules([])
      setEvidenceIndex(null)
    } finally {
      setLoading(false)
    }
  }, [t, statusQuery])

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  const postAction = async (path: string) => {
    if (!apiReachable || dataSource !== 'runtime_api') {
      toast.error(t('devDashboard.standalone.runtimeTestsLocked'))
      return
    }
    try {
      const r = await fetchApi(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
      const d = await r.json().catch(() => ({}))
      const mk = typeof d?.message_key === 'string' ? d.message_key : 'devDashboard.actions.confirmRequired'
      toast(t(mk), { icon: 'ℹ️', duration: 5000 })
    } catch {
      toast.error(t('devDashboard.noData'))
    }
  }

  const toggle = (id: string) => setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))

  const rg = (dashboard?.runtime_gate as Record<string, unknown>) || {}
  const stm = (dashboard?.safe_test_mode as Record<string, unknown>) || {}
  const sh = (dashboard?.structure_health as Record<string, unknown>) || {}
  const runtimeGateLabel =
    !apiReachable || rg.passed === false
      ? t('devDashboard.standalone.blocked')
      : String(rg.status ?? '—')

  const navBtn = (id: SidebarSection, label: string) => (
    <button
      key={id}
      type="button"
      data-testid={`dev-dashboard-nav-${id}`}
      onClick={() => setSection(id)}
      className={`w-full text-left px-3 py-2 rounded-md text-sm ${section === id ? 'bg-violet-900/60 border border-violet-500/50' : 'border border-transparent hover:bg-slate-800/60'}`}
    >
      {label}
    </button>
  )

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 text-slate-100" data-testid="development-dashboard">
      <PageHeader
        visualStyle="tech-panel"
        tone="settings"
        title={t('devDashboard.title')}
        subtitle={t('devDashboard.subtitle')}
        badge={<Terminal className="text-violet-400 shrink-0" size={28} aria-hidden />}
      />

      <StandaloneModeBanner
        source={dataSource}
        apiReachable={apiReachable}
        capabilities={capabilities}
        workspaceRoot={workspaceRoot}
      />

      <div className="rounded-lg border border-amber-700/50 bg-amber-950/30 px-4 py-3 text-sm text-amber-100 mb-4">
        {t('devDashboard.expertOnlyNotice')}
      </div>
      <div className="rounded-lg border border-slate-600 bg-slate-900/50 px-4 py-3 text-sm text-slate-300 mb-6">
        {t('devDashboard.readOnlyNotice')}
      </div>

      <div className="grid lg:grid-cols-[200px_1fr] gap-6">
        <aside className="space-y-1 rounded-xl border border-slate-700 bg-slate-900/40 p-2" data-testid="dev-dashboard-sidebar">
          {navBtn('overview', t('devDashboard.nav.overview'))}
          {navBtn('gates', t('devDashboard.nav.gates'))}
          {navBtn('structure', t('devDashboard.nav.structure'))}
          {navBtn('roadmap', t('devDashboard.nav.roadmap'))}
          {navBtn('modules', t('devDashboard.nav.modules'))}
          <button type="button" onClick={() => void loadAll()} className="w-full mt-2 btn-secondary inline-flex items-center justify-center gap-2 text-xs" disabled={loading}>
            <RefreshCw className={loading ? 'animate-spin' : ''} size={14} />
            {t('backup.ui.refresh')}
          </button>
        </aside>

        <main className="space-y-6 min-w-0">
          <div className="grid md:grid-cols-3 gap-4" data-testid="dev-dashboard-status-cards">
            <StatusCard
              label={t('devDashboard.runtimeGate.title')}
              value={runtimeGateLabel}
              tone={!apiReachable || rg.passed === false ? 'red' : String(rg.status || 'gray')}
              testId="dev-dashboard-runtime-gate-summary"
            />
            <StatusCard
              label={t('devDashboard.safeTestMode.title')}
              value={String(stm.mode ?? 'LOCKED')}
              tone={stm.locked ? 'red' : 'green'}
              testId="dev-dashboard-safe-test-summary"
            />
            <StatusCard
              label={t('devDashboard.structureHealth.title')}
              value={`${sh.score ?? '—'}/100`}
              tone={String(sh.status || 'gray')}
              testId="dev-dashboard-structure-health-summary"
            />
          </div>

          {(section === 'overview' || section === 'gates') && (
            <>
              <RuntimeGatePanel dashboard={dashboard} t={t} />
              <SafeTestModePanel dashboard={dashboard} t={t} />
              <RuntimeWorkspacePanel dashboard={dashboard} t={t} apiBaseDisplay={apiBaseDisplay} />
              <DeployDriftPanel dashboard={dashboard} t={t} />
              <PackageGatePanel dashboard={dashboard} t={t} />
              <ReleaseGatePanel dashboard={dashboard} t={t} />
              <RecommendedActionsPanel dashboard={dashboard} t={t} />
            </>
          )}

          {(section === 'overview' || section === 'structure') && (
            <>
              <StructuralHealthPanel dashboard={dashboard} t={t} />
              <EvidencePanel dashboard={dashboard} t={t} />
              <CommitHygienePanel dashboard={dashboard} t={t} />
              <DocsConsistencyPanel dashboard={dashboard} t={t} />
              <AIExportPanel
                statusQuery={statusQuery}
                apiReachable={apiReachable}
                standaloneMetaPrompt={standaloneMetaPrompt}
              />
            </>
          )}

          {(section === 'overview' || section === 'roadmap') && <RoadmapDrawer dashboard={dashboard} t={t} />}

          {(section === 'overview' || section === 'modules') && (
            <DevDashboardBody
              t={t}
              loading={loading}
              dashboard={dashboard}
              modules={modules}
              evidenceIndex={evidenceIndex}
              filter={filter}
              onFilterChange={setFilter}
              expanded={expanded}
              onToggleModule={toggle}
              selectedId={selectedId}
              onSelectModuleId={setSelectedId}
              onRefresh={() => void loadAll()}
              postAction={postAction}
              apiBaseDisplay={apiBaseDisplay}
              hideHeader
              hideRuntimePanels
            />
          )}
        </main>
      </div>
    </div>
  )
}

export default DevelopmentDashboard
