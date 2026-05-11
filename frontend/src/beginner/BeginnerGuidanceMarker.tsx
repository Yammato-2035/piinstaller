import React from 'react'
import { Lock, Clock, FlaskConical } from 'lucide-react'
import type { AvailabilityState } from './moduleModel'

export type BeginnerMarkerKind = 'locked' | 'later' | 'advanced'

const kindFromAvailability = (a: AvailabilityState): BeginnerMarkerKind | null => {
  if (a === 'locked') return 'locked'
  if (a === 'coming_later') return 'later'
  if (a === 'advanced_only') return 'advanced'
  return null
}

export interface BeginnerGuidanceMarkerProps {
  kind?: BeginnerMarkerKind
  /** Alternative: aus AvailabilityState ableiten */
  availability?: AvailabilityState
  className?: string
  compact?: boolean
}

/**
 * Wiederverwendbare Markierung: gesperrt / später / fortgeschritten.
 */
const BeginnerGuidanceMarker: React.FC<BeginnerGuidanceMarkerProps> = ({
  kind: kindProp,
  availability,
  className = '',
  compact = false,
}) => {
  const kind = kindProp ?? (availability ? kindFromAvailability(availability) : null)
  if (!kind) return null

  const base =
    'inline-flex items-center gap-1 rounded-md font-semibold border whitespace-nowrap ' +
    (compact ? 'px-1.5 py-0.5 text-[9px]' : 'px-2 py-0.5 text-[10px]')

  if (kind === 'locked') {
    return (
      <span
        className={`${base} border-rose-500/50 bg-rose-950/40 text-rose-200 ${className}`}
        title="Im Einsteiger-Modus gesperrt – in den Einstellungen das Erfahrungslevel anheben."
      >
        <Lock className={compact ? 'w-2.5 h-2.5' : 'w-3 h-3 shrink-0'} aria-hidden />
        Gesperrt
      </span>
    )
  }
  if (kind === 'later') {
    return (
      <span
        className={`${base} border-amber-500/45 bg-amber-950/35 text-amber-100 ${className}`}
        title="Kommt später oder nach dem Basisschritten."
      >
        <Clock className={compact ? 'w-2.5 h-2.5' : 'w-3 h-3 shrink-0'} aria-hidden />
        Später
      </span>
    )
  }
  return (
    <span
      className={`${base} border-violet-500/45 bg-violet-950/35 text-violet-100 ${className}`}
      title="Für Fortgeschrittene – optional für den Einstieg."
    >
      <FlaskConical className={compact ? 'w-2.5 h-2.5' : 'w-3 h-3 shrink-0'} aria-hidden />
      Fortgeschritten
    </span>
  )
}

export default BeginnerGuidanceMarker
