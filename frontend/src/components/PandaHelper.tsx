import React from 'react'
import type { ExperienceLevel } from './Sidebar'
import { mascotPublicUrl } from '../lib/mascotPublicUrl'

export type PandaVariant = 'base' | 'backup' | 'bluetooth' | 'gpio' | 'security' | 'diagnostics'

interface PandaHelperProps {
  /** Erfahrungslevel aus App-State – steuert Sichtbarkeit. */
  experienceLevel: ExperienceLevel
  /** Kontext, in dem der Panda angezeigt wird (steuert Asset-Pfad). */
  variant?: PandaVariant
  /** Größe der Darstellung im UI. */
  size?: 'sm' | 'md' | 'lg'
  /** Zusätzliche CSS-Klassen für Layout/Abstand. */
  className?: string
  /** Wenn true, wird nur das Icon ohne erklärenden Text angezeigt (für Fortgeschrittene). */
  iconOnly?: boolean
  /** Optional: Überschreibt den Standard-Alt-Text. */
  alt?: string
}

/**
 * Panda-Motive als PNG (statt SVG), damit die Accessoires überall zuverlässig sichtbar sind.
 * (WebKit/Tauri rendert SVG-`<image href>` innerhalb von SVG-as-`<img>` teilweise nicht.)
 */
const variantToAsset: Record<PandaVariant, string> = {
  base: mascotPublicUrl('assets/mascot/panda_base.png'),
  backup: mascotPublicUrl('assets/mascot/panda_backup.png'),
  bluetooth: mascotPublicUrl('assets/mascot/panda_bluetooth.png'),
  gpio: mascotPublicUrl('assets/mascot/panda_gpio.png'),
  security: mascotPublicUrl('assets/mascot/panda_security.png'),
  diagnostics: mascotPublicUrl('assets/mascot/panda_diagnostics.png'),
}

const sizeToClass: Record<NonNullable<PandaHelperProps['size']>, string> = {
  sm: 'w-10 h-10',
  md: 'w-14 h-14',
  lg: 'w-20 h-20',
}

export const PandaHelper: React.FC<PandaHelperProps> = ({
  experienceLevel,
  variant = 'base',
  size = 'md',
  className = '',
  iconOnly = false,
  alt,
}) => {
  // Expertenansicht: Panda vollständig ausgeblendet.
  if (experienceLevel === 'developer') return null

  const assetSrc = variantToAsset[variant]
  const baseClasses = `${sizeToClass[size]} rounded-xl bg-white/80 dark:bg-slate-900/60 p-1 object-contain shrink-0 shadow-sm`
  const combinedClassName = `${baseClasses} ${className}`.trim()
  const altText = alt || 'SetupHelfer Panda'

  // Nur natives img – Framer-Motion in WebViews (Tauri) kann zu leeren Darstellungen führen.
  if (iconOnly) {
    return (
      <img
        src={assetSrc}
        alt={altText}
        className={combinedClassName}
        loading="eager"
        decoding="async"
      />
    )
  }

  return (
    <div className="flex items-start gap-4">
      <img
        src={assetSrc}
        alt={altText}
        className={combinedClassName}
        loading="eager"
        decoding="async"
      />
      {/* Textliche Erklärungen (über i18n im Aufrufer gesteuert) */}
    </div>
  )
}

export default PandaHelper

