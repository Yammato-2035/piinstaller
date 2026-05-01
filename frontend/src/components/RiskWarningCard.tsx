import React from 'react'
import { useTranslation } from 'react-i18next'
import { AlertTriangle } from 'lucide-react'
import type { RiskLevel } from '../config/riskLevels'
import RiskLevelBadge from './RiskLevelBadge'

interface RiskWarningCardProps {
  level: RiskLevel
  title?: string
  /** Kurzer Hinweis (1–2 Sätze). */
  children: React.ReactNode
  className?: string
}

const CARD_STYLES: Record<RiskLevel, { border: string; bg: string; icon: string }> = {
  green: { border: 'border-emerald-500/40', bg: 'bg-emerald-500/10', icon: 'text-emerald-400' },
  yellow: { border: 'border-amber-300/70', bg: 'bg-amber-900/35', icon: 'text-amber-200' },
  red: { border: 'border-red-500/40', bg: 'bg-red-500/10', icon: 'text-red-400' },
}

const RiskWarningCard: React.FC<RiskWarningCardProps> = ({ level, title, children, className = '' }) => {
  const { t } = useTranslation()
  const s = CARD_STYLES[level]
  const defaultTitle =
    level === 'red' ? t('risk.cardTitle.danger') : level === 'yellow' ? t('risk.cardTitle.systemChange') : t('risk.cardTitle.note')

  return (
    <div
      className={`rounded-xl border p-4 ${s.border} ${s.bg} ${className}`}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className={`w-5 h-5 shrink-0 mt-0.5 ${s.icon}`} aria-hidden />
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <RiskLevelBadge level={level} showLabel />
            <span className="font-semibold text-slate-200">{title ?? defaultTitle}</span>
          </div>
          <p className="text-sm text-slate-300">{children}</p>
        </div>
      </div>
    </div>
  )
}

export default RiskWarningCard
