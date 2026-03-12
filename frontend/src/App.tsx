import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Toaster, toast } from 'react-hot-toast'
import Sidebar from './components/Sidebar'
import SudoPasswordDialog from './components/SudoPasswordDialog'
import Dashboard from './pages/Dashboard'
import SecuritySetup from './pages/SecuritySetup'
import UserManagement from './pages/UserManagement'
import DevelopmentEnv from './pages/DevelopmentEnv'
import WebServerSetup from './pages/WebServerSetup'
import MailServerSetup from './pages/MailServerSetup'
import NASSetup from './pages/NASSetup'
import HomeAutomationSetup from './pages/HomeAutomationSetup'
import MusicBoxSetup from './pages/MusicBoxSetup'
import InstallationWizard from './pages/InstallationWizard'
import PresetsSetup from './pages/PresetsSetup'
import LearningComputerSetup from './pages/LearningComputerSetup'
import MonitoringDashboard from './pages/MonitoringDashboard'
import BackupRestore from './pages/BackupRestore'
import SettingsPage from './pages/SettingsPage'
import RaspberryPiConfig from './pages/RaspberryPiConfig'
import ControlCenter from './pages/ControlCenter'
import PeripheryScan from './pages/PeripheryScan'
import KinoStreaming from './pages/KinoStreaming'
import Documentation from './pages/Documentation'
import AppStore from './pages/AppStore'
import PiInstallerUpdate from './pages/PiInstallerUpdate'
import TFTPage from './pages/TFTPage'
import DsiRadioSettings from './pages/DsiRadioSettings'
import RadioPlayer from './components/RadioPlayer'
import RemoteView from './features/remote/RemoteView'
import FirstRunWizard, { FIRST_RUN_DONE_KEY } from './components/FirstRunWizard'
import RunningBackupModal from './components/RunningBackupModal'
import { fetchApi, getApiBase, setApiBase } from './api'
import { PlatformProvider, platformFromSystemInfo } from './context/PlatformContext'
import { UIModeProvider } from './context/UIModeContext'
import './App.css'

/* REGRESSION-RISK: Neue Menüeinträge/Pages nur mit existierendem Ziel; Grundlagen vs. Erweitert sauber trennen. */
type Page = 
  | 'dashboard' 
  | 'security' 
  | 'users' 
  | 'devenv' 
  | 'webserver' 
  | 'mailserver' 
  | 'nas'
  | 'homeautomation'
  | 'musicbox'
  | 'kino-streaming'
  | 'wizard'
  | 'presets'
  | 'learning'
  | 'monitoring'
  | 'backup'
  | 'raspberry-pi-config'
  | 'control-center'
  | 'periphery-scan'
  | 'settings'
  | 'documentation'
  | 'app-store'
  | 'pi-installer-update'
  | 'tft'
  | 'dsi-radio-settings'
  | 'remote'

type Theme = 'light' | 'dark' | 'system'

const isDsiRadioView = () =>
  typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('view') === 'dsi-radio'

function getInitialPage(): Page {
  if (typeof window === 'undefined') return 'dashboard'
  const p = new URLSearchParams(window.location.search).get('page')
  if (p === 'tft') return 'tft'
  if (p && ['dashboard', 'security', 'users', 'devenv', 'webserver', 'mailserver', 'nas', 'homeautomation', 'musicbox', 'kino-streaming', 'wizard', 'presets', 'learning', 'monitoring', 'backup', 'raspberry-pi-config', 'control-center', 'periphery-scan', 'settings', 'documentation', 'app-store', 'pi-installer-update', 'dsi-radio-settings', 'remote'].includes(p)) return p as Page
  return 'dashboard'
}

