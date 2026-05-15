import type { CockpitPanelProps } from './types'
import { toneClass } from '../../pages/devDashboardFilters'

export function EvidencePanel({ dashboard, t }: CockpitPanelProps) {
  const te = (dashboard?.tests_evidence as Record<string, unknown>) || {}
  const tone = String(te.status || 'gray')
  const files = (te.files as Record<string, Record<string, unknown>>) || {}
  return (
    <div className={`rounded-xl border p-4 ${toneClass(tone)}`} data-testid="dev-dashboard-evidence-panel">
      <h2 className="text-base font-semibold text-white">{t('devDashboard.evidencePanel.title')}</h2>
      <ul className="mt-2 space-y-1 text-xs font-mono text-slate-300">
        {Object.entries(files).map(([name, meta]) => (
          <li key={name} className="flex flex-wrap gap-2">
            <span>{name}</span>
            <span className="text-slate-500">{String(meta?.ampel ?? meta?.status ?? '—')}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
