import type { CockpitPanelProps } from './types'

export function DocsConsistencyPanel({ dashboard, t }: CockpitPanelProps) {
  const sh = (dashboard?.structure_health as Record<string, unknown>) || {}
  const docs = (sh.docs_consistency as Record<string, unknown>) || {}
  const matrix = (dashboard?.matrix_files as Record<string, unknown>) || {}
  return (
    <div className="rounded-xl border border-slate-600 bg-slate-900/50 p-4" data-testid="dev-dashboard-docs-consistency-panel">
      <h2 className="text-base font-semibold text-white">{t('devDashboard.docsConsistency.title')}</h2>
      <p className="text-xs text-slate-300 mt-2">
        STATUS_MATRIX: {docs.matrix_exists === true ? '✓' : '—'}
      </p>
      <ul className="mt-2 text-xs font-mono text-slate-400">
        {Object.keys(matrix).slice(0, 4).map((k) => (
          <li key={k}>{k}</li>
        ))}
      </ul>
    </div>
  )
}
