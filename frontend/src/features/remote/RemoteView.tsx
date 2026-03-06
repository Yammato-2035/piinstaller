/**
 * Remote-Companion-Container: Pair / Dashboard / Module je nach Session und Auswahl.
 * Session beim Mount aus localStorage laden; WebSocket starten bei Session.
 */

import React, { useEffect, useState } from 'react'
import PairPage from './pages/PairPage'
import DashboardPage from './pages/DashboardPage'
import ModulePage from './pages/ModulePage'
import { useRemoteStore } from './store/remoteStore'
import type { ModuleDescriptor } from './api/remoteClient'

interface RemoteViewProps {
  setCurrentPage: (page: string) => void
}

export default function RemoteView({ setCurrentPage }: RemoteViewProps) {
  const sessionToken = useRemoteStore((s) => s.sessionToken)
  const modules = useRemoteStore((s) => s.modules)
  const loadSessionFromStorage = useRemoteStore((s) => s.loadSessionFromStorage)
  const startWs = useRemoteStore((s) => s.startWs)
  const [selectedModuleId, setSelectedModuleId] = useState<string | null>(null)

  useEffect(() => {
    loadSessionFromStorage()
  }, [loadSessionFromStorage])

  useEffect(() => {
    if (sessionToken) startWs()
  }, [sessionToken, startWs])

  const descriptor: ModuleDescriptor | null =
    selectedModuleId ? modules.find((m) => m.id === selectedModuleId) ?? null : null

  if (!sessionToken) {
    return <PairPage />
  }

  if (selectedModuleId && descriptor) {
    return (
      <ModulePage
        moduleId={selectedModuleId}
        descriptor={descriptor}
        onBack={() => setSelectedModuleId(null)}
      />
    )
  }

  return <DashboardPage onOpenModule={(id) => setSelectedModuleId(id)} />
}
