import React from 'react'
import { useTranslation } from 'react-i18next'
import { Bot, Shield } from 'lucide-react'
import type { ControlCenterSummary } from '../../api/devDashboardApi'
import { toneClass } from '../../pages/devDashboardFilters'
import { dashboardLegacyToneFromInput } from '../../viewmodels/statusViewModel'

type Props = {
  summary: ControlCenterSummary | null
}

function itemTone(status: string): string {
  return dashboardLegacyToneFromInput(status)
}

export function RescueDeveloperPipelineCard({ summary }: Props) {
  const { t } = useTranslation()
  const rescue = (summary?.rescue_developer as Record<string, unknown>) || {}
  const items = (rescue.items as Array<Record<string, unknown>>) || []
  const devServer = (summary?.dev_server as Record<string, unknown>) || {}
  const agentStatus = String(devServer.agent_status || 'unknown')

  return (
    <section
      className="rounded-xl border border-slate-700 bg-slate-900/50 p-4 mb-4"
      data-testid="rescue-developer-pipeline-card"
    >
      <h2 className="text-base font-semibold text-white flex items-center gap-2">
        <Bot className="text-violet-400" size={18} aria-hidden />
        {t('devDashboard.controlCenter.rescuePipelineTitle')}
      </h2>
      <p className="text-xs text-slate-400 mt-1">{t('devDashboard.controlCenter.rescuePipelineSubtitle')}</p>

      <ul className="mt-3 space-y-2">
        {items.map((item) => (
          <li
            key={String(item.id)}
            className={`rounded-lg border px-3 py-2 text-sm flex flex-wrap items-center justify-between gap-2 ${toneClass(itemTone(String(item.status || 'unknown')))}`}
            data-testid={`rescue-pipeline-${String(item.id)}`}
          >
            <span className="font-medium">{String(item.label || item.id)}</span>
            <span className="text-xs font-mono uppercase">{String(item.status || 'unknown')}</span>
          </li>
        ))}
      </ul>

      <div className="mt-3 rounded-lg border border-slate-700/60 bg-slate-950/40 p-3 text-xs" data-testid="rescue-pipeline-agent-status">
        <div className="flex items-center gap-2 text-slate-200">
          <Shield size={14} className="text-sky-400" aria-hidden />
          {t('devDashboard.controlCenter.agentStatus')}:{' '}
          <span className="font-mono">{agentStatus}</span>
        </div>
        {devServer.agent_last_report ? (
          <p className="text-slate-400 mt-1">
            {t('devDashboard.controlCenter.lastAgentReport')}:{' '}
            {String((devServer.agent_last_report as Record<string, unknown>).report_id || '—')}
          </p>
        ) : (
          <p className="text-slate-500 mt-1">{t('devDashboard.controlCenter.noAgentReport')}</p>
        )}
      </div>

      {rescue.next_step ? (
        <p className="mt-3 text-xs text-violet-200/90 border-t border-slate-800 pt-3" data-testid="rescue-pipeline-next-step">
          {t('devDashboard.controlCenter.nextStep')}: {String(rescue.next_step)}
        </p>
      ) : null}
    </section>
  )
}
