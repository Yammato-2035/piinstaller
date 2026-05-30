import React from 'react'
import type { ControlCenterSummary } from '../../api/devDashboardApi'

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

export function ControlCenterEvidenceSection({ summary }: { summary: ControlCenterSummary | null }) {
  const evidence = (summary?.evidence as Record<string, unknown>) || {}
  const recent = (evidence.recent_files as Array<Record<string, unknown>>) || []

  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900/50 p-4 mb-4" data-testid="control-center-evidence-section">
      <h2 className="text-base font-semibold text-white">Evidence</h2>
      <p className="text-xs text-slate-400 mt-1">Read-only index — newest files first</p>
      <ul className="mt-3 space-y-1 text-xs font-mono text-slate-300 max-h-96 overflow-y-auto">
        {recent.length ? (
          recent.map((f) => (
            <li key={String(f.path)} className="truncate">
              <span className="text-slate-500">{String(f.mtime_iso || '').slice(0, 19)}</span> — {String(f.path || '—')}
            </li>
          ))
        ) : (
          <li className="text-slate-500">—</li>
        )}
      </ul>
    </section>
  )
}
