import React, { useState } from 'react'
import { ChevronDown, ChevronUp } from 'lucide-react'
import type { CockpitPanelProps } from './types'
import type { RoadmapTabKey } from './types'

const TAB_KEYS: RoadmapTabKey[] = ['created', 'in_progress', 'planned', 'blocked']

export function RoadmapDrawer({ dashboard, t }: CockpitPanelProps) {
  const [open, setOpen] = useState(false)
  const [tab, setTab] = useState<RoadmapTabKey>('in_progress')
  const roadmap = (dashboard?.roadmap as Record<string, unknown>) || {}
  const tabs = (roadmap.tabs as Record<string, Array<Record<string, unknown>>>) || {}
  const changed = (roadmap.changed_to_green as Record<string, unknown>) || {}
  const items = tabs[tab] || []

  return (
    <div className="rounded-xl border border-violet-700/40 bg-violet-950/15" data-testid="dev-dashboard-roadmap-drawer">
      <button
        type="button"
        className="w-full flex items-center justify-between px-4 py-3 text-left"
        onClick={() => setOpen((v) => !v)}
        data-testid="dev-dashboard-roadmap-toggle"
      >
        <span className="font-semibold text-white">{t('devDashboard.roadmap.title')}</span>
        {open ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
      </button>
      {open ? (
        <div className="px-4 pb-4 space-y-3 border-t border-white/10">
          <div className="flex flex-wrap gap-2 pt-3">
            {TAB_KEYS.map((k) => (
              <button
                key={k}
                type="button"
                data-testid={`dev-dashboard-roadmap-tab-${k}`}
                onClick={() => setTab(k)}
                className={`px-2 py-1 text-xs rounded border ${tab === k ? 'border-violet-400 bg-violet-900/50' : 'border-slate-600'}`}
              >
                {t(`devDashboard.roadmap.tab.${k}`)} ({(tabs[k] || []).length})
              </button>
            ))}
          </div>
          <p className="text-xs text-slate-400">{String(changed.message || t('devDashboard.roadmap.noHistory'))}</p>
          <ul className="max-h-64 overflow-y-auto space-y-2 text-xs">
            {items.slice(0, 40).map((it, i) => (
              <li key={`${it.title}-${i}`} className="border border-slate-700/50 rounded p-2">
                <div className="font-semibold text-slate-100">{String(it.title)}</div>
                <div className="text-slate-500">{String(it.source)} · {String(it.status)}</div>
                {it.summary ? <p className="text-slate-400 mt-1">{String(it.summary).slice(0, 200)}</p> : null}
              </li>
            ))}
            {items.length === 0 ? <li className="text-slate-500">{t('devDashboard.noData')}</li> : null}
          </ul>
        </div>
      ) : null}
    </div>
  )
}
