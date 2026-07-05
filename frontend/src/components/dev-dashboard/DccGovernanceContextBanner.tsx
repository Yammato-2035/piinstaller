import React from 'react'
import { useTranslation } from 'react-i18next'
import type { DccRuntimeStatusModel } from '../../dcc/visibility/runtimeStatusModel'

type Props = {
  model: DccRuntimeStatusModel
  workspaceVersion?: string
  runtimeVersion?: string
  redAreaCount: number
}

/** Explains expected red governance when token + API work but Hard-Safety gates stay closed. */
export function DccGovernanceContextBanner({ model, workspaceVersion, runtimeVersion, redAreaCount }: Props) {
  const { t } = useTranslation()
  const tokenOk = model.developerTokenState === 'valid'
  const apiOk = model.dashboardApiReachable
  if (!tokenOk || !apiOk || redAreaCount === 0) return null

  return (
    <section
      className="mb-4 rounded-xl border border-amber-700/45 bg-amber-950/20 p-4"
      data-testid="dcc-governance-context-banner"
    >
      <h2 className="text-sm font-semibold text-amber-100">{t('devDashboard.vis.governance.redContextTitle')}</h2>
      <p className="mt-1 text-xs text-amber-100/90">{t('devDashboard.vis.governance.redContextBody')}</p>
      {model.workspaceAheadOfRuntime && workspaceVersion && runtimeVersion ? (
        <p className="mt-2 text-xs font-mono text-amber-200/95" data-testid="dcc-governance-version-drift">
          {t('devDashboard.vis.governance.versionDrift', {
            workspace: workspaceVersion,
            runtime: runtimeVersion,
          })}
        </p>
      ) : null}
      {model.workspaceAheadOfRuntime ? (
        <p className="mt-2 text-xs text-amber-100/85">{t('devDashboard.vis.governance.deployHint')}</p>
      ) : null}
    </section>
  )
}
