/**
 * Modulansicht: State anzeigen, Widgets rendern, Aktionen ausführen.
 * Lädt State und reagiert auf Live-Events (Store wird per WS aktualisiert).
 */

import React, { useEffect } from 'react'
import toast from 'react-hot-toast'
import { useRemoteStore } from '../store/remoteStore'
import type { ModuleDescriptor } from '../api/remoteClient'
import StatusCard from '../components/StatusCard'
import PresetGrid from '../components/PresetGrid'
import VolumeSlider from '../components/VolumeSlider'
import EqControl from '../components/EqControl'
import LogViewer from '../components/LogViewer'

interface ModulePageProps {
  moduleId: string
  descriptor: ModuleDescriptor | null
  onBack: () => void
}

export default function ModulePage({ moduleId, descriptor, onBack }: ModulePageProps) {
  const moduleStates = useRemoteStore((s) => s.moduleStates)
  const fetchModuleState = useRemoteStore((s) => s.fetchModuleState)
  const performAction = useRemoteStore((s) => s.performAction)
  const state = moduleStates[moduleId] || {}

  useEffect(() => {
    fetchModuleState(moduleId)
  }, [moduleId, fetchModuleState])

  const handleAction = async (actionId: string, payload: Record<string, unknown>) => {
    const result = await performAction(moduleId, actionId, payload)
    if (result.success) toast.success(result.message || 'OK')
    else toast.error(result.message || 'Fehler')
  }

  if (!descriptor) {
    return (
      <div className="p-4">
        <button type="button" onClick={onBack} className="text-sky-600 dark:text-sky-400">
          ← Zurück
        </button>
        <p className="mt-4 text-slate-500">Modul nicht gefunden.</p>
      </div>
    )
  }

  return (
    <div className="p-4 max-w-lg mx-auto space-y-4">
      <div className="flex items-center gap-3">
        <button type="button" onClick={onBack} className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700">
          ←
        </button>
        <h1 className="text-xl font-bold text-slate-800 dark:text-white">{descriptor.name}</h1>
      </div>

      {descriptor.widgets.map((w) => {
        if (w.type === 'StatusCard') return <StatusCard key={w.id} widget={w} state={state} />
        if (w.type === 'PresetGrid') return <PresetGrid key={w.id} widget={w} state={state} onAction={handleAction} />
        if (w.type === 'VolumeSlider') return <VolumeSlider key={w.id} widget={w} state={state} onAction={handleAction} />
        if (w.type === 'EqControl') return <EqControl key={w.id} widget={w} state={state} onAction={handleAction} />
        if (w.type === 'LogViewer') return <LogViewer key={w.id} widget={w} state={state} />
        return (
          <div key={w.id} className="rounded-xl bg-slate-100 dark:bg-slate-800 p-3">
            <span className="text-sm font-medium text-slate-600 dark:text-slate-300">{w.label || w.id}</span>
            <pre className="mt-1 text-xs text-slate-700 dark:text-slate-200 overflow-auto max-h-24">
              {JSON.stringify(state)}
            </pre>
          </div>
        )
      })}

      {descriptor.actions.length > 0 && (
        <section className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4">
          <h2 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">Aktionen</h2>
          <div className="flex flex-wrap gap-2">
            {descriptor.actions.map((a) => (
              <button
                key={a.id}
                type="button"
                onClick={() => handleAction(a.id, {})}
                className="px-3 py-1.5 rounded-lg bg-sky-600 text-white text-sm font-medium hover:bg-sky-700"
              >
                {a.label}
              </button>
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
