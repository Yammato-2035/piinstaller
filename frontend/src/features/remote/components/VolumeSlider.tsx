import React, { useState } from 'react'

interface Widget {
  id: string
  type: string
  label?: string
}

interface VolumeSliderProps {
  widget: Widget
  state: Record<string, unknown>
  onAction: (actionId: string, payload: Record<string, unknown>) => void
}

export default function VolumeSlider({ widget, state, onAction }: VolumeSliderProps) {
  const label = widget.label || widget.id
  const volume = typeof state.volume === 'number' ? state.volume : 80
  const muted = Boolean(state.muted)
  const [localVolume, setLocalVolume] = useState(volume)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = Number(e.target.value)
    setLocalVolume(v)
    onAction('set_volume', { value: v })
  }

  return (
    <div className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4">
      <h3 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">{label}</h3>
      <div className="flex items-center gap-3">
        <input
          type="range"
          min={0}
          max={100}
          value={muted ? 0 : localVolume}
          onChange={handleChange}
          className="flex-1 h-2 rounded-lg appearance-none bg-slate-300 dark:bg-slate-600 accent-sky-600"
        />
        <span className="text-sm font-mono w-10 text-slate-700 dark:text-slate-200">
          {muted ? 'Mute' : localVolume}
        </span>
        <button
          type="button"
          onClick={() => onAction('mute_toggle', {})}
          className="px-2 py-1 rounded text-xs bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 dark:hover:bg-slate-600"
        >
          {muted ? 'An' : 'Stumm'}
        </button>
      </div>
    </div>
  )
}