function App() {
  const dsiRadioView = isDsiRadioView()
  const [currentPage, setCurrentPage] = useState<Page>(getInitialPage)
  const [systemInfo, setSystemInfo] = useState<any>(null)
  const [freenoveDetected, setFreenoveDetected] = useState(false)
  const [backendError, setBackendError] = useState(false)
  const [backendErrorReason, setBackendErrorReason] = useState<'timeout' | 'connection' | 'other' | null>(null)
  const [sudoPasswordReady, setSudoPasswordReady] = useState(false)
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('pi-installer-theme')
    return (saved as Theme) || 'system'
  })
  const [firstRunDone, setFirstRunDone] = useState(() => {
    try {
      return localStorage.getItem(FIRST_RUN_DONE_KEY) === '1'
    } catch {
      return true
    }
  })
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [experienceLevel, setExperienceLevel] = useState<'beginner' | 'advanced' | 'developer'>('beginner')

  const handleSudoPasswordSaved = useCallback(() => {
    setSudoPasswordReady(true)
  }, [])
  
  const handlePageChange = useCallback((page: Page) => {
    setCurrentPage(page)
    setMobileMenuOpen(false)
  }, [])
  
  const handleThemeChange = useCallback((newTheme: Theme) => {
    setTheme(newTheme)
  }, [])

  useEffect(() => {
    if (typeof window !== 'undefined' && (window as any).__TAURI__) {
      document.documentElement.setAttribute('data-tauri', 'true')
    }
  }, [])

  useEffect(() => {
    if (dsiRadioView) {
      document.title = 'Sabrina Tuner'
    }
  }, [dsiRadioView])

  const platform = useMemo(() => platformFromSystemInfo(systemInfo), [systemInfo])

  useEffect(() => {
    if (!dsiRadioView && platform.appTitle) {
      document.title = platform.appTitle
    }
  }, [dsiRadioView, platform.appTitle])

  const fetchSystemInfo = useCallback(async () => {
    setBackendError(false)
    setBackendErrorReason(null)
    const base = getApiBase() || 'http://127.0.0.1:8000'
    const timeoutMs = 15000
    const maxRetries = 3

    const tryFetch = async (apiBase: string): Promise<Response> => {
      const url = `${apiBase.replace(/\/$/, '')}/api/system-info`
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs)
      const res = await fetch(url, { signal: controller.signal })
      clearTimeout(timeoutId)
      return res
    }

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const response = await tryFetch(base)
        const data = await response.json()
        setSystemInfo(data)
        return
      } catch (error) {
        const isAbort = error instanceof Error && error.name === 'AbortError'
        const reason: 'timeout' | 'connection' | 'other' = isAbort ? 'timeout' : 'connection'
        if (attempt < maxRetries) {
          await new Promise((r) => setTimeout(r, 1500))
          continue
        }
        console.error('Fehler beim Laden der Systeminfo:', error)
        setBackendErrorReason(reason)
        setBackendError(true)
        // Fallback: Wenn Standard-URL 127.0.0.1 war, einmal localhost probieren (IPv6/Resolver-Probleme)
        if (base === 'http://127.0.0.1:8000') {
          try {
            const res = await tryFetch('http://localhost:8000')
            const data = await res.json()
            setApiBase('http://localhost:8000')
            setSystemInfo(data)
            setBackendError(false)
            setBackendErrorReason(null)
            return
          } catch {
            // Fallback fehlgeschlagen, Fehlerzustand bleibt
          }
        }
      }
    }
  }, [])

  const fetchFreenoveDetection = useCallback(async () => {
    try {
      const res = await fetchApi('/api/system/freenove-detection')
      if (!res.ok) return
      const data = await res.json()
      setFreenoveDetected(data?.detected === true)
    } catch {
      setFreenoveDetected(false)
    }
  }, [])

  useEffect(() => {
    fetchSystemInfo()
  }, [fetchSystemInfo])

  useEffect(() => {
    fetchFreenoveDetection()
  }, [fetchFreenoveDetection])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetchApi('/api/user-profile')
        if (!res.ok || cancelled) return
        const data = await res.json()
        if (!cancelled && data?.profile?.experience_level) {
          const level = String(data.profile.experience_level).toLowerCase()
          if (level === 'advanced' || level === 'developer') setExperienceLevel(level)
          else setExperienceLevel('beginner')
        }
      } catch {
        // Default bleibt beginner
      }
    })()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    const handler = () => fetchSystemInfo()
    window.addEventListener('pi-installer-screenshot-mode-changed', handler)
    return () => window.removeEventListener('pi-installer-screenshot-mode-changed', handler)
  }, [fetchSystemInfo])

  useEffect(() => {
    const handler = () => fetchSystemInfo()
    window.addEventListener('pi-installer-api-base-changed', handler)
    return () => window.removeEventListener('pi-installer-api-base-changed', handler)
  }, [fetchSystemInfo])

  // F10: Screenshot vom App-Fenster (nur in Tauri-Desktop-App)
  useEffect(() => {
    const isTauri = typeof window !== 'undefined' && !!(window as any).__TAURI__
    if (!isTauri) return

    const handleKeyDown = async (event: KeyboardEvent) => {
      if (event.key !== 'F10') return
      event.preventDefault()
      try {
        const { getScreenshotableWindows, getWindowScreenshot } = await import('tauri-plugin-screenshots-api')
        const windows = await getScreenshotableWindows()
        const main = windows.find((w: { title?: string }) =>
          (w.title || '').includes('PI-Installer') || (w.title || '').includes('Sabrina Tuner') || (w.title || '').includes('Raspberry')
        )
        const windowId = main?.id ?? windows[0]?.id
        if (windowId == null) {
          toast.error('Kein Fenster für Screenshot gefunden')
          return
        }
        const path = await getWindowScreenshot(windowId)
        toast.success(`Screenshot gespeichert:\n${path}`, { duration: 5000 })
      } catch (e: any) {
        console.error('F10 Screenshot:', e)
        toast.error(e?.message || 'Screenshot fehlgeschlagen')
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [])

  useEffect(() => {
    // Theme anwenden
    const root = document.documentElement
    const applyTheme = (t: Theme) => {
      // Entferne alle Theme-Klassen
      root.classList.remove('dark', 'light')
      
      if (t === 'system') {
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        if (prefersDark) {
          root.classList.add('dark')
        } else {
          root.classList.add('light')
        }
      } else {
        root.classList.add(t)
      }
    }
    applyTheme(theme)
    localStorage.setItem('pi-installer-theme', theme)
    
    // Listener für System-Theme-Änderungen
    if (theme === 'system') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
      const handler = () => applyTheme('system')
      mediaQuery.addEventListener('change', handler)
      return () => mediaQuery.removeEventListener('change', handler)
    }
  }, [theme])

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return (
          <Dashboard
            systemInfo={systemInfo}
            backendError={backendError}
            backendErrorReason={backendErrorReason}
            onRetryBackend={fetchSystemInfo}
            setCurrentPage={handlePageChange}
            experienceLevel={experienceLevel}
          />
        )
      case 'security':
        return <SecuritySetup />
      case 'users':
        return <UserManagement />
      case 'devenv':
        return <DevelopmentEnv />
      case 'webserver':
        return <WebServerSetup />
      case 'mailserver':
        return <MailServerSetup />
      case 'nas':
        return <NASSetup />
      case 'homeautomation':
        return <HomeAutomationSetup />
      case 'musicbox':
        return <MusicBoxSetup />
      case 'kino-streaming':
        return <KinoStreaming />
      case 'wizard':
        return <InstallationWizard />
      case 'presets':
        return <PresetsSetup />
      case 'learning':
        return <LearningComputerSetup />
      case 'monitoring':
        return <MonitoringDashboard />
      case 'backup':
        return <BackupRestore />
      case 'raspberry-pi-config':
        return platform?.isRaspberryPi ? (
          <RaspberryPiConfig />
        ) : (
          <Dashboard
            systemInfo={systemInfo}
            backendError={backendError}
            backendErrorReason={backendErrorReason}
            onRetryBackend={fetchSystemInfo}
            setCurrentPage={handlePageChange}
            experienceLevel={experienceLevel}
          />
        )
      case 'control-center':
        return <ControlCenter isRaspberryPi={platform?.isRaspberryPi ?? false} />
      case 'periphery-scan':
        return <PeripheryScan setCurrentPage={handlePageChange} />
      case 'settings':
        return <SettingsPage setCurrentPage={handlePageChange} onExperienceLevelChange={setExperienceLevel} />
      case 'documentation':
        return <Documentation />
      case 'app-store':
        return <AppStore freenoveDetected={freenoveDetected} setCurrentPage={handlePageChange} />
      case 'pi-installer-update':
        return <PiInstallerUpdate />
      case 'tft':
        return <TFTPage />
      case 'dsi-radio-settings':
        return <DsiRadioSettings setCurrentPage={handlePageChange} />
      case 'remote':
        return <RemoteView setCurrentPage={handlePageChange} />
      default:
        return (
          <Dashboard
            systemInfo={systemInfo}
            backendError={backendError}
            backendErrorReason={backendErrorReason}
            onRetryBackend={fetchSystemInfo}
            setCurrentPage={handlePageChange}
            experienceLevel={experienceLevel}
          />
        )
    }
  }

  if (dsiRadioView) {
    return (
      <div className="fixed inset-0 bg-slate-800 text-white overflow-auto flex flex-col items-center justify-center p-4">
        <div className="rounded-2xl border-2 border-[#c0c0c0] shadow-2xl overflow-hidden bg-slate-900 flex flex-col max-w-lg w-full" style={{ boxShadow: '0 0 0 1px #c0c0c0, 0 25px 50px -12px rgba(0,0,0,0.5)' }}>
          {/* Fenstertitelbereich (4px schmaler: py-2 statt py-3) */}
          <header className="flex items-center justify-between px-4 py-2 bg-slate-800 border-b border-[#c0c0c0]/50 shrink-0">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 rounded-full border-2 border-[#c0c0c0] flex items-center justify-center shrink-0" title={backendError ? 'Server nicht erreichbar' : 'Server bereit'}>
                <div className={`w-1.5 h-1.5 rounded-full ${backendError ? 'bg-red-500' : 'bg-emerald-500'}`} />
              </div>
              <div>
                <h1 className="text-base font-bold text-white leading-tight">Sabrina Tuner</h1>
                <p className="text-[10px] text-slate-400 leading-tight">VU-Meter + Titel/Interpret</p>
              </div>
            </div>
          </header>
          <div className="p-4 overflow-auto">
            <RadioPlayer compact dsi backendError={backendError} />
          </div>
        </div>
      </div>
    )
  }

  return (
    <UIModeProvider>
    <PlatformProvider value={platform}>
      <div className="flex h-screen bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100">
        {!firstRunDone && (
          <FirstRunWizard
            onComplete={(level) => {
              setFirstRunDone(true)
              if (level) setExperienceLevel(level)
            }}
            setCurrentPage={handlePageChange}
            systemInfo={systemInfo}
          />
        )}
        <SudoPasswordDialog onPasswordSaved={handleSudoPasswordSaved} />
        <RunningBackupModal />
        {/* Mobile: Hamburger-Leiste */}
        <header className="md:hidden flex items-center gap-3 px-4 py-3 bg-slate-200 dark:bg-slate-800 border-b border-slate-300 dark:border-slate-700">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(true)}
            className="p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700"
            aria-label="Menü öffnen"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
          </button>
          <span className="font-semibold text-slate-800 dark:text-white">{platform.appTitle}</span>
        </header>
        <Sidebar currentPage={currentPage} setCurrentPage={handlePageChange} theme={theme} setTheme={handleThemeChange} isRaspberryPi={platform.isRaspberryPi} freenoveDetected={freenoveDetected} mobileOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} experienceLevel={experienceLevel} />
      <main className="flex-1 overflow-auto bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
        <div className="p-4 sm:p-8 min-h-full">
          <AnimatePresence mode="wait" initial={false}>
            <motion.div
              key={currentPage}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2, ease: [0.25, 0.1, 0.25, 1] }}
              className="min-h-full"
            >
              {renderPage()}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
        <Toaster position="bottom-right" />
      </div>
    </PlatformProvider>
    </UIModeProvider>
  )
}

export default App
