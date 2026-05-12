import React from 'react'
import { useTranslation } from 'react-i18next'
import type { RiskLevel } from '../config/riskLevels'

interface RiskLevelBadgeProps {
  level: RiskLevel
  /** Kompakt (nur Punkt) oder mit Text */
  showLabel?: boolean
  className?: string
  title?: string
}

const STYLES: Record<RiskLevel, { bg: string; text: string; labelKey: string }> = {
  green: {
    bg: 'bg-emerald-500/20 border-emerald-500/50',
    text: 'text-emerald-400',
    labelKey: 'risk.label.safe',
  },
  yellow: {
    bg: 'bg-amber-900/45 border-amber-300/70',
    text: 'text-amber-100',
    labelKey: 'risk.label.systemChange',
  },
  red: {
    bg: 'bg-red-500/20 border-red-500/50',
    text: 'text-red-400',
    labelKey: 'risk.label.danger',
  },
}

const RiskLevelBadge: React.FC<RiskLevelBadgeProps> = ({ level, showLabel = false, className = '', title }) => {
  const { t } = useTranslation()
  const s = STYLES[level]
  const tLabel = title ?? t(s.labelKey)

  if (!showLabel) {
    return (
      <span
        className={`inline-block w-2 h-2 rounded-full border ${s.bg} ${className}`}
        title={tLabel}
        aria-label={tLabel}
      />
    )
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium border ${s.bg} ${s.text} ${className}`}
      title={tLabel}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current shrink-0" />
      {t(s.labelKey)}
    </span>
  )
}

export default RiskLevelBadge
