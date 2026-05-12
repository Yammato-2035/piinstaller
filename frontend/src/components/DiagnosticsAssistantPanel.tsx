import React from 'react'
import { useTranslation } from 'react-i18next'
import type { DiagnosticsAnalyzeResponse, DiagnosticsUserLevel } from '../types/diagnostics'

interface Props {
  result: DiagnosticsAnalyzeResponse
  level: DiagnosticsUserLevel
}

const DiagnosticsAssistantPanel: React.FC<Props> = ({ result, level }) => {
  const { t } = useTranslation()
  const msg = result.messages?.[level] || result.user_message_beginner

  return (
    <section className="rounded-lg border border-indigo-500/40 bg-slate-900/60 p-3 text-sm">
      <p className="text-xs uppercase tracking-wide text-indigo-300">{t('diagnostics.panel.badge')}</p>
      <h3 className="mt-1 font-semibold text-white">
        {result.primary_diagnosis?.id || t('diagnostics.panel.noPrimary')}
      </h3>
      <p className="mt-2 text-slate-200">{msg}</p>
      <p className="mt-2 text-xs text-slate-400">
        {t('diagnostics.panel.meta', { severity: result.severity, confidence: result.confidence })}
      </p>
      {result.actions_now.length > 0 && (
        <ul className="mt-2 list-disc list-inside text-slate-300 text-xs">
          {result.actions_now.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      )}
      {level === 'expert' && result.technical_summary && (
        <pre className="mt-3 rounded border border-slate-700 bg-slate-950/60 p-2 text-[11px] text-slate-400 whitespace-pre-wrap">
          {result.technical_summary}
        </pre>
      )}
    </section>
  )
}

export default DiagnosticsAssistantPanel
