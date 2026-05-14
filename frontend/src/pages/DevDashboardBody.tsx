import React from 'react'
import type { TFunction } from 'i18next'
import { ChevronDown, ChevronRight, RefreshCw, Terminal } from 'lucide-react'
import PageHeader from '../components/layout/PageHeader'
import { matchesFilter, toneClass, type FilterKey } from './devDashboardFilters'

export type Traffic = 'green' | 'yellow' | 'red' | 'gray' | string

export type DashboardPayload = Record<string, unknown> | null

export type ModuleRow = {
  id?: string
  title?: string
  area?: string
  status?: Traffic
  summary?: string
  current_focus?: string
  next_steps?: string[]
  blockers?: string[]
  evidence_files?: string[]
  prompt_files?: string[]
  report_files?: string[]
  docs?: string[]
  faq?: string[]
  knowledge_base?: string[]
  diagnostics?: string[]
  i18n?: string[]
  tests?: string[]
  children?: ModuleRow[]
  artifact_status?: Array<{ path?: string; exists?: boolean; kind?: string }>
}

export type DevDashboardBodyProps = {
  t: TFunction
  loading: boolean
  dashboard: DashboardPayload
  modules: ModuleRow[]
  evidenceIndex: Record<string, unknown> | null
  filter: FilterKey
  onFilterChange: (f: FilterKey) => void
  expanded: Record<string, boolean>
  onToggleModule: (id: string) => void
  selectedId: string | null
  onSelectModuleId: (id: string) => void
  onRefresh: () => void
  postAction: (path: string) => void | Promise<void>
  /** Anzeige der konfigurierten API-Basis (Browser); optional. */
  apiBaseDisplay?: string
}

