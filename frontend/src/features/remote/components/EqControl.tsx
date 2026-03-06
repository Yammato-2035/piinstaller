import React from 'react'

interface Widget {
  id: string
  type: string
  label?: string
}

interface EqControlProps {
  widget: Widget
  state: Record<string, unknown>
  onAction: (actionId: string, payload: Record<string, unknown>) => void
}

export default function EqControl({ widget, state, onAction }: EqControlProps) {
  const label = widget.label || widget.id
  const eq = (state.eq as Record<string, number>) || {}
  const handleSet = () => onAction('set_eq', { eq: { ...eq } })
  return (
    <div className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4">
      <h3 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">{label}</h3>
      <p className="text-xs text-slate-500 dark:text-slate-400 mb-2">
        EQ-Stub (Anpassung in Modul-Aktion)
      </p>
      <button
        type="button"
        onClick={handleSet}
        className="px-3 py-1.5 rounded-lg bg-sky-600 text-white text-sm hover:bg-sky-700"
      >
        EQ setzen
      </button>
    </div>
  )
}
