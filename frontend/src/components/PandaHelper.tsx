import React, { useCallback, useEffect, useState } from 'react'
import type { ExperienceLevel } from './Sidebar'
import {
  companionShouldUseLogoMainCrop,
  getCompanionBaseDisplayUrl,
  getPandaHelperBundledUrl,
} from './companions/companionAssets'

export type PandaVariant = 'base' | 'backup' | 'bluetooth' | 'gpio' | 'security' | 'diagnostics'

interface PandaHelperProps {
  experienceLevel: ExperienceLevel
  variant?: PandaVariant
  size?: 'sm' | 'md' | 'lg'
  className?: string
  iconOnly?: boolean
  alt?: string
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
  if (experienceLevel === 'developer') return null

  const bundledUrl = getPandaHelperBundledUrl(variant)
  const logoUrl = getCompanionBaseDisplayUrl()
  const [tier, setTier] = useState<'bundle' | 'logo'>('bundle')

  useEffect(() => {
    setTier('bundle')
  }, [variant])

  const activeSrc = tier === 'bundle' ? bundledUrl : logoUrl ?? ''
  const useLogoCrop =
    tier === 'logo' && Boolean(logoUrl) && companionShouldUseLogoMainCrop()

  const baseClasses = `${sizeToClass[size]} rounded-xl bg-white/80 dark:bg-slate-900/60 p-1 shrink-0 shadow-sm overflow-hidden ${
    useLogoCrop ? 'object-cover object-[51%_41%]' : 'object-contain'
  }`
  const combinedClassName = `${baseClasses} ${className}`.trim()
  const altText = alt || 'SetupHelfer Panda'

  const [failed, setFailed] = useState(false)
  useEffect(() => {
    setFailed(false)
  }, [variant, tier, activeSrc])

  const onErr = useCallback(() => {
    if (tier === 'bundle' && logoUrl) {
      setTier('logo')
      return
    }
    setFailed(true)
  }, [tier, logoUrl])

  if (failed || (tier === 'logo' && !logoUrl)) {
    const box = `${sizeToClass[size]} shrink-0 rounded-lg border-2 border-dashed border-red-500 bg-red-950/30 flex flex-col items-center justify-center p-1 text-[8px] font-bold text-red-200 text-center leading-tight`
    return (
      <div
        className={`${box} ${className}`.trim()}
        title="Companion Asset fehlt"
        role="img"
        aria-label="Companion Asset fehlt"
      >
        <span>!</span>
        <span className="font-mono opacity-90">Asset fehlt</span>
      </div>
    )
  }

  if (iconOnly) {
    return (
      <img
        key={`${variant}-${tier}`}
        src={activeSrc}
        alt={altText}
        className={combinedClassName}
        loading="eager"
        decoding="async"
        onError={onErr}
      />
    )
  }

  return (
    <div className="flex items-start gap-4">
      <img
        key={`${variant}-${tier}`}
        src={activeSrc}
        alt={altText}
        className={combinedClassName}
        loading="eager"
        decoding="async"
        onError={onErr}
      />
    </div>
  )
}

export default PandaHelper
