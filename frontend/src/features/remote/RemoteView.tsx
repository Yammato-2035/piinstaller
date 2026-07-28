/**
 * Remote-Companion-Container: Pair / Dashboard / Module je nach Session und Auswahl.
 * Refresh-Token (persistiert) entscheidet über Pairing-Status; Access-Token wird
 * bei Mount proaktiv erneuert, WebSocket startet sobald ein Access-Token vorliegt.
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
  const refreshToken = useRemoteStore((s) => s.refreshToken)
  const accessToken = useRemoteStore((s) => s.accessToken)
  const modules = useRemoteStore((s) => s.modules)
  const ensureFreshAccessToken = useRemoteStore((s) => s.ensureFreshAccessToken)
  const startWs = useRemoteStore((s) => s.startWs)
  const [selectedModuleId, setSelectedModuleId] = useState<string | null>(null)

  useEffect(() => {
    if (refreshToken) ensureFreshAccessToken()
  }, [refreshToken, ensureFreshAccessToken])

  useEffect(() => {
    if (accessToken) startWs()
  }, [accessToken, startWs])

  const descriptor: ModuleDescriptor | null =
    selectedModuleId ? modules.find((m) => m.id === selectedModuleId) ?? null : null

  if (!refreshToken) {
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
