/**
 * UI-Modus für Grundlagen / Erweiterte Funktionen / Diagnose.
 * Phase 5: Einsteiger sehen weniger Optionen, Experten haben vollen Zugriff.
 */
import React, { createContext, useContext, useCallback, useState, useEffect } from 'react'

export type UIMode = 'basic' | 'advanced' | 'diagnose'

const STORAGE_KEY = 'pi-installer-ui-mode'

const UIModeContext = createContext<{
  mode: UIMode
  setMode: (m: UIMode) => void
}>({ mode: 'basic', setMode: () => {} })

export function useUIMode() {
  return useContext(UIModeContext)
}

export function UIModeProvider({ children }: { children: React.ReactNode }) {
  const [mode, setModeState] = useState<UIMode>(() => {
    try {
      const s = localStorage.getItem(STORAGE_KEY)
      if (s === 'basic' || s === 'advanced' || s === 'diagnose') return s
    } catch { /* ignore */ }
    return 'basic'
  })

  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, mode)
    } catch { /* ignore */ }
  }, [mode])

  const setMode = useCallback((m: UIMode) => {
    setModeState(m)
  }, [])

  return (
    <UIModeContext.Provider value={{ mode, setMode }}>
      {children}
    </UIModeContext.Provider>
  )
}
