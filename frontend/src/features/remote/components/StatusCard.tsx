import React from 'react'

interface Widget {
  id: string
  type: string
  label?: string
  config?: Record<string, unknown>
}

interface StatusCardProps {
  widget: Widget
  state: Record<string, unknown>
}

export default function StatusCard({ widget, state }: StatusCardProps) {
  const label = widget.label || widget.id
  const status = state.job_status ?? state.station ?? state.volume ?? '—'
  const extra = state.stage || state.now_playing
  return (
    <div className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4">
      <h3 className="text-sm font-medium text-slate-600 dark:text-slate-300">{label}</h3>
      <p className="text-lg font-semibold text-slate-800 dark:text-white mt-1">{String(status)}</p>
      {extra != null && (
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{JSON.stringify(extra)}</p>
      )}
    </div>
  )
}
