import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { fetchApi } from '../../api'
import { toneClass } from '../../pages/devDashboardFilters'
import type { CockpitPanelProps } from './types'

export type EvidenceItem = {
  title?: string
  path?: string
  category?: string
  status?: string
  timestamp?: string
  source?: string
  summary?: string
  head?: string
  is_latest?: boolean
}

type FeedPayload = {
  recent_reports?: EvidenceItem[]
  recent_tests?: EvidenceItem[]
  items?: EvidenceItem[]
  total_count?: number
  total_reports_unfiltered?: number
  default_limit?: number
  report_filters?: {
    categories?: string[]
    statuses?: string[]
    time_ranges?: string[]
  }
}

type Props = CockpitPanelProps & {
  mode?: 'reports' | 'tests' | 'both'
  initialReports?: EvidenceItem[]
  initialTests?: EvidenceItem[]
}

const DEFAULT_LIMIT = 5

export function RecentEvidenceFeedPanel({
  t,
  mode = 'both',
  initialReports,
  initialTests,
}: Props) {
  const [category, setCategory] = useState('all')
  const [status, setStatus] = useState('all')
  const [timeRange, setTimeRange] = useState('all')
  const [search, setSearch] = useState('')
  const [showAll, setShowAll] = useState(false)
  const [loading, setLoading] = useState(!initialReports && !initialTests)
  const [error, setError] = useState<string | null>(null)
  const [feed, setFeed] = useState<FeedPayload | null>(
    initialReports || initialTests
      ? { recent_reports: initialReports, recent_tests: initialTests }
      : null,
  )

  const limit = showAll ? 20 : DEFAULT_LIMIT

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      params.set('limit', String(limit))
      if (category !== 'all') params.set('category', category)
      if (status !== 'all') params.set('status', status)
      if (timeRange !== 'all') params.set('time_range', timeRange)
      if (search.trim()) params.set('search', search.trim())
      const res = await fetchApi(`/api/dev-dashboard/recent-evidence?${params}`)
      if (!res.ok) {
        setError(`HTTP ${res.status}`)
        return
      }
      setFeed((await res.json()) as FeedPayload)
    } catch {
      setError('fetch_failed')
    } finally {
      setLoading(false)
    }
  }, [category, status, timeRange, search, limit])

  useEffect(() => {
    if (initialReports || initialTests) {
      if (category !== 'all' || status !== 'all' || timeRange !== 'all' || search.trim()) {
        void load()
      }
      return
    }
    void load()
  }, [load, initialReports, initialTests, category, status, timeRange, search])

  const reports = useMemo(
    () => feed?.recent_reports ?? feed?.items ?? initialReports ?? [],
    [feed, initialReports],
  )
  const tests = useMemo(() => feed?.recent_tests ?? initialTests ?? [], [feed, initialTests])

  const filters = feed?.report_filters

  const renderList = (items: EvidenceItem[], testId: string) => {
    if (!items.length) {
      return <p className="text-sm text-slate-400 mt-2">{t('devDashboard.recentEvidence.empty')}</p>
    }
    return (
      <ul className="mt-2 space-y-2" data-testid={testId}>
        {items.map((it) => (
          <li
            key={String(it.path || it.title)}
            className={`rounded-lg border px-3 py-2 text-xs ${toneClass(String(it.status || 'gray'))}`}
          >
            <div className="font-semibold text-white truncate">{it.title || it.path}</div>
            <div className="text-slate-400 mt-0.5 flex flex-wrap gap-2">
              <span>{String(it.timestamp || '').slice(0, 19)}</span>
              <span className="uppercase text-[10px]">{it.category}</span>
              <span className="uppercase text-[10px]">{it.status}</span>
              {it.is_latest ? (
                <span className="text-violet-300 text-[10px]">{t('devDashboard.recentEvidence.latest')}</span>
              ) : null}
            </div>
            <div className="font-mono text-[10px] text-slate-500 mt-0.5 truncate">{it.path}</div>
            {it.summary ? <p className="text-slate-300 mt-1">{it.summary}</p> : null}
          </li>
        ))}
      </ul>
    )
  }

  return (
    <section
      className="rounded-xl border border-slate-700 bg-slate-900/50 p-4"
      data-testid="dev-dashboard-recent-evidence-panel"
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-base font-semibold text-white">{t('devDashboard.recentEvidence.title')}</h2>
          <p className="text-xs text-slate-400 mt-1">
            {showAll
              ? t('devDashboard.recentEvidence.subtitleFiltered')
              : t('devDashboard.recentEvidence.subtitleDefault', { count: DEFAULT_LIMIT })}
          </p>
        </div>
        <button type="button" className="btn-secondary text-xs" onClick={() => void load()} disabled={loading}>
          {t('backup.ui.refresh')}
        </button>
      </div>

      <div className="mt-3 grid sm:grid-cols-2 lg:grid-cols-4 gap-2 text-xs" data-testid="recent-evidence-filters">
        <label className="flex flex-col gap-1 text-slate-400">
          {t('devDashboard.recentEvidence.filterCategory')}
          <select
            className="bg-slate-950 border border-slate-600 rounded px-2 py-1 text-slate-200"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          >
            <option value="all">{t('devDashboard.recentEvidence.filterAll')}</option>
            {(filters?.categories || []).map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-slate-400">
          {t('devDashboard.recentEvidence.filterStatus')}
          <select
            className="bg-slate-950 border border-slate-600 rounded px-2 py-1 text-slate-200"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="all">{t('devDashboard.recentEvidence.filterAll')}</option>
            {(filters?.statuses || []).map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-slate-400">
          {t('devDashboard.recentEvidence.filterTime')}
          <select
            className="bg-slate-950 border border-slate-600 rounded px-2 py-1 text-slate-200"
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
          >
            <option value="all">{t('devDashboard.recentEvidence.filterAll')}</option>
            {(filters?.time_ranges || ['today', '24h', '7d']).map((tr) => (
              <option key={tr} value={tr}>
                {tr}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-slate-400 sm:col-span-2 lg:col-span-1">
          {t('devDashboard.recentEvidence.filterSearch')}
          <input
            type="search"
            className="bg-slate-950 border border-slate-600 rounded px-2 py-1 text-slate-200"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('devDashboard.recentEvidence.searchPlaceholder')}
          />
        </label>
      </div>

      <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-500">
        <span>
          {t('devDashboard.recentEvidence.total')}: {feed?.total_count ?? reports.length} /{' '}
          {feed?.total_reports_unfiltered ?? '—'}
        </span>
        <button
          type="button"
          className="text-violet-300 hover:underline"
          onClick={() => setShowAll((v) => !v)}
        >
          {showAll ? t('devDashboard.recentEvidence.showFive') : t('devDashboard.recentEvidence.showMore')}
        </button>
      </div>

      {loading ? <p className="text-sm text-slate-400 mt-3">…</p> : null}
      {error ? <p className="text-sm text-red-300 mt-3">{error}</p> : null}

      {(mode === 'reports' || mode === 'both') && !loading ? (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-slate-200">{t('devDashboard.recentEvidence.reportsHeading')}</h3>
          {renderList(reports.slice(0, limit), 'recent-evidence-reports-list')}
        </div>
      ) : null}

      {(mode === 'tests' || mode === 'both') && !loading ? (
        <div className="mt-4">
          <h3 className="text-sm font-medium text-slate-200">{t('devDashboard.recentEvidence.testsHeading')}</h3>
          {renderList(tests.slice(0, limit), 'recent-evidence-tests-list')}
        </div>
      ) : null}
    </section>
  )
}
