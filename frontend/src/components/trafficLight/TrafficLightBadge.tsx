import React from 'react'
import { LampDot } from '../companions/StatusDots'
import type { TrafficLightLampState, TrafficLightState } from '../../trafficLight/trafficLightModel'
import { trafficLightStateToLamp } from '../../trafficLight/trafficLightModel'

export interface TrafficLightBadgeProps {
  state: TrafficLightState
  label: string
  /** Kurztext für Tooltip / Titel */
  detail?: string
  className?: string
  /** unknown = gedimmtes Gelb */
  quietUnknown?: boolean
  /** Auf dunklen Karten (z. B. Monitoring) lesbar */
  tone?: 'default' | 'onDark'
}

export const TrafficLightBadge: React.FC<TrafficLightBadgeProps> = ({
  state,
  label,
  detail,
  className = '',
  quietUnknown = true,
  tone = 'default',
}) => {
  const lamp: TrafficLightLampState = trafficLightStateToLamp(state)
  const quiet = state === 'unknown' ? quietUnknown : lamp === 'yellow'
  const title = detail ? `${label}: ${detail}` : label
  const shell =
    tone === 'onDark'
      ? 'border-slate-600 bg-slate-800/90'
      : 'border-slate-300 dark:border-slate-600 bg-slate-100/95 dark:bg-slate-900/60'
  const textCls = tone === 'onDark' ? 'text-slate-100' : 'text-slate-800 dark:text-slate-100'

  return (
    <div
      className={`inline-flex items-center gap-2 rounded-lg border px-2.5 py-1.5 ${shell} ${className}`.trim()}
      role="status"
      title={title}
    >
      <LampDot lamp={lamp} quiet={quiet} />
      <span className={`text-xs font-medium leading-tight ${textCls}`.trim()}>{label}</span>
    </div>
  )
}
