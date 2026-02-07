import React, { useState, useEffect } from 'react'
import { Monitor, Cpu, Radio, Clock, Image, HardDrive, Home } from 'lucide-react'
import { fetchApi } from '../api'

type TFTMode = 'dashboard' | 'radio' | 'alarm' | 'gallery' | 'nas' | 'smarthome' | 'idle'

interface ModeInfo {
  id: TFTMode
  label: string
  description: string
  icon: React.ElementType
}

const TFT_MODES: ModeInfo[] = [
  { id: 'dashboard', label: 'Dashboard', description: 'CPU, RAM, Temperatur', icon: Cpu },
  { id: 'radio', label: 'Internetradio', description: 'Streams vom Pi', icon: Radio },
  { id: 'alarm', label: 'Wecker', description: 'Alarm auf dem Display', icon: Clock },
  { id: 'gallery', label: 'Bilderrahmen', description: 'Fotos im Loop', icon: Image },
  { id: 'nas', label: 'NAS-Auslastung', description: 'Speicher-Übersicht', icon: HardDrive },
  { id: 'smarthome', label: 'Hauszentrale', description: 'Smart-Home-Status', icon: Home },
  { id: 'idle', label: 'Leerlauf', description: 'Uhr und Info', icon: Monitor },
]

const TFTPage: React.FC = () => {
  const [mode, setMode] = useState<TFTMode>('dashboard')
  const [resources, setResources] = useState<{ cpu?: number; ram_percent?: number; temperature_c?: number } | null>(null)

  useEffect(() => {
    let cancelled = false
    const load = async () => {
      try {
        const res = await fetchApi('/api/system/resources')
        if (res.ok && !cancelled) {
          const data = await res.json()
          setResources(data)
        }
      } catch {
        /* ignore */
      }
    }
    load()
    const t = setInterval(load, 2000)
    return () => {
      cancelled = true
      clearInterval(t)
    }
  }, [])

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-slate-800 dark:text-slate-100 flex items-center gap-3">
          <Monitor className="w-9 h-9 text-emerald-600" />
          TFT Display (Freenove 4,3″)
        </h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Modi für das Gehäuse-Display – Dashboard, Radio, Wecker und mehr. Lautsprecher: System-Sound → Ausgabegerät wählen.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {TFT_MODES.map(m => {
          const Icon = m.icon
          const isActive = mode === m.id
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => setMode(m.id)}
              className={`p-4 rounded-xl border text-left transition-all ${
                isActive
                  ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
                  : 'border-slate-200 dark:border-slate-700 hover:border-slate-300 dark:hover:border-slate-600'
              }`}
            >
              <Icon className={`w-6 h-6 mb-2 ${isActive ? 'text-emerald-600' : 'text-slate-500'}`} />
              <div className="font-medium text-slate-800 dark:text-slate-100">{m.label}</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">{m.description}</div>
            </button>
          )
        })}
      </div>

      <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-slate-800 dark:text-slate-100 mb-4">Vorschau: {TFT_MODES.find(m => m.id === mode)?.label}</h2>
        {mode === 'dashboard' && (
          <div className="flex flex-wrap gap-6">
            <div className="px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-400">CPU</div>
              <div className="text-2xl font-bold text-slate-800 dark:text-slate-100">{resources?.cpu != null ? `${Math.round(resources.cpu)}%` : '—'}</div>
            </div>
            <div className="px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-400">RAM</div>
              <div className="text-2xl font-bold text-slate-800 dark:text-slate-100">{resources?.ram_percent != null ? `${Math.round(resources.ram_percent)}%` : '—'}</div>
            </div>
            <div className="px-4 py-3 rounded-xl bg-slate-100 dark:bg-slate-700">
              <div className="text-xs text-slate-500 dark:text-slate-400">Temp</div>
              <div className="text-2xl font-bold text-slate-800 dark:text-slate-100">{resources?.temperature_c != null ? `${resources.temperature_c}°C` : '—'}</div>
            </div>
          </div>
        )}
        {(mode === 'radio' || mode === 'alarm' || mode === 'gallery' || mode === 'nas' || mode === 'smarthome' || mode === 'idle') && (
          <p className="text-slate-500 dark:text-slate-400">
            Modus „{TFT_MODES.find(m => m.id === mode)?.label}“ – Implementierung folgt. DSI-Display für Kiosk-Modus nutzen.
          </p>
        )}
      </div>
    </div>
  )
}

export default TFTPage
