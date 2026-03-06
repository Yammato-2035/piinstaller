import React from 'react'

interface Widget {
  id: string
  type: string
  label?: string
}

interface PresetGridProps {
  widget: Widget
  state: Record<string, unknown>
  onAction: (actionId: string, payload: Record<string, unknown>) => void
}

export default function PresetGrid({ widget, state, onAction }: PresetGridProps) {
  const label = widget.label || widget.id
  const station = state.station as string | undefined
  const presets = ['Preset 1', 'Preset 2', 'Preset 3']
  return (
    <div className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4">
      <h3 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">{label}</h3>
      <div className="flex flex-wrap gap-2">
        {presets.map((name, i) => {
          const presetId = 'preset-' + (i + 1)
          const active = station === presetId
          return (
            <button
              key={presetId}
              type="button"
              onClick={() => onAction('play_preset', { preset_id: presetId })}
              className={
                active
                  ? 'px-3 py-2 rounded-lg text-sm font-medium bg-sky-600 text-white'
                  : 'px-3 py-2 rounded-lg text-sm font-medium bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 hover:bg-slate-300 dark:hover:bg-slate-600'
              }
            >
              {name}
            </button>
          )
        })}
      </div>
    </div>
  )
}
