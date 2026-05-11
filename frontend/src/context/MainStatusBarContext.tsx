import React, { createContext, useContext, useMemo, useState } from 'react'

export type MainStatusTone = 'danger' | 'neutral' | 'soft' | 'calm'

export interface MainStatusPayload {
  lines: string[]
  tone: MainStatusTone
}

type Ctx = {
  status: MainStatusPayload | null
  setStatus: (s: MainStatusPayload | null) => void
}

const MainStatusBarContext = createContext<Ctx | null>(null)

export function MainStatusBarProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<MainStatusPayload | null>(null)
  const value = useMemo(() => ({ status, setStatus }), [status])
  return <MainStatusBarContext.Provider value={value}>{children}</MainStatusBarContext.Provider>
}

export function useMainStatusBar(): Ctx {
  const ctx = useContext(MainStatusBarContext)
  if (!ctx) throw new Error('useMainStatusBar: Provider fehlt')
  return ctx
}

export function useOptionalMainStatusBar(): Ctx | null {
  return useContext(MainStatusBarContext)
}
