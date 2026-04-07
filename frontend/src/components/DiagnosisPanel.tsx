import React, { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { TFunction } from 'i18next'
import type { DiagnosisRecord } from '../types/diagnosis'

function isKeyV1(record: DiagnosisRecord): boolean {
  return record.localization_model === 'key_v1'
}

/** i18n-Key mit Fallback auf Legacy-String, wenn Übersetzung fehlt. */
function tOrLegacy(t: TFunction, key: string | null | undefined, legacy: string): string {
  if (!key) return legacy
  const v = t(key)
  return v === key ? legacy : v
}

function borderClass(record: DiagnosisRecord): string {
  switch (record.companion_mode) {
    case 'blocked':
      return 'border-red-500/50 bg-red-950/25'
    case 'warning':
      return 'border-amber-500/45 bg-amber-950/20'
    case 'caution':
      return 'border-amber-500/30 bg-amber-950/10'
    case 'recommendation':
    case 'guided_step':
      return 'border-sky-500/35 bg-slate-800/60'
    case 'info':
    default:
      return 'border-slate-600/60 bg-slate-800/50'
  }
}

export interface DiagnosisPanelProps {
  record: DiagnosisRecord
  className?: string
}

/**
 * Companion/Diagnose: verständliche Hauptsicht, Technik aufklappbar.
 */
const DiagnosisPanel: React.FC<DiagnosisPanelProps> = ({ record, className = '' }) => {
  const { t } = useTranslation()
  const [open, setOpen] = useState(false)

  const title = isKeyV1(record) ? tOrLegacy(t, record.title_key ?? null, record.title) : record.title
  const userMessage = isKeyV1(record)
    ? tOrLegacy(t, record.user_message_key ?? null, record.user_message)
    : record.user_message
  const suggestedList =
    isKeyV1(record) && record.suggested_action_keys && record.suggested_action_keys.length > 0
      ? record.suggested_action_keys.map((k, i) =>
          tOrLegacy(t, k, record.suggested_actions[i] ?? ''),
        )
      : record.suggested_actions

  return (
    <section
      className={`rounded-lg border px-3 py-2.5 sm:px-4 sm:py-3 text-sm ${borderClass(record)} ${className}`}
      role="region"
      aria-label={t('diagnosis.panel.ariaLabel')}
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-[10px] uppercase tracking-wide text-slate-500 mb-0.5">
            {t('diagnosis.panel.badge')}
            {record.interpreter_version.startsWith('v1-local') ? ` · ${t('diagnosis.panel.localFallback')}` : null}
          </p>
          <h3 className="font-semibold text-white leading-snug">{title}</h3>
        </div>
        <span
          className="shrink-0 text-[10px] uppercase px-1.5 py-0.5 rounded bg-slate-900/60 text-slate-400 border border-slate-600/50"
          title={t('diagnosis.panel.severityHint', { severity: record.severity })}
        >
          {record.severity}
        </span>
      </div>
      <p className="text-slate-200/95 mt-2 text-sm leading-relaxed">{userMessage}</p>

      {suggestedList.length > 0 && (
        <div className="mt-3">
          <p className="text-xs font-medium text-slate-400 mb-1">{t('diagnosis.panel.suggestedSteps')}</p>
          <ul className="list-disc list-inside text-xs sm:text-sm text-slate-300 space-y-0.5">
            {suggestedList.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </div>
      )}

      {record.technical_summary ? (
        <div className="mt-2 border-t border-slate-700/50 pt-2">
          <button
            type="button"
            onClick={() => setOpen(o => !o)}
            className="text-xs text-sky-400 hover:text-sky-300 underline"
          >
            {open ? t('diagnosis.panel.hideTechnical') : t('diagnosis.panel.showTechnical')}
          </button>
          {open && (
            <pre className="mt-2 text-[11px] text-slate-400 whitespace-pre-wrap break-words font-mono bg-slate-950/50 rounded p-2 border border-slate-700/40 max-h-40 overflow-y-auto">
              {record.technical_summary}
            </pre>
          )}
        </div>
      ) : null}
    </section>
  )
}

export default DiagnosisPanel