export function DevDashboardBody({
  t,
  loading,
  dashboard,
  modules,
  evidenceIndex,
  filter,
  onFilterChange,
  expanded,
  onToggleModule,
  selectedId,
  onSelectModuleId,
  onRefresh,
  postAction,
  apiBaseDisplay,
}: DevDashboardBodyProps) {
  const filteredModules = modules.filter((m) => matchesFilter(m, filter))

  const selected =
    filteredModules.find((x) => x.id === selectedId) || filteredModules.find((x) => x.id) || null

  const jobs = Array.isArray(dashboard?.active_backup_jobs)
    ? (dashboard?.active_backup_jobs as Record<string, unknown>[])
    : []
  const mounts = Array.isArray(dashboard?.mount_summary) ? (dashboard?.mount_summary as Record<string, string>[]) : []

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-6 text-slate-100">
      <PageHeader
        visualStyle="tech-panel"
        tone="settings"
        title={t('devDashboard.title')}
        subtitle={t('devDashboard.subtitle')}
        badge={<Terminal className="text-violet-400 shrink-0" size={28} aria-hidden />}
      />

      <div className="rounded-lg border border-amber-700/50 bg-amber-950/30 px-4 py-3 text-sm text-amber-100">
        {t('devDashboard.expertOnlyNotice')}
      </div>
      <div className="rounded-lg border border-slate-600 bg-slate-900/50 px-4 py-3 text-sm text-slate-300">
        {t('devDashboard.readOnlyNotice')}
      </div>

      <RuntimeWorkspacePanel dashboard={dashboard} t={t} apiBaseDisplay={apiBaseDisplay} />

      <DeployDriftPanel dashboard={dashboard} t={t} />

      <div className="flex flex-wrap items-center gap-2">
        <button type="button" onClick={() => onRefresh()} className="btn-secondary inline-flex items-center gap-2" disabled={loading}>
          <RefreshCw className={loading ? 'animate-spin' : ''} size={16} />
          {t('backup.ui.refresh')}
        </button>
        {(['all', 'red', 'yellow', 'green', 'gray', 'backup', 'rescue', 'diagnostics', 'docs'] as FilterKey[]).map((k) => (
          <button
            key={k}
            type="button"
            data-testid={`dev-dashboard-filter-${k}`}
            onClick={() => onFilterChange(k)}
            className={`px-3 py-1.5 rounded-md text-xs border ${filter === k ? 'border-sky-500 bg-sky-900/40' : 'border-slate-600 bg-slate-800/40'}`}
          >
            {t(`devDashboard.filter.${k}`)}
          </button>
        ))}
      </div>

      <div className="grid md:grid-cols-3 gap-4" data-testid="dev-dashboard-status-cards">
        <div className={`rounded-xl border p-4 ${toneClass(String(dashboard?.release_gate_status || 'gray'))}`}>
          <div className="text-xs font-semibold uppercase tracking-wide opacity-80">{t('devDashboard.releaseGate')}</div>
          <div className="text-lg font-bold mt-1" data-testid="dev-dashboard-gate-value">
            {String(dashboard?.release_gate_status ?? t('devDashboard.noData'))}
          </div>
          <div className="text-xs mt-2 opacity-80 break-all">{String(dashboard?.release_gate_path ?? '')}</div>
        </div>
        <div className="rounded-xl border border-slate-600 bg-slate-900/50 p-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t('devDashboard.backendStatus')}</div>
          <div className="text-lg font-bold mt-1 text-white" data-testid="dev-dashboard-backend-version">
            {String(dashboard?.backend_version ?? '—')}
          </div>
          <div className="text-xs text-slate-400 mt-1">
            {String(dashboard?.install_profile ?? '')} · {String(dashboard?.app_edition ?? '')}
          </div>
        </div>
        <div className="rounded-xl border border-slate-600 bg-slate-900/50 p-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t('devDashboard.activeJobs')}</div>
          <div className="text-lg font-bold mt-1 text-white" data-testid="dev-dashboard-job-count">
            {jobs.length}
          </div>
          <div className="text-xs text-slate-400 mt-1">{t('devDashboard.modules')}</div>
        </div>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="space-y-3">
          <h2 className="text-lg font-semibold text-sky-300">{t('devDashboard.modules')}</h2>
          {filteredModules.length === 0 ? (
            <p className="text-sm text-slate-400">{t('devDashboard.noData')}</p>
          ) : (
            filteredModules.map((m, idx) => {
              const id = String(m.id || `row-${idx}`)
              const open = !!expanded[id]
              return (
                <div
                  key={`mod-${id}-${idx}`}
                  data-testid={`dev-dashboard-mod-${id}`}
                  className={`rounded-lg border p-3 ${toneClass(String(m.status || 'gray'))}`}
                >
                  <button type="button" className="w-full flex items-start gap-2 text-left" onClick={() => onToggleModule(id)}>
                    {open ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-white">{m.title || id}</div>
                      <div className="text-xs opacity-90 line-clamp-2">{m.summary}</div>
                    </div>
                    <button
                      type="button"
                      className="text-xs underline shrink-0"
                      onClick={(e) => {
                        e.stopPropagation()
                        onSelectModuleId(id)
                      }}
                    >
                      {t('devDashboard.detail.select')}
                    </button>
                  </button>
                  {open && (
                    <div className="mt-3 pl-7 text-xs space-y-2 border-t border-white/10 pt-2" data-testid={`dev-dashboard-mod-expanded-${id}`}>
                      <div>
                        <span className="font-semibold">{t('devDashboard.status.label')}:</span> {String(m.status)}
                      </div>
                      {Array.isArray(m.next_steps) && m.next_steps.length > 0 && (
                        <div>
                          <div className="font-semibold">{t('devDashboard.nextSteps')}</div>
                          <ul className="list-disc pl-4">
                            {m.next_steps.map((s) => (
                              <li key={s}>{s}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {Array.isArray(m.children) && m.children.length > 0 && (
                        <div>
                          <div className="font-semibold">{t('devDashboard.detail.submodules')}</div>
                          <ul className="list-none space-y-1 pl-0">
                            {m.children.map((ch, ci) => (
                              <li
                                key={`${id}-ch-${String(ch.id || ci)}`}
                                className={`rounded border px-2 py-1 ${toneClass(String(ch.status || 'gray'))}`}
                              >
                                <span className="font-medium text-white">{ch.title || ch.id}</span>
                                {ch.summary ? <span className="block text-slate-300 mt-0.5">{ch.summary}</span> : null}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>

        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-sky-300">{t('devDashboard.detail.title')}</h2>
          {!selected ? (
            <p className="text-sm text-slate-400">{t('devDashboard.noData')}</p>
          ) : (
            <div className="rounded-lg border border-slate-600 bg-slate-900/60 p-4 space-y-3 text-sm" data-testid="dev-dashboard-detail-panel">
              <div className="font-bold text-white text-base">{selected.title}</div>
              <p className="text-slate-300">{selected.summary}</p>
              <div>
                <div className="font-semibold text-sky-200">{t('devDashboard.blockers')}</div>
                <ul className="list-disc pl-4 text-slate-300">
                  {(selected.blockers || []).length ? (
                    selected.blockers!.map((b) => <li key={b}>{b}</li>)
                  ) : (
                    <li>{t('devDashboard.noData')}</li>
                  )}
                </ul>
              </div>
              <ArtifactList dataTestId="evidence" title={t('devDashboard.evidence')} paths={selected.evidence_files} />
              <ArtifactList dataTestId="prompts" title={t('devDashboard.prompts')} paths={selected.prompt_files} />
              <ArtifactList dataTestId="reports" title={t('devDashboard.reports')} paths={selected.report_files} />
              <div>
                <div className="font-semibold text-sky-200">{t('devDashboard.docs')}</div>
                <PathList paths={selected.docs} artifacts={selected.artifact_status} />
              </div>
              <div>
                <div className="font-semibold text-sky-200">{t('devDashboard.knowledgeBase')}</div>
                <PathList paths={selected.knowledge_base} artifacts={selected.artifact_status} />
              </div>
              <div>
                <div className="font-semibold text-sky-200">{t('devDashboard.i18n')}</div>
                <PathList paths={selected.i18n} artifacts={selected.artifact_status} />
              </div>
              <div>
                <div className="font-semibold text-sky-200">{t('devDashboard.tests')}</div>
                <PathList paths={selected.tests} artifacts={selected.artifact_status} />
              </div>
            </div>
          )}

          <div className="rounded-lg border border-slate-600 bg-slate-900/40 p-4">
            <h3 className="text-sm font-semibold text-slate-200 mb-2">{t('devDashboard.mounts')}</h3>
            <div className="max-h-48 overflow-y-auto text-xs font-mono space-y-1">
              {mounts.length === 0 ? (
                <span className="text-slate-500">{t('devDashboard.noData')}</span>
              ) : (
                mounts.map((ln, i) => (
                  <div key={i} className="truncate text-slate-300">
                    {ln.mountpoint} <span className="text-slate-500">({ln.fstype})</span>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-lg border border-slate-600 bg-slate-900/40 p-4">
            <h3 className="text-sm font-semibold text-slate-200 mb-2">{t('devDashboard.activeJobs')}</h3>
            <pre className="text-xs text-slate-400 max-h-40 overflow-auto whitespace-pre-wrap">{JSON.stringify(jobs, null, 0)}</pre>
          </div>

          <div className="rounded-lg border border-slate-600 bg-slate-900/40 p-4">
            <h3 className="text-sm font-semibold text-slate-200 mb-2">{t('devDashboard.evidence')}</h3>
            <pre className="text-xs text-slate-400 max-h-32 overflow-auto whitespace-pre-wrap">
              {evidenceIndex ? JSON.stringify(evidenceIndex.buckets ?? evidenceIndex, null, 0) : t('devDashboard.noData')}
            </pre>
          </div>

          <div className="flex flex-wrap gap-2" data-testid="dev-dashboard-action-row">
            <button
              type="button"
              className="btn-secondary opacity-60"
              disabled
              data-testid="dev-dashboard-restart-disabled"
              title={t('devDashboard.actions.confirmRequired')}
            >
              {t('devDashboard.actions.restartBackend')}
            </button>
            <button
              type="button"
              className="btn-secondary"
              data-testid="dev-dashboard-restart-probe"
              onClick={() => void postAction('/api/dev-dashboard/actions/restart-backend')}
            >
              {t('devDashboard.actions.restartBackendProbe')}
            </button>
            <button
              type="button"
              className="btn-secondary"
              data-testid="dev-dashboard-backup-probe"
              onClick={() => void postAction('/api/dev-dashboard/actions/start-backup')}
            >
              {t('devDashboard.actions.startBackupProbe')}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function DeployDriftPanel({ dashboard, t }: { dashboard: DashboardPayload; t: TFunction }) {
  if (!dashboard) return null
  const dd = dashboard.deploy_drift as Record<string, unknown> | undefined
  if (!dd) return null
  const st = String(dd.status || 'gray')
  const borderTone =
    st === 'red'
      ? 'border-rose-500/70 bg-rose-950/30'
      : st === 'yellow'
        ? 'border-amber-500/70 bg-amber-950/25'
        : st === 'gray'
          ? 'border-slate-500/60 bg-slate-900/40'
          : 'border-emerald-600/50 bg-emerald-950/20'
  const tri =
    st === 'red'
      ? t('devDashboard.status.red')
      : st === 'yellow'
        ? t('devDashboard.status.yellow')
        : st === 'gray'
          ? t('devDashboard.status.gray')
          : t('devDashboard.status.green')
  const checked = Array.isArray(dd.checked_files) ? (dd.checked_files as Record<string, unknown>[]) : []
  const missRt = Array.isArray(dd.missing_runtime_files) ? (dd.missing_runtime_files as string[]) : []
  const missWs = Array.isArray(dd.missing_workspace_files) ? (dd.missing_workspace_files as string[]) : []
  const ddWarns = Array.isArray(dd.warnings) ? (dd.warnings as string[]) : []
  const actions = Array.isArray(dd.suggested_actions) ? (dd.suggested_actions as string[]) : []

  return (
    <div className={`rounded-xl border p-4 space-y-3 ${borderTone}`} data-testid="dev-dashboard-deploy-drift-card">
      <div>
        <h2 className="text-base font-semibold text-white">{t('devDashboard.deployDrift.title')}</h2>
        <p className="text-xs text-slate-300 mt-1">{t('devDashboard.deployDrift.subtitle')}</p>
      </div>
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="text-slate-400">{t('devDashboard.deployDrift.statusLabel')}</span>
        <span className="font-mono font-bold text-white">{tri}</span>
        <span className="text-xs text-slate-500">({st})</span>
      </div>
      <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-2 text-xs text-slate-200">
        <div className="sm:col-span-2">
          <dt className="text-slate-500">{t('devDashboard.deployDrift.runtimeRoot')}</dt>
          <dd className="font-mono break-all text-slate-300">{String(dd.runtime_root ?? '—')}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-slate-500">{t('devDashboard.deployDrift.workspaceRoot')}</dt>
          <dd className="font-mono break-all text-slate-300">{String(dd.workspace_root ?? '—')}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.deployDrift.checkedCount')}</dt>
          <dd>{checked.length}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.deployDrift.matching')}</dt>
          <dd>{String(dd.matching_files_count ?? '—')}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.deployDrift.differing')}</dt>
          <dd>{String(dd.differing_files_count ?? '—')}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.deployDrift.missingRuntime')}</dt>
          <dd className="break-all">{missRt.length ? missRt.join(', ') : '—'}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.deployDrift.missingWorkspace')}</dt>
          <dd className="break-all">{missWs.length ? missWs.join(', ') : '—'}</dd>
        </div>
      </dl>
      <div className="text-xs border-t border-white/10 pt-2 grid sm:grid-cols-2 gap-2">
        <div>
          <div className="font-semibold text-slate-200">{t('devDashboard.deployDrift.manifest.workspace')}</div>
          <div className="text-slate-400">
            {Boolean(dd.manifest_available_workspace) ? t('devDashboard.deployDrift.manifest.present') : t('devDashboard.deployDrift.manifest.absent')}
          </div>
        </div>
        <div>
          <div className="font-semibold text-slate-200">{t('devDashboard.deployDrift.manifest.runtime')}</div>
          <div className="text-slate-400">
            {Boolean(dd.manifest_available_runtime) ? t('devDashboard.deployDrift.manifest.present') : t('devDashboard.deployDrift.manifest.absent')}
          </div>
        </div>
        <div className="sm:col-span-2">
          <div className="font-semibold text-slate-200">{t('devDashboard.deployDrift.manifest.match')}</div>
          <div className="text-slate-400">
            {dd.manifest_match === true
              ? '✓'
              : dd.manifest_match === false
                ? '✗'
                : t('devDashboard.deployDrift.manifest.unknown')}
          </div>
        </div>
      </div>
      <div className="text-xs">
        <div className="font-semibold text-slate-200 mb-1">{t('devDashboard.deployDrift.suggested')}</div>
        <ul className="list-disc pl-4 space-y-0.5 text-sky-100/90">
          {actions.map((a) => (
            <li key={a}>{t(`devDashboard.deployDrift.action.${a}`, { defaultValue: a })}</li>
          ))}
        </ul>
      </div>
      {Array.isArray(dd.manifest_warnings) && (dd.manifest_warnings as string[]).length > 0 ? (
        <div className="text-xs border-t border-white/10 pt-2">
          <div className="font-semibold text-slate-300 mb-1">{t('devDashboard.deployDrift.manifestNotes')}</div>
          <ul className="list-disc pl-4 text-amber-100/90">
            {(dd.manifest_warnings as string[]).slice(0, 8).map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {ddWarns.length > 0 ? (
        <div className="text-xs border-t border-white/10 pt-2">
          <div className="font-semibold text-slate-300 mb-1">{t('devDashboard.deployDrift.warnings')}</div>
          <ul className="list-disc pl-4 text-amber-100/90">
            {ddWarns.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {checked.length > 0 ? (
        <div className="text-xs border-t border-white/10 pt-2">
          <div className="font-semibold text-slate-200 mb-1">{t('devDashboard.deployDrift.details')}</div>
          <div className="max-h-40 overflow-y-auto space-y-1 font-mono text-slate-400">
            {checked.map((row) => (
              <div key={String(row.relative_path)} className="flex flex-wrap gap-x-2">
                <span className="text-slate-300">{String(row.relative_path)}</span>
                <span>
                  {t('devDashboard.deployDrift.matches')}:{' '}
                  {row.matches === true ? '✓' : row.matches === false ? '✗' : '—'}
                </span>
                {row.reason ? <span className="text-slate-500">({String(row.reason)})</span> : null}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  )
}

function RuntimeWorkspacePanel({
  dashboard,
  t,
  apiBaseDisplay,
}: {
  dashboard: DashboardPayload
  t: TFunction
  apiBaseDisplay?: string
}) {
  if (!dashboard) return null
  const runtime = dashboard.runtime as Record<string, unknown> | undefined
  const workspace = dashboard.workspace as Record<string, unknown> | undefined
  const frontend = dashboard.frontend as Record<string, unknown> | undefined
  const consistency = dashboard.consistency as Record<string, unknown> | undefined
  const st = String(consistency?.status || 'gray')
  const borderTone =
    st === 'red'
      ? 'border-rose-500/70 bg-rose-950/30'
      : st === 'yellow'
        ? 'border-amber-500/70 bg-amber-950/25'
        : st === 'gray'
          ? 'border-slate-500/60 bg-slate-900/40'
          : 'border-emerald-600/50 bg-emerald-950/20'
  const feSrc = String(frontend?.frontend_runtime_source || 'unknown')
  const feSrcLabel = t(`devDashboard.runtimeWorkspace.source.${feSrc}`, {
    defaultValue: feSrc,
  })
  const cw = Array.isArray(consistency?.warnings) ? (consistency?.warnings as string[]) : []
  const tri =
    st === 'red'
      ? t('devDashboard.status.red')
      : st === 'yellow'
        ? t('devDashboard.status.yellow')
        : st === 'gray'
          ? t('devDashboard.status.gray')
          : t('devDashboard.status.green')

  const fmtTri = (v: unknown) => (v === true ? '✓' : v === false ? '✗' : '—')

  return (
    <div
      className={`rounded-xl border p-4 space-y-3 ${borderTone}`}
      data-testid="dev-dashboard-runtime-workspace-card"
    >
      <div>
        <h2 className="text-base font-semibold text-white">{t('devDashboard.runtimeWorkspace.title')}</h2>
        <p className="text-xs text-slate-300 mt-1">{t('devDashboard.runtimeWorkspace.subtitle')}</p>
      </div>
      <div className="flex flex-wrap items-center gap-3 text-sm">
        <span className="text-slate-400">{t('devDashboard.runtimeWorkspace.consistency')}:</span>
        <span className="font-mono font-bold text-white">{tri}</span>
        <span className="text-xs text-slate-500">({st})</span>
      </div>
      {apiBaseDisplay ? (
        <div className="text-xs text-slate-400">
          {t('devDashboard.runtimeWorkspace.apiBase')}: <code className="text-slate-200 break-all">{apiBaseDisplay}</code>
        </div>
      ) : null}
      <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-2 text-xs text-slate-200">
        <div>
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.backendVersion')}</dt>
          <dd className="font-mono break-all">{String(runtime?.backend_project_version ?? runtime?.backend_version ?? '—')}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.workspaceVersion')}</dt>
          <dd className="font-mono break-all">{String(workspace?.workspace_version ?? '—')}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.frontendBuild')}</dt>
          <dd className="font-mono break-all">{String(frontend?.frontend_build_version ?? '—')}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.frontendSource')}</dt>
          <dd>{feSrcLabel}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.runtimePath')}</dt>
          <dd className="font-mono break-all text-slate-300">{String(runtime?.backend_runtime_path ?? '—')}</dd>
        </div>
        <div className="sm:col-span-2">
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.workspacePath')}</dt>
          <dd className="font-mono break-all text-slate-300">{String(workspace?.workspace_path ?? '—')}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.gitHead')}</dt>
          <dd className="font-mono break-all">{String(workspace?.git_head ?? '—')}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.gitBranch')}</dt>
          <dd className="font-mono break-all">{String(workspace?.git_branch ?? '—')}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.dirtyCount')}</dt>
          <dd>{workspace?.git_dirty_count != null ? String(workspace.git_dirty_count) : '—'}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.unpushedCount')}</dt>
          <dd>{workspace?.git_unpushed_count != null ? String(workspace.git_unpushed_count) : '—'}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.workspaceMatches')}</dt>
          <dd className="font-mono">{fmtTri(consistency?.backend_workspace_match)}</dd>
        </div>
        <div>
          <dt className="text-slate-500">{t('devDashboard.runtimeWorkspace.frontendMatches')}</dt>
          <dd className="font-mono">{fmtTri(consistency?.frontend_backend_match)}</dd>
        </div>
      </dl>
      {cw.length > 0 ? (
        <div className="text-xs border-t border-white/10 pt-2">
          <div className="font-semibold text-slate-300 mb-1">{t('devDashboard.runtimeWorkspace.warnings')}</div>
          <ul className="list-disc pl-4 space-y-0.5 text-amber-100/90">
            {cw.map((w) => (
              <li key={w}>{t(`devDashboard.runtimeWorkspace.warn.${w}`, { defaultValue: w })}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  )
}

function PathList({
  paths,
  artifacts,
}: {
  paths?: string[]
  artifacts?: Array<{ path?: string; exists?: boolean; kind?: string }>
}) {
  const rows = paths || []
  if (!rows.length) return <p className="text-xs text-slate-500">—</p>
  return (
    <ul className="list-none space-y-1 text-xs">
      {rows.map((p) => {
        const art = artifacts?.find((a) => a.path === p)
        const ok = art?.exists
        return (
          <li key={p} className="flex gap-2">
            <span className={ok ? 'text-emerald-400' : 'text-slate-500'}>{ok ? '●' : '○'}</span>
            <code className="break-all text-slate-300">{p}</code>
          </li>
        )
      })}
    </ul>
  )
}

function ArtifactList({ title, paths, dataTestId }: { title: string; paths?: string[]; dataTestId: string }) {
  const rows = paths || []
  if (!rows.length) return null
  return (
    <div data-testid={`dev-dashboard-artifact-${dataTestId}`}>
      <div className="font-semibold text-sky-200">{title}</div>
      <ul className="list-disc pl-4 text-xs text-slate-300">
        {rows.map((p) => (
          <li key={p}>
            <code className="break-all">{p}</code>
          </li>
        ))}
      </ul>
    </div>
  )
}
