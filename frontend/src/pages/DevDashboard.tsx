import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { fetchApi, getApiBase, normalizeApiBaseUrl } from '../api'
import { DevDashboardBody, type DashboardPayload, type ModuleRow } from './DevDashboardBody'
import { matchesFilter, type FilterKey } from './devDashboardFilters'

const DevDashboard: React.FC = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [dashboard, setDashboard] = useState<DashboardPayload>(null)
  const [modules, setModules] = useState<ModuleRow[]>([])
  const [evidenceIndex, setEvidenceIndex] = useState<Record<string, unknown> | null>(null)
  const [filter, setFilter] = useState<FilterKey>('all')
  const [expanded, setExpanded] = useState<Record<string, boolean>>({})
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const [apiBaseDisplay, setApiBaseDisplay] = useState('')

  const devDashboardStatusUrl = useCallback(() => {
    const params = new URLSearchParams()
    const fv =
      typeof __APP_VERSION__ !== 'undefined' && String(__APP_VERSION__).trim() ? String(__APP_VERSION__).trim() : ''
    if (fv) params.set('frontend_build_version', fv)
    params.set('frontend_runtime_source', import.meta.env.DEV ? 'dev' : 'build')
    const q = params.toString()
    return `/api/dev-dashboard/status?${q}`
  }, [])

  const loadAll = useCallback(async () => {
    setLoading(true)
    try {
      const base = getApiBase()
      setApiBaseDisplay(base ? normalizeApiBaseUrl(base) : t('app.apiConsistency.apiBase.sameOrigin'))
      const [r1, r2, r3] = await Promise.all([
        fetchApi(devDashboardStatusUrl()),
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
  }, [t, devDashboardStatusUrl])

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

  return (
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
    />
  )
}

export default DevDashboard
