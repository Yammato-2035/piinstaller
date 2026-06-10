/**
 * PartitionHardstopPanel – dominante Hardstop-Warnung (Phase 2.3 Mockup).
 */

import React from 'react'
import { useTranslation } from 'react-i18next'
import { ShieldAlert, AlertTriangle } from 'lucide-react'
import type { HardstopMessage } from '../api/partitionApi'
import { MOCKUP_STATUS } from '../lib/partition/partitionMockupTheme'

interface Props {
  hardstops: HardstopMessage[]
  warnings?: HardstopMessage[]
}

function normalizeCode(code: string): string {
  return code.replace(/^partition\.hardstop\./, '').replace(/^partition\.warning\./, '')
}

const PartitionHardstopPanel: React.FC<Props> = ({ hardstops, warnings = [] }) => {
  const { t } = useTranslation()

  const resolve = (code: string) => {
    const short = normalizeCode(code)
    const base = `hardstops.codes.${short}`
    return {
      title: t(`${base}.title`, { defaultValue: t(`partition.phase2.code.${code}`, code) }),
      explanation: t(`${base}.explanation`, { defaultValue: '' }),
      risk: t(`${base}.risk`, { defaultValue: '' }),
      action: t(`${base}.action`, { defaultValue: '' }),
    }
  }

  if (hardstops.length === 0 && warnings.length === 0) {
    return null
  }

  return (
    <section className="space-y-4" data-testid="partition-hardstop-panel">
      {hardstops.map((h) => {
        const info = resolve(h.code)
        const short = normalizeCode(h.code)
        return (
          <div
            key={h.code}
            className={`rounded-2xl border-2 px-6 py-6 sm:px-8 sm:py-7 ${MOCKUP_STATUS.blocked.card} shadow-lg`}
            data-testid={`partition-hardstop-${short}`}
          >
            <div className="flex items-start gap-4">
              <div className="w-14 h-14 rounded-2xl bg-red-500/25 flex items-center justify-center shrink-0">
                <ShieldAlert className="w-8 h-8 text-red-300" />
              </div>
              <div className="min-w-0 flex-1 space-y-3">
                <h3 className="text-xl sm:text-2xl font-black text-red-100 uppercase tracking-wide leading-tight">
                  {info.title}
                </h3>
                {info.explanation && (
                  <p className="text-base text-red-100/90 leading-relaxed">{info.explanation}</p>
                )}
                <p className="text-xs font-mono text-red-300/70 bg-red-950/50 inline-block px-2 py-1 rounded">
                  {h.code}
                </p>
                {info.risk && (
                  <p className="text-sm text-red-200/90">
                    <strong>{t('hardstops.riskLabel')}:</strong> {info.risk}
                  </p>
                )}
                {info.action && (
                  <p className="text-sm text-slate-300 italic border-t border-red-500/30 pt-3">
                    → {info.action}
                  </p>
                )}
              </div>
            </div>
          </div>
        )
      })}

      {warnings.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-bold text-amber-300 uppercase tracking-widest flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            {t('hardstops.warningsTitle')}
          </h4>
          {warnings.map((w) => {
            const info = resolve(w.code)
            return (
              <div
                key={w.code}
                className={`rounded-xl border px-5 py-4 ${MOCKUP_STATUS.review.card}`}
              >
                <p className="font-bold text-amber-100">{info.title}</p>
                <p className="text-sm text-amber-100/85 mt-1">{info.explanation || w.message}</p>
              </div>
            )
          })}
        </div>
      )}
    </section>
  )
}

export default PartitionHardstopPanel
