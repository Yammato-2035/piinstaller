import React from 'react'
import { useTranslation } from 'react-i18next'
import { DEFAULT_WORKSPACE_HANDOFF } from '../../dcc/visibility/workspaceHandoff'

type Props = {
  currentBranch?: string
  currentCommit?: string
}

export function DccWorkspaceHandoffCard({ currentBranch, currentCommit }: Props) {
  const { t } = useTranslation()
  const handoff = DEFAULT_WORKSPACE_HANDOFF

  return (
    <section
      className="rounded-xl border border-indigo-700/40 bg-indigo-950/20 p-4 mb-4"
      data-testid="dcc-workspace-handoff-card"
    >
      <h2 className="text-sm font-semibold text-white">{t('devDashboard.vis.handoff.title')}</h2>
      <p className="text-xs text-slate-400 mt-1">{t('devDashboard.vis.handoff.subtitle')}</p>

      <dl className="mt-3 grid gap-3 md:grid-cols-2 text-xs">
        <div className="rounded-lg border border-slate-700/60 bg-slate-950/40 p-3">
          <dt className="text-slate-500 uppercase text-[10px] tracking-wide">{t('devDashboard.vis.handoff.current')}</dt>
          <dd className="mt-1 font-mono text-slate-100" data-testid="dcc-handoff-current-workspace">
            {handoff.currentWorkspace}
          </dd>
          <dd className="mt-1 text-slate-300">{handoff.currentPhase}</dd>
          {currentBranch ? <dd className="mt-1 text-slate-400 font-mono">branch: {currentBranch}</dd> : null}
          {currentCommit ? <dd className="mt-1 text-slate-400 font-mono">HEAD: {currentCommit.slice(0, 12)}</dd> : null}
        </div>
        <div className="rounded-lg border border-indigo-700/40 bg-indigo-950/30 p-3">
          <dt className="text-slate-500 uppercase text-[10px] tracking-wide">{t('devDashboard.vis.handoff.next')}</dt>
          <dd className="mt-1 font-mono text-indigo-100" data-testid="dcc-handoff-next-workspace">
            {handoff.nextWorkspace}
          </dd>
          <dd className="mt-1 text-indigo-200">{handoff.nextPhase}</dd>
        </div>
      </dl>

      <div className="mt-3 space-y-2 text-xs text-slate-300">
        <p><strong className="text-slate-400">{t('devDashboard.vis.handoff.reason')}:</strong> {t(handoff.reasonKey)}</p>
        <p><strong className="text-emerald-400/80">{t('devDashboard.vis.handoff.allowed')}:</strong> {t(handoff.allowedKey)}</p>
        <p><strong className="text-red-400/80">{t('devDashboard.vis.handoff.forbidden')}:</strong> {t(handoff.forbiddenKey)}</p>
      </div>
    </section>
  )
}
