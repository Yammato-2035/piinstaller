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
      className={`flex items-start gap-3 rounded-lg border border-slate-400/90 bg-slate-200/95 text-slate-900 shadow-sm dark:border-slate-600/70 dark:bg-slate-800/70 dark:text-slate-100 px-3 py-2.5 ${className}`.trim()}
    >
      <PandaHelper
        experienceLevel={experienceLevel}
        variant={variant}
        size="sm"
        iconOnly
        className="!rounded-lg shrink-0"
      />
      <div className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-snug min-w-0 pt-0.5">{children}</div>
    </div>
  )
}
