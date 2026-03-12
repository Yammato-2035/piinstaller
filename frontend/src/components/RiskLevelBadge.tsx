import React from 'react'
import type { RiskLevel } from '../config/riskLevels'

interface RiskLevelBadgeProps {
  level: RiskLevel
  /** Kompakt (nur Punkt) oder mit Text */
  showLabel?: boolean
  className?: string
  title?: string
}

const STYLES: Record<RiskLevel, { bg: string; text: string; label: string }> = {
  green: {
    bg: 'bg-emerald-500/20 border-emerald-500/50',
    text: 'text-emerald-400',
    label: 'Sicher',
  },
  yellow: {
    bg: 'bg-amber-500/20 border-amber-500/50',
    text: 'text-amber-400',
    label: 'Systemänderung',
  },
  red: {
    bg: 'bg-red-500/20 border-red-500/50',
    text: 'text-red-400',
    label: 'Gefahr',
  },
}

const RiskLevelBadge: React.FC<RiskLevelBadgeProps> = ({ level, showLabel = false, className = '', title }) => {
  const s = STYLES[level]
  const t = title ?? s.label

  if (!showLabel) {
    return (
      <span
        className={`inline-block w-2 h-2 rounded-full border ${s.bg} ${className}`}
        title={t}
        aria-label={t}
      />
    )
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium border ${s.bg} ${s.text} ${className}`}
      title={t}
    >
      <span className="w-1.5 h-1.5 rounded-full bg-current shrink-0" />
      {s.label}
    </span>
  )
}

export default RiskLevelBadge
