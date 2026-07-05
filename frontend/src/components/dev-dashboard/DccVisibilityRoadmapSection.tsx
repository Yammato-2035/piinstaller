import React from 'react'
import { useTranslation } from 'react-i18next'
import { buildRoadmapVisibilityStatus } from '../../dcc/visibility/roadmapStatus'
import { changelogByStatus } from '../../dcc/visibility/changelogModel'
import { DccVisibleResultsPanel } from './DccVisibleResultsPanel'
import { DccWorkspaceHandoffCard } from './DccWorkspaceHandoffCard'

type Props = {
  blockers?: string[]
  currentBranch?: string
  currentCommit?: string
}

export function DccVisibilityRoadmapSection({ blockers = [], currentBranch, currentCommit }: Props) {
  const { t } = useTranslation()
  const status = buildRoadmapVisibilityStatus({ blockers, branch: currentBranch, commit: currentCommit })
  const inProgress = changelogByStatus('in_progress')
  const completed = changelogByStatus('completed')
  const planned = changelogByStatus('planned')

  return (
    <div className="space-y-4" data-testid="dcc-visibility-roadmap-section">
      <section className="rounded-xl border border-violet-700/40 bg-violet-950/15 p-4">
        <h2 className="text-sm font-semibold text-white">{t('devDashboard.vis.roadmap.sectionTitle')}</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4 text-xs">
          <div className="rounded-lg border border-slate-700 p-3" data-testid="dcc-vis-current-work">
            <div className="text-slate-500">{t('devDashboard.vis.roadmap.inProgress')}</div>
            <div className="mt-1 font-semibold text-white">{status.current_phase}</div>
          </div>
          <div className="rounded-lg border border-slate-700 p-3" data-testid="dcc-vis-last-completed">
            <div className="text-slate-500">{t('devDashboard.vis.roadmap.lastCompleted')}</div>
            <div className="mt-1 font-semibold text-white">{status.last_completed_phase}</div>
            <div className="mt-1 text-slate-400">{t(status.last_visible_result)}</div>
          </div>
          <div className="rounded-lg border border-slate-700 p-3" data-testid="dcc-vis-next-phase">
            <div className="text-slate-500">{t('devDashboard.vis.roadmap.nextPhase')}</div>
            <div className="mt-1 font-semibold text-white">{planned[0]?.id ?? status.next_recommended_phase}</div>
          </div>
          <div className="rounded-lg border border-slate-700 p-3" data-testid="dcc-vis-next-workspace">
            <div className="text-slate-500">{t('devDashboard.vis.roadmap.nextWorkspace')}</div>
            <div className="mt-1 font-mono text-slate-200 text-[11px]">{status.next_required_workspace}</div>
          </div>
        </div>

        {blockers.length > 0 ? (
          <div className="mt-3 rounded border border-red-700/40 bg-red-950/20 p-3 text-xs" data-testid="dcc-vis-blockers">
            <div className="font-semibold text-red-200">{t('devDashboard.vis.roadmap.blockers')}</div>
            <ul className="mt-1 list-disc pl-4 text-red-100/90">
              {blockers.map((b) => (
                <li key={b}>{b}</li>
              ))}
            </ul>
          </div>
        ) : null}

        {completed.filter((c) => c.visibleSurfaces.dcc === false).length > 0 ? (
          <div className="mt-3 rounded border border-amber-700/40 bg-amber-950/20 p-3 text-xs" data-testid="dcc-vis-no-ui">
            <div className="font-semibold text-amber-100">{t('devDashboard.vis.roadmap.noVisibleUi')}</div>
            <ul className="mt-1 space-y-1 text-amber-100/90">
              {completed
                .filter((c) => c.visibleSurfaces.dcc === false)
                .map((c) => (
                  <li key={c.id}>
                    {c.id} — {t('devDashboard.vis.roadmap.techCompleteNotVisible')}
                  </li>
                ))}
            </ul>
          </div>
        ) : null}
      </section>

      <DccVisibleResultsPanel />
      <DccWorkspaceHandoffCard currentBranch={currentBranch} currentCommit={currentCommit} />
    </div>
  )
}
