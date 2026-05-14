import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ChevronDown, ChevronRight, RefreshCw, Terminal } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'
import PageHeader from '../components/layout/PageHeader'
import { matchesFilter, toneClass, type FilterKey } from './devDashboardFilters'

type Traffic = 'green' | 'yellow' | 'red' | 'gray' | string

type DashboardPayload = Record<string, unknown> | null

type ModuleRow = {
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

const DevDashboard: React.FC = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [dashboard, setDashboard] = useState<DashboardPayload>(null)
  const [modules, setModules] = useState<ModuleRow[]>([])
  const [evidenceIndex, setEvidenceIndex] = useState<Record<string, unknown> | null>(null)
  const [filter, setFilter] = useState<FilterKey>('all')
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const loadAll = useCallback(async () => {
    setLoading(true)
    try {
      const [r1, r2, r3] = await Promise.all([
        fetchApi('/api/dev-dashboard/status'),
        fetchApi('/api/dev-dashboard/modules'),
        fetchApi('/api/dev-dashboard/evidence-index'),
      ])
      const d1 = await r1.json().catch(() => ({}))
      const d2 = await r2.json().catch(() => ({}))
      const d3 = await r3.json().catch(() => ({}))
      setDashboard((d1?.dashboard as DashboardPayload) ?? null)
      setModules(Array.isArray(d2?.modules) ? (d2.modules as ModuleRow[]) : [])
      setEvidenceIndex(d3 && typeof d3 === 'object' ? (d3 as Record<string, unknown>) : null)
    } catch {
      toast.error(t('devDashboard.noData'))
      setDashboard(null)
      setModules([])
      setEvidenceIndex(null)
    } finally {
      setLoading(false)
    }
  }, [t])

  useEffect(() => {
    void loadAll()
  }, [loadAll])

  const filteredModules = useMemo(() => modules.filter((m) => matchesFilter(m, filter)), [modules, filter])

  useEffect(() => {
    if (!selectedId) return
    if (!filteredModules.some((m) => String(m.id || '') === selectedId)) {
      const first = filteredModules[0]
      setSelectedId(first?.id != null ? String(first.id) : null)
    }
  }, [filteredModules, selectedId])

  const selected = useMemo(
    () => filteredModules.find((x) => x.id === selectedId) || filteredModules.find((x) => x.id) || null,
    [filteredModules, selectedId],
  )

  const toggle = (id: string) => {
    setExpanded((prev) => ({ ...prev, [id]: !prev[id] }))
  }

  const postAction = async (path: string) => {
    try {
      const r = await fetchApi(path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' })
      const d = await r.json().catch(() => ({}))
      const mk = typeof d?.message_key === 'string' ? d.message_key : 'devDashboard.actions.confirmRequired'
      toast(t(mk), { icon: 'ℹ️', duration: 5000 })
    } catch {
      toast.error(t('devDashboard.noData'))
    }
  }

  const jobs = Array.isArray(dashboard?.active_backup_jobs) ? (dashboard?.active_backup_jobs as Record<string, unknown>[]) : []
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

      <div className="flex flex-wrap items-center gap-2">
        <button type="button" onClick={() => void loadAll()} className="btn-secondary inline-flex items-center gap-2" disabled={loading}>
          <RefreshCw className={loading ? 'animate-spin' : ''} size={16} />
          {t('backup.ui.refresh')}
        </button>
        {(['all', 'red', 'yellow', 'green', 'gray', 'backup', 'rescue', 'diagnostics', 'docs'] as FilterKey[]).map((k) => (
          <button
            key={k}
            type="button"
            onClick={() => setFilter(k)}
            className={`px-3 py-1.5 rounded-md text-xs border ${filter === k ? 'border-sky-500 bg-sky-900/40' : 'border-slate-600 bg-slate-800/40'}`}
          >
            {t(`devDashboard.filter.${k}`)}
          </button>
        ))}
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <div className={`rounded-xl border p-4 ${toneClass(String(dashboard?.release_gate_status || 'gray'))}`}>
          <div className="text-xs font-semibold uppercase tracking-wide opacity-80">{t('devDashboard.releaseGate')}</div>
          <div className="text-lg font-bold mt-1">{String(dashboard?.release_gate_status ?? t('devDashboard.noData'))}</div>
          <div className="text-xs mt-2 opacity-80 break-all">{String(dashboard?.release_gate_path ?? '')}</div>
        </div>
        <div className="rounded-xl border border-slate-600 bg-slate-900/50 p-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t('devDashboard.backendStatus')}</div>
          <div className="text-lg font-bold mt-1 text-white">{String(dashboard?.backend_version ?? '—')}</div>
          <div className="text-xs text-slate-400 mt-1">
            {String(dashboard?.install_profile ?? '')} · {String(dashboard?.app_edition ?? '')}
          </div>
        </div>
        <div className="rounded-xl border border-slate-600 bg-slate-900/50 p-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-400">{t('devDashboard.activeJobs')}</div>
          <div className="text-lg font-bold mt-1 text-white">{jobs.length}</div>
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
                <div key={`mod-${id}-${idx}`} className={`rounded-lg border p-3 ${toneClass(String(m.status || 'gray'))}`}>
                  <button type="button" className="w-full flex items-start gap-2 text-left" onClick={() => toggle(id)}>
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
                        setSelectedId(id)
                      }}
                    >
                      {t('devDashboard.detail.select')}
                    </button>
                  </button>
                  {open && (
                    <div className="mt-3 pl-7 text-xs space-y-2 border-t border-white/10 pt-2">
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
            <div className="rounded-lg border border-slate-600 bg-slate-900/60 p-4 space-y-3 text-sm">
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
              <ArtifactList title={t('devDashboard.evidence')} paths={selected.evidence_files} />
              <ArtifactList title={t('devDashboard.prompts')} paths={selected.prompt_files} />
              <ArtifactList title={t('devDashboard.reports')} paths={selected.report_files} />
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

          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="btn-secondary opacity-60"
              disabled
              title={t('devDashboard.actions.confirmRequired')}
            >
              {t('devDashboard.actions.restartBackend')}
            </button>
            <button type="button" className="btn-secondary" onClick={() => void postAction('/api/dev-dashboard/actions/restart-backend')}>
              {t('devDashboard.actions.restartBackendProbe')}
            </button>
            <button type="button" className="btn-secondary" onClick={() => void postAction('/api/dev-dashboard/actions/start-backup')}>
              {t('devDashboard.actions.startBackupProbe')}
            </button>
          </div>
        </div>
      </div>
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

function ArtifactList({ title, paths }: { title: string; paths?: string[] }) {
  const rows = paths || []
  if (!rows.length) return null
  return (
    <div>
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

export default DevDashboard
