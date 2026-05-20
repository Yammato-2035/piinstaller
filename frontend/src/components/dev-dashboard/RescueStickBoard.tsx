import React from 'react'
import { useTranslation } from 'react-i18next'
import { HardDrive, Shield } from 'lucide-react'
import type { DashboardPayload } from '../../pages/DevDashboardBody'
import { toneClass } from '../../pages/devDashboardFilters'

type Br001GateSide = {
  id?: string
  release_gate?: boolean
  role?: string
  status?: string
  summary?: string
  policy?: string
}

function readBr001Gates(dashboard: DashboardPayload) {
  const g = (dashboard?.br001_gates as Record<string, unknown>) || {}
  return {
    primary: String(g.primary_release_gate || 'BR-001-OFFLINE'),
    live: (g.live as Br001GateSide) || {},
    offline: (g.offline as Br001GateSide) || {},
    pivot: String(g.pivot_evidence || 'docs/evidence/release-gates/BR-001_offline_gate_pivot_2026-05-20.md'),
  }
}

export function RescueStickBoard({ dashboard }: { dashboard: DashboardPayload }) {
  const { t } = useTranslation()
  const { primary, live, offline, pivot } = readBr001Gates(dashboard)
  const board = (dashboard?.rescue_stick_board as Record<string, unknown>) || {}
  const missing = Array.isArray(board.missing_mvp_component_ids)
    ? (board.missing_mvp_component_ids as string[])
    : []

  const card = (side: Br001GateSide, variant: 'live' | 'offline') => {
    const status = String(side.status || 'red')
    const isRelease = Boolean(side.release_gate)
    return (
      <div
        className={`rounded-lg border p-3 ${toneClass(status)}`}
        data-testid={`rescue-stick-board-${variant}`}
      >
        <div className="flex items-center gap-2 text-sm font-semibold text-white">
          {variant === 'offline' ? <Shield size={16} className="shrink-0" /> : <HardDrive size={16} className="shrink-0" />}
          {side.id || (variant === 'offline' ? 'BR-001-OFFLINE' : 'BR-001-LIVE')}
        </div>
        <p className="text-xs mt-1 opacity-90">
          {isRelease
            ? t('devDashboard.rescueStickBoard.releaseGateYes')
            : t('devDashboard.rescueStickBoard.releaseGateNo')}
          {' · '}
          {side.role === 'experimental'
            ? t('devDashboard.rescueStickBoard.experimental')
            : t('devDashboard.rescueStickBoard.releaseRole')}
        </p>
        {side.summary ? <p className="text-xs mt-2 text-slate-200">{String(side.summary)}</p> : null}
        {variant === 'live' && side.policy ? (
          <p className="text-xs mt-1 text-amber-200/90">{t('devDashboard.rescueStickBoard.noLiveGateRetries')}</p>
        ) : null}
      </div>
    )
  }

  return (
    <section
      className="rounded-xl border border-violet-800/40 bg-violet-950/20 p-4 space-y-3"
      data-testid="rescue-stick-board"
    >
      <div>
        <h2 className="text-base font-semibold text-violet-100">{t('devDashboard.rescueStickBoard.title')}</h2>
        <p className="text-xs text-slate-400 mt-0.5">{t('devDashboard.rescueStickBoard.subtitle', { gate: primary })}</p>
      </div>
      <div className="grid md:grid-cols-2 gap-3">
        {card(live, 'live')}
        {card(offline, 'offline')}
      </div>
      {missing.length > 0 ? (
        <div className="text-xs text-slate-300">
          <span className="font-medium text-slate-200">{t('devDashboard.rescueStickBoard.missingMvp')}:</span>{' '}
          <span className="font-mono">{missing.join(', ')}</span>
        </div>
      ) : null}
      <p className="text-[10px] text-slate-500 break-all">{pivot}</p>
    </section>
  )
}
