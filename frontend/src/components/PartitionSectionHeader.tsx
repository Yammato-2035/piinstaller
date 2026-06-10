/**
 * Nummerierte Abschnittsüberschrift (Mockup Phase 2.2).
 */

import React from 'react'

interface Props {
  step: number
  title: string
  subtitle?: string
  className?: string
}

const PartitionSectionHeader: React.FC<Props> = ({ step, title, subtitle, className = '' }) => (
  <div className={`flex items-start gap-3 ${className}`}>
    <span
      className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal-500/25 border-2 border-teal-500/45 text-base font-black text-teal-200"
      aria-hidden
    >
      {step}
    </span>
    <div className="min-w-0">
      <h2 className="text-lg sm:text-xl font-black text-slate-50 tracking-tight">{title}</h2>
      {subtitle && <p className="text-sm text-slate-400 mt-1">{subtitle}</p>}
    </div>
  </div>
)

export default PartitionSectionHeader
