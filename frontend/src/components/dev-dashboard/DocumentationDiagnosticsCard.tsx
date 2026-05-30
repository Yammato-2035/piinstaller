import React from 'react'
import { useTranslation } from 'react-i18next'
import { BookOpen, Stethoscope } from 'lucide-react'
import type { ControlCenterSummary } from '../../api/devDashboardApi'
import { toneClass } from '../../pages/devDashboardFilters'

type Props = {
  summary: ControlCenterSummary | null
}

function docsTone(summary: ControlCenterSummary | null): string {
  const doc = (summary?.documentation as Record<string, unknown>) || {}
  const pairs = (doc.translation_pairs as Record<string, unknown>) || {}
  const missing = ((pairs.missing_de as string[]) || []).length + ((pairs.missing_en as string[]) || []).length
  if (doc.status === 'not_available') return 'gray'
  if (missing > 5) return 'yellow'
  return 'green'
}

function diagTone(summary: ControlCenterSummary | null): string {
  const diag = (summary?.diagnostics as Record<string, unknown>) || {}
  if (!diag.catalog_available) return 'gray'
  if ((diag.code_count as number) > 0) return 'green'
  return 'yellow'
}

export function DocumentationDiagnosticsCard({ summary }: Props) {
  const { t } = useTranslation()
  const doc = (summary?.documentation as Record<string, unknown>) || {}
  const pairs = (doc.translation_pairs as Record<string, unknown>) || {}
  const diag = (summary?.diagnostics as Record<string, unknown>) || {}
  const missingDe = (pairs.missing_de as string[]) || []
  const missingEn = (pairs.missing_en as string[]) || []

  return (
    <section
      className="rounded-xl border border-slate-700 bg-slate-900/50 p-4 mb-4"
      data-testid="documentation-diagnostics-card"
    >
      <h2 className="text-base font-semibold text-white flex items-center gap-2">
        <BookOpen className="text-amber-400" size={18} aria-hidden />
        {t('devDashboard.controlCenter.docsDiagnosticsTitle')}
      </h2>
      <p className="text-xs text-slate-400 mt-1">{t('devDashboard.controlCenter.docsDiagnosticsSubtitle')}</p>

      <div className="grid sm:grid-cols-2 gap-4 mt-4">
        <div className={`rounded-lg border p-3 ${toneClass(docsTone(summary))}`} data-testid="documentation-stats">
          <div className="text-sm font-semibold text-white">{t('devDashboard.controlCenter.documentation')}</div>
          <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
            <dt className="text-slate-400">{t('devDashboard.controlCenter.docsTotal')}</dt>
            <dd className="text-slate-200 font-mono">{doc.docs_total ?? '—'}</dd>
            <dt className="text-slate-400">FAQ</dt>
            <dd className="text-slate-200 font-mono">{doc.faq_total ?? '—'}</dd>
            <dt className="text-slate-400">KB</dt>
            <dd className="text-slate-200 font-mono">{doc.kb_total ?? '—'}</dd>
            <dt className="text-slate-400">{t('devDashboard.controlCenter.evidence')}</dt>
            <dd className="text-slate-200 font-mono">{doc.evidence_total ?? '—'}</dd>
            <dt className="text-slate-400">{t('devDashboard.controlCenter.translationPairs')}</dt>
            <dd className="text-slate-200 font-mono">{pairs.complete ?? 0}</dd>
          </dl>
          {missingDe.length || missingEn.length ? (
            <div className="mt-2 text-[11px] text-amber-200/90">
              {missingDe.length ? (
                <p>
                  {t('devDashboard.controlCenter.missingDe')}: {missingDe.slice(0, 3).join(', ')}
                  {missingDe.length > 3 ? '…' : ''}
                </p>
              ) : null}
              {missingEn.length ? (
                <p>
                  {t('devDashboard.controlCenter.missingEn')}: {missingEn.slice(0, 3).join(', ')}
                  {missingEn.length > 3 ? '…' : ''}
                </p>
              ) : null}
            </div>
          ) : null}
        </div>

        <div className={`rounded-lg border p-3 ${toneClass(diagTone(summary))}`} data-testid="diagnostics-stats">
          <div className="text-sm font-semibold text-white flex items-center gap-2">
            <Stethoscope size={16} className="text-cyan-400" aria-hidden />
            {t('devDashboard.controlCenter.diagnostics')}
          </div>
          <dl className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1 text-xs">
            <dt className="text-slate-400">{t('devDashboard.controlCenter.catalog')}</dt>
            <dd className="text-slate-200">{diag.catalog_available ? t('devDashboard.greenVisibility.ok') : t('devDashboard.controlCenter.unavailable')}</dd>
            <dt className="text-slate-400">{t('devDashboard.controlCenter.diagCodes')}</dt>
            <dd className="text-slate-200 font-mono">{diag.code_count ?? '—'}</dd>
            <dt className="text-slate-400">{t('devDashboard.controlCenter.diagTests')}</dt>
            <dd className="text-slate-200 font-mono">{diag.test_count ?? '—'}</dd>
            <dt className="text-slate-400">{t('devDashboard.controlCenter.diagKb')}</dt>
            <dd className="text-slate-200 font-mono">{diag.kb_count ?? '—'}</dd>
          </dl>
        </div>
      </div>
    </section>
  )
}
