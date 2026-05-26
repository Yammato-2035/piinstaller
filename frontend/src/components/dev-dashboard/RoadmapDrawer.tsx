import React, { useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { Copy, Download, Eye } from 'lucide-react'
import { fetchApi } from '../../api'
import type { CockpitPanelProps } from './types'

type RoadmapDrawerProps = CockpitPanelProps & {
  apiReachable?: boolean
}

type JsonRow = Record<string, unknown>

function asRows(value: unknown): JsonRow[] {
  return Array.isArray(value) ? (value as JsonRow[]) : []
}

function localized(row: JsonRow, base: string): string {
  const de = row[`${base}_de`]
  const en = row[`${base}_en`]
  const direct = row[base]
  return String(de || direct || en || row.id || '—')
}

function localizedReason(row: JsonRow): string {
  const decision = String(row.decision_de || row.reason_de || row.description_de || row.summary || '').trim()
  return decision || '—'
}

function toneForStatus(status: string): string {
  if (status === 'green') return 'border-emerald-700/50 bg-emerald-950/20 text-emerald-100'
  if (status === 'partial_green') return 'border-teal-700/50 bg-teal-950/20 text-teal-100'
  if (status === 'yellow') return 'border-amber-700/50 bg-amber-950/20 text-amber-100'
  if (status === 'blocked' || status === 'red') return 'border-red-700/50 bg-red-950/20 text-red-100'
  if (status === 'deferred') return 'border-slate-600 bg-slate-900/50 text-slate-200'
  return 'border-slate-700 bg-slate-900/40 text-slate-200'
}

function displayRange(row: JsonRow): string {
  const start = String(row.planned_start || '').trim()
  const end = String(row.planned_end || '').trim()
  if (start && end) return `${start} → ${end}`
  if (start) return start
  if (end) return end
  return '—'
}

function buildTreeRows(areas: JsonRow[]): Array<{ key: string; level: number; row: JsonRow; kind: 'area' | 'milestone' | 'task' }> {
  const rows: Array<{ key: string; level: number; row: JsonRow; kind: 'area' | 'milestone' | 'task' }> = []
  for (const area of areas) {
    rows.push({ key: `area-${String(area.id)}`, level: 0, row: area, kind: 'area' })
    for (const milestone of asRows(area.milestones)) {
      rows.push({ key: `milestone-${String(milestone.id)}`, level: 1, row: milestone, kind: 'milestone' })
      for (const task of asRows(milestone.tasks)) {
        rows.push({ key: `task-${String(task.id)}`, level: 2, row: task, kind: 'task' })
      }
    }
  }
  return rows
}

function fallbackItems(roadmap: JsonRow): JsonRow[] {
  const tabs = (roadmap.tabs as Record<string, JsonRow[]>) || {}
  return [
    ...(tabs.created || []),
    ...(tabs.in_progress || []),
    ...(tabs.planned || []),
    ...(tabs.blocked || []),
  ]
}

export function RoadmapDrawer({ dashboard, t, apiReachable = true }: RoadmapDrawerProps) {
  const roadmap = (dashboard?.roadmap as JsonRow) || {}
  const areas = asRows(roadmap.areas)
  const summary = (roadmap.summary as JsonRow) || {}
  const statusCounts = (summary.status_counts as Record<string, number>) || {}
  const recommendedPrompt = (roadmap.recommended_prompt as JsonRow) || null
  const nextPrompts = asRows(roadmap.next_prompts)
  const runtimeOverlay = (roadmap.runtime_overlay as JsonRow) || {}
  const [promptText, setPromptText] = useState('')
  const [loadingPrompt, setLoadingPrompt] = useState(false)

  const restoreArea = useMemo(() => areas.find((row) => String(row.id) === 'restore') || null, [areas])
  const diagnosticsArea = useMemo(() => areas.find((row) => String(row.id) === 'diagnostics') || null, [areas])
  const rows = useMemo(() => buildTreeRows(areas), [areas])
  const promptUnlocks = Array.isArray(recommendedPrompt?.unlocks) ? (recommendedPrompt?.unlocks as string[]) : []
  const promptBlockers = Array.isArray(recommendedPrompt?.blocked_by) ? (recommendedPrompt?.blocked_by as string[]) : []

  const promptById = useMemo(() => {
    const map = new Map<string, JsonRow>()
    for (const prompt of nextPrompts) {
      const id = String(prompt.id || '').trim()
      if (id) map.set(id, prompt)
    }
    return map
  }, [nextPrompts])

  const loadPromptExport = async (): Promise<string | null> => {
    const promptId = String(recommendedPrompt?.id || '').trim()
    if (!promptId) return null
    if (!apiReachable) {
      const localPrompt = String(recommendedPrompt?.prompt_text || '').trim()
      return localPrompt || null
    }
    const response = await fetchApi(`/api/dev-dashboard/roadmap/export-next-prompt/${encodeURIComponent(promptId)}`)
    if (!response.ok) {
      throw new Error(`prompt_export_${response.status}`)
    }
    return await response.text()
  }

  const showPrompt = async () => {
    setLoadingPrompt(true)
    try {
      const text = await loadPromptExport()
      if (!text) {
        toast.error(t('devDashboard.noData'))
        return
      }
      setPromptText(text)
    } catch {
      toast.error(t('devDashboard.noData'))
    } finally {
      setLoadingPrompt(false)
    }
  }

  const copyPrompt = async () => {
    setLoadingPrompt(true)
    try {
      const text = await loadPromptExport()
      if (!text || !navigator.clipboard) {
        toast.error(t('devDashboard.noData'))
        return
      }
      await navigator.clipboard.writeText(text)
      setPromptText(text)
      toast.success(t('devDashboard.roadmap.copyPromptSuccess'))
    } catch {
      toast.error(t('devDashboard.noData'))
    } finally {
      setLoadingPrompt(false)
    }
  }

  const exportPrompt = async () => {
    setLoadingPrompt(true)
    try {
      const text = await loadPromptExport()
      const promptId = String(recommendedPrompt?.id || 'next-prompt').trim() || 'next-prompt'
      if (!text) {
        toast.error(t('devDashboard.noData'))
        return
      }
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${promptId}.md`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      setPromptText(text)
      toast.success(t('devDashboard.roadmap.exportPromptSuccess'))
    } catch {
      toast.error(t('devDashboard.noData'))
    } finally {
      setLoadingPrompt(false)
    }
  }

  if (areas.length === 0) {
    const items = fallbackItems(roadmap)
    return (
      <section className="rounded-xl border border-violet-700/40 bg-violet-950/15 p-4" data-testid="dev-dashboard-roadmap-panel">
        <h2 className="text-base font-semibold text-white">{t('devDashboard.roadmap.title')}</h2>
        <p className="text-xs text-slate-400 mt-1">{String(roadmap.validation_warnings || t('devDashboard.roadmap.noHistory'))}</p>
        <ul className="mt-4 space-y-2 text-xs">
          {items.length ? (
            items.slice(0, 12).map((item, index) => (
              <li key={`${String(item.title || item.id)}-${index}`} className="rounded border border-slate-700/50 p-2">
                <div className="font-semibold text-slate-100">{String(item.title || item.id)}</div>
                <div className="text-slate-400">{String(item.status || 'unknown')}</div>
              </li>
            ))
          ) : (
            <li className="text-slate-500">{t('devDashboard.noData')}</li>
          )}
        </ul>
      </section>
    )
  }

  return (
    <section className="space-y-4 rounded-xl border border-violet-700/40 bg-violet-950/15 p-4" data-testid="dev-dashboard-roadmap-panel">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h2 className="text-base font-semibold text-white">{t('devDashboard.roadmap.title')}</h2>
          <p className="text-xs text-slate-300 mt-1">{t('devDashboard.roadmap.subtitle')}</p>
        </div>
        <div className="text-xs text-slate-400">
          {t('devDashboard.roadmap.runtimeOverlay')}: {String(runtimeOverlay.runtime_gate_status || t('devDashboard.standalone.unavailable'))}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6" data-testid="dev-dashboard-roadmap-summary">
        <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-3">
          <div className="text-[11px] uppercase tracking-wide text-slate-400">{t('devDashboard.roadmap.overallStatus')}</div>
          <div className="mt-1 text-sm font-semibold text-white">{String(summary.overall_status || 'unknown')}</div>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-3">
          <div className="text-[11px] uppercase tracking-wide text-slate-400">{t('devDashboard.roadmap.greenCount')}</div>
          <div className="mt-1 text-sm font-semibold text-white">{statusCounts.green ?? 0}</div>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-3">
          <div className="text-[11px] uppercase tracking-wide text-slate-400">{t('devDashboard.roadmap.partialGreenCount')}</div>
          <div className="mt-1 text-sm font-semibold text-white">{statusCounts.partial_green ?? 0}</div>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-3">
          <div className="text-[11px] uppercase tracking-wide text-slate-400">{t('devDashboard.roadmap.blockedCount')}</div>
          <div className="mt-1 text-sm font-semibold text-white">{(statusCounts.blocked ?? 0) + (statusCounts.red ?? 0)}</div>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-3">
          <div className="text-[11px] uppercase tracking-wide text-slate-400">{t('devDashboard.roadmap.deferredCount')}</div>
          <div className="mt-1 text-sm font-semibold text-white">{statusCounts.deferred ?? 0}</div>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-900/50 p-3">
          <div className="text-[11px] uppercase tracking-wide text-slate-400">{t('devDashboard.roadmap.recommendedPrompt')}</div>
          <div className="mt-1 text-sm font-semibold text-white">{localized(recommendedPrompt || {}, 'title')}</div>
        </div>
      </div>

      {restoreArea ? (
        <div className={`rounded-lg p-3 ${toneForStatus(String(restoreArea.status || 'deferred'))}`} data-testid="dev-dashboard-roadmap-restore-hint">
          <div className="text-sm font-semibold">{t('devDashboard.roadmap.restoreDeferredTitle')}</div>
          <p className="mt-1 text-xs">{localizedReason(asRows(restoreArea.decisions)[0] || restoreArea)}</p>
        </div>
      ) : null}

      {diagnosticsArea ? (
        <div className={`rounded-lg p-3 ${toneForStatus(String(diagnosticsArea.status || 'partial_green'))}`} data-testid="dev-dashboard-roadmap-diagnostics-hint">
          <div className="text-sm font-semibold">{t('devDashboard.roadmap.diagnosticsPartialTitle')}</div>
          <p className="mt-1 text-xs">{localizedReason(asRows(diagnosticsArea.decisions)[0] || diagnosticsArea)}</p>
        </div>
      ) : null}

      <div className="rounded-xl border border-indigo-700/40 bg-indigo-950/20 p-4" data-testid="dev-dashboard-roadmap-next-prompt-card">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="space-y-1">
            <div className="text-[11px] uppercase tracking-wide text-indigo-300">{t('devDashboard.roadmap.recommendedPrompt')}</div>
            <h3 className="text-sm font-semibold text-white">{localized(recommendedPrompt || {}, 'title')}</h3>
            <p className="text-xs text-slate-300">{String(recommendedPrompt?.reason_de || t('devDashboard.noData'))}</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="btn-secondary inline-flex items-center gap-1 text-xs"
              onClick={() => void showPrompt()}
              disabled={loadingPrompt || !recommendedPrompt}
              data-testid="dev-dashboard-roadmap-show-prompt"
            >
              <Eye size={14} />
              {t('devDashboard.roadmap.showPrompt')}
            </button>
            <button
              type="button"
              className="btn-secondary inline-flex items-center gap-1 text-xs"
              onClick={() => void copyPrompt()}
              disabled={loadingPrompt || !recommendedPrompt}
              data-testid="dev-dashboard-roadmap-copy-prompt"
            >
              <Copy size={14} />
              {t('devDashboard.roadmap.copyPrompt')}
            </button>
            <button
              type="button"
              className="btn-secondary inline-flex items-center gap-1 text-xs"
              onClick={() => void exportPrompt()}
              disabled={loadingPrompt || !recommendedPrompt}
              data-testid="dev-dashboard-roadmap-export-prompt"
            >
              <Download size={14} />
              {t('devDashboard.roadmap.exportPrompt')}
            </button>
          </div>
        </div>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <div>
            <div className="text-[11px] uppercase tracking-wide text-slate-400">{t('devDashboard.roadmap.unlocks')}</div>
            <ul className="mt-1 space-y-1 text-xs text-slate-200">
              {promptUnlocks.length ? (
                promptUnlocks.map((entry) => <li key={entry}>- {entry}</li>)
              ) : (
                <li>- {t('devDashboard.noData')}</li>
              )}
            </ul>
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-wide text-slate-400">{t('devDashboard.roadmap.blockers')}</div>
            <ul className="mt-1 space-y-1 text-xs text-slate-200">
              {promptBlockers.length ? (
                promptBlockers.map((entry) => <li key={entry}>- {entry}</li>)
              ) : (
                <li>- {t('devDashboard.roadmap.notBlocked')}</li>
              )}
            </ul>
          </div>
        </div>
        {promptText ? (
          <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded border border-slate-700 bg-slate-950/80 p-3 text-xs text-slate-100">
            {promptText}
          </pre>
        ) : null}
      </div>

      <div className="overflow-auto rounded-xl border border-slate-700/60" data-testid="dev-dashboard-roadmap-tree-table">
        <table className="min-w-full text-left text-xs">
          <thead className="bg-slate-900/70 text-slate-300">
            <tr>
              <th className="px-3 py-2">{t('devDashboard.roadmap.columnItem')}</th>
              <th className="px-3 py-2">{t('devDashboard.roadmap.columnStatus')}</th>
              <th className="px-3 py-2">{t('devDashboard.roadmap.columnProgress')}</th>
              <th className="px-3 py-2">{t('devDashboard.roadmap.columnEvidenceLevel')}</th>
              <th className="px-3 py-2">{t('devDashboard.roadmap.columnBlockers')}</th>
              <th className="px-3 py-2">{t('devDashboard.roadmap.columnNextStep')}</th>
              <th className="px-3 py-2">{t('devDashboard.roadmap.columnPlannedRange')}</th>
              <th className="px-3 py-2">{t('devDashboard.roadmap.columnCompletedAt')}</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(({ key, level, row, kind }) => {
              const status = String(row.status || 'unknown')
              const blockers = asRows(row.blockers)
              return (
                <tr key={key} className="border-t border-slate-800/80 align-top">
                  <td className="px-3 py-2">
                    <div style={{ paddingLeft: `${level * 18}px` }}>
                      <div className={`font-medium ${kind === 'area' ? 'text-white' : 'text-slate-200'}`}>{localized(row, 'title')}</div>
                      <div className="text-[10px] uppercase tracking-wide text-slate-500">{kind}</div>
                    </div>
                  </td>
                  <td className="px-3 py-2">
                    <span className={`inline-flex rounded-full border px-2 py-0.5 ${toneForStatus(status)}`}>{status}</span>
                  </td>
                  <td className="px-3 py-2 text-slate-200">{String(row.progress_percent ?? '—')}%</td>
                  <td className="px-3 py-2 text-slate-200">{String(row.evidence_level || '—')}</td>
                  <td className="px-3 py-2 text-slate-200">
                    {blockers[0] ? localized(blockers[0], 'title') : Array.isArray(row.blocker_refs) && row.blocker_refs.length ? String(row.blocker_refs[0]) : '—'}
                  </td>
                  <td className="px-3 py-2 text-slate-200">{String(row.next_recommended_action || row.next_action_de || '—')}</td>
                  <td className="px-3 py-2 text-slate-200">{displayRange(row)}</td>
                  <td className="px-3 py-2 text-slate-200">{String(row.completed_at || '—')}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      <div className="space-y-3" data-testid="dev-dashboard-roadmap-details">
        {areas.map((area) => {
          const areaStatus = String(area.status || 'unknown')
          const areaPrompt = promptById.get(String(area.next_prompt_id || ''))
          return (
            <details key={String(area.id)} className="rounded-xl border border-slate-700/60 bg-slate-900/40" open={String(area.id) === 'restore' || String(area.id) === 'diagnostics'}>
              <summary className="cursor-pointer list-none px-4 py-3">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-semibold text-white">{localized(area, 'title')}</div>
                    <div className="text-xs text-slate-400">{String(area.description_de || '')}</div>
                  </div>
                  <span className={`inline-flex rounded-full border px-2 py-0.5 text-xs ${toneForStatus(areaStatus)}`}>{areaStatus}</span>
                </div>
              </summary>
              <div className="border-t border-slate-800/80 px-4 py-4 space-y-3 text-xs">
                <div>
                  <div className="font-semibold text-slate-200">{t('devDashboard.roadmap.reasonTitle')}</div>
                  <p className="mt-1 text-slate-300">{localizedReason(asRows(area.decisions)[0] || area)}</p>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <div className="font-semibold text-slate-200">{t('devDashboard.roadmap.blockers')}</div>
                    <ul className="mt-1 space-y-1 text-slate-300">
                      {asRows(area.blockers).length ? (
                        asRows(area.blockers).map((blocker) => <li key={String(blocker.id)}>- {localized(blocker, 'title')}</li>)
                      ) : (
                        <li>- {t('devDashboard.roadmap.none')}</li>
                      )}
                    </ul>
                  </div>
                  <div>
                    <div className="font-semibold text-slate-200">{t('devDashboard.roadmap.decisions')}</div>
                    <ul className="mt-1 space-y-1 text-slate-300">
                      {asRows(area.decisions).length ? (
                        asRows(area.decisions).map((decision) => <li key={String(decision.id)}>- {localizedReason(decision)}</li>)
                      ) : (
                        <li>- {t('devDashboard.roadmap.none')}</li>
                      )}
                    </ul>
                  </div>
                </div>
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <div className="font-semibold text-slate-200">{t('devDashboard.roadmap.notes')}</div>
                    <ul className="mt-1 space-y-1 text-slate-300">
                      {asRows(area.notes).length ? (
                        asRows(area.notes).map((note) => <li key={String(note.id)}>- {String(note.text_de || '—')}</li>)
                      ) : (
                        <li>- {t('devDashboard.roadmap.none')}</li>
                      )}
                    </ul>
                  </div>
                  <div>
                    <div className="font-semibold text-slate-200">{t('devDashboard.roadmap.evidence')}</div>
                    <ul className="mt-1 space-y-1 text-slate-300">
                      {(Array.isArray(area.authoritative_evidence) ? (area.authoritative_evidence as string[]) : []).length ? (
                        (area.authoritative_evidence as string[]).map((entry) => (
                          <li key={entry}>
                            <code>{entry}</code>
                          </li>
                        ))
                      ) : (
                        <li>- {t('devDashboard.roadmap.none')}</li>
                      )}
                    </ul>
                  </div>
                </div>
                <div className="rounded border border-slate-700/60 bg-slate-950/30 p-3">
                  <div className="font-semibold text-slate-200">{t('devDashboard.roadmap.linkedNextPrompt')}</div>
                  <div className="mt-1 text-slate-300">
                    {areaPrompt ? localized(areaPrompt, 'title') : t('devDashboard.roadmap.noLinkedPrompt')}
                  </div>
                </div>
              </div>
            </details>
          )
        })}
      </div>
    </section>
  )
}
