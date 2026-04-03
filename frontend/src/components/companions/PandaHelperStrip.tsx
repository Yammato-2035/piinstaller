import React from 'react'
import PandaHelper, { type PandaVariant } from '../PandaHelper'
import type { ExperienceLevel } from '../Sidebar'

export interface PandaHelperStripProps {
  experienceLevel: ExperienceLevel
  variant?: PandaVariant
  children: React.ReactNode
  className?: string
}

/** Kompakte Zeile: kleines Panda-Icon + Kurztext (Expertenansicht ausgeblendet). */
export const PandaHelperStrip: React.FC<PandaHelperStripProps> = ({
  experienceLevel,
  variant = 'base',
  children,
  className = '',
}) => {
  if (experienceLevel === 'developer') return null
  return (
    <div
      className={`flex items-start gap-3 rounded-lg border border-slate-600/60 bg-slate-800/35 px-3 py-2.5 ${className}`.trim()}
    >
      <PandaHelper
        experienceLevel={experienceLevel}
        variant={variant}
        size="sm"
        iconOnly
        className="!rounded-lg shrink-0"
      />
      <div className="text-xs sm:text-sm text-slate-400 leading-snug min-w-0 pt-0.5">{children}</div>
    </div>
  )
}
