/**
 * Dashboard: Modulübersicht, Links zu Modulseiten.
 * Mobile-first.
 */

import React, { useEffect } from 'react'
import { useRemoteStore } from '../store/remoteStore'
import type { ModuleDescriptor } from '../api/remoteClient'

interface DashboardPageProps {
  onOpenModule: (moduleId: string) => void
}

export default function DashboardPage({ onOpenModule }: DashboardPageProps) {
  const sessionToken = useRemoteStore((s) => s.sessionToken)
  const deviceInfo = useRemoteStore((s) => s.deviceInfo)
  const modules = useRemoteStore((s) => s.modules)
  const error = useRemoteStore((s) => s.error)
  const fetchDeviceInfo = useRemoteStore((s) => s.fetchDeviceInfo)
  const fetchModules = useRemoteStore((s) => s.fetchModules)
  const clearSession = useRemoteStore((s) => s.clearSession)

  useEffect(() => {
    if (sessionToken) {
      fetchDeviceInfo()
      fetchModules()
    }
  }, [sessionToken, fetchDeviceInfo, fetchModules])

  return (
    <div className="p-4 max-w-lg mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-800 dark:text-white">Remote Companion</h1>
        <button
          type="button"
          onClick={clearSession}
          className="text-sm text-slate-500 dark:text-slate-400 hover:text-red-600"
        >
          Abmelden
        </button>
      </div>

      {error && (
        <div className="rounded-lg bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200 px-3 py-2 text-sm">
          {error}
        </div>
      )}

      {deviceInfo && (
        <section className="rounded-xl bg-slate-100 dark:bg-slate-800 p-4">
          <h2 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-1">Gerät</h2>
          <p className="text-slate-800 dark:text-white font-mono text-sm">
            {(deviceInfo.name as string) || (deviceInfo.device_id as string) || '—'}
          </p>
        </section>
      )}

      <section>
        <h2 className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-2">Module</h2>
        <ul className="space-y-2">
          {modules.map((mod: ModuleDescriptor) => (
            <li key={mod.id}>
              <button
                type="button"
                onClick={() => onOpenModule(mod.id)}
                className="w-full text-left rounded-xl bg-slate-100 dark:bg-slate-800 p-4 hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
              >
                <span className="font-medium text-slate-800 dark:text-white">{mod.name}</span>
                {mod.description && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">{mod.description}</p>
                )}
              </button>
            </li>
          ))}
        </ul>
        {modules.length === 0 && !error && (
          <p className="text-sm text-slate-500 dark:text-slate-400">Keine Module geladen.</p>
        )}
      </section>
    </div>
  )
}
