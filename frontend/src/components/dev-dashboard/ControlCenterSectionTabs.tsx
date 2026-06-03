import React from 'react'
import type { ControlCenterSummary } from '../../api/devDashboardApi'
import { RecentEvidenceFeedPanel, type EvidenceItem } from './RecentEvidenceFeedPanel'

export type ControlCenterTab =
  | 'overview'
  | 'roadmap'
  | 'telemetry'
  | 'rescue'
  | 'documentation'
  | 'evidence'
  | 'operations'

type Props = {
  active: ControlCenterTab
  onChange: (tab: ControlCenterTab) => void
  t: (key: string) => string
}

const TABS: ControlCenterTab[] = [
  'overview',
  'roadmap',
  'telemetry',
  'rescue',
  'documentation',
  'evidence',
  'operations',
]

export function ControlCenterSectionTabs({ active, onChange, t }: Props) {
  return (
    <nav
      className="flex flex-wrap gap-1 mb-4 border-b border-slate-700 pb-2"
      data-testid="control-center-section-tabs"
      aria-label={t('devDashboard.controlCenter.tabsLabel')}
    >
      {TABS.map((tab) => (
        <button
          key={tab}
          type="button"
          data-testid={`control-center-tab-${tab}`}
          onClick={() => onChange(tab)}
          className={`px-3 py-1.5 rounded-md text-xs font-medium border transition-colors ${
            active === tab
              ? 'bg-violet-900/70 border-violet-500/60 text-white'
              : 'border-transparent text-slate-400 hover:text-slate-200 hover:bg-slate-800/50'
          }`}
        >
          {t(`devDashboard.controlCenter.tab.${tab}`)}
        </button>
      ))}
    </nav>
  )
}

export function ControlCenterEvidenceSection({
  summary,
  t,
}: {
  summary: ControlCenterSummary | null
  t: (key: string, opts?: Record<string, unknown>) => string
}) {
  const evidence = (summary?.evidence as Record<string, unknown>) || {}
  const recentReports = (evidence.recent_reports as Array<Record<string, unknown>>) || []
  const recentTests = (evidence.recent_tests as Array<Record<string, unknown>>) || []

  return (
    <div data-testid="control-center-evidence-section">
      <RecentEvidenceFeedPanel
        t={t}
        mode="both"
        initialReports={recentReports as EvidenceItem[]}
        initialTests={recentTests as EvidenceItem[]}
      />
    </div>
  )
}
