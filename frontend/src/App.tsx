import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Toaster } from 'react-hot-toast'
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
import TFTPage from './pages/TFTPage'
import RadioPlayer from './components/RadioPlayer'
import FirstRunWizard, { FIRST_RUN_DONE_KEY } from './components/FirstRunWizard'
import RunningBackupModal from './components/RunningBackupModal'
import { fetchApi } from './api'
import { PlatformProvider, platformFromSystemInfo } from './context/PlatformContext'
import './App.css'

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
  | 'tft'

type Theme = 'light' | 'dark' | 'system'

const isDsiRadioView = () =>
  typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('view') === 'dsi-radio'

function App() {
  const dsiRadioView = isDsiRadioView()
  const [currentPage, setCurrentPage] = useState<Page>('dashboard')
  const [systemInfo, setSystemInfo] = useState<any>(null)
  const [freenoveDetected, setFreenoveDetected] = useState(false)
  const [backendError, setBackendError] = useState(false)
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
      document.title = 'PI-Installer DSI Radio'
    }
  }, [dsiRadioView])

  const fetchSystemInfo = useCallback(async () => {
    setBackendError(false)
    const maxRetries = 3
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 15000)
        const response = await fetchApi('/api/system-info', { signal: controller.signal })
        clearTimeout(timeoutId)
        const data = await response.json()
        setSystemInfo(data)
        return
      } catch (error) {
        if (attempt < maxRetries) {
          await new Promise((r) => setTimeout(r, 1500))
          continue
        }
        console.error('Fehler beim Laden der Systeminfo:', error)
        setBackendError(true)
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
    const handler = () => fetchSystemInfo()
    window.addEventListener('pi-installer-screenshot-mode-changed', handler)
    return () => window.removeEventListener('pi-installer-screenshot-mode-changed', handler)
  }, [fetchSystemInfo])

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
        return <Dashboard systemInfo={systemInfo} setCurrentPage={handlePageChange} />
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
        return platform?.isRaspberryPi ? <RaspberryPiConfig /> : <Dashboard systemInfo={systemInfo} setCurrentPage={handlePageChange} />
      case 'control-center':
        return <ControlCenter isRaspberryPi={platform?.isRaspberryPi ?? false} />
      case 'periphery-scan':
        return <PeripheryScan setCurrentPage={handlePageChange} />
      case 'settings':
        return <SettingsPage setCurrentPage={handlePageChange} />
      case 'documentation':
        return <Documentation />
      case 'app-store':
        return <AppStore freenoveDetected={freenoveDetected} setCurrentPage={handlePageChange} />
      case 'tft':
        return <TFTPage />
      default:
        return <Dashboard systemInfo={systemInfo} backendError={backendError} setCurrentPage={handlePageChange} />
    }
  }

  const platform = useMemo(() => platformFromSystemInfo(systemInfo), [systemInfo])

  if (dsiRadioView) {
    return (
      <div className="fixed inset-0 bg-slate-900 text-white overflow-auto flex flex-col items-center justify-center p-4">
        <RadioPlayer compact dsi />
      </div>
    )
  }

  return (
    <PlatformProvider value={platform}>
      <div className="flex h-screen bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100">
        {!firstRunDone && (
          <FirstRunWizard
            onComplete={() => setFirstRunDone(true)}
            setCurrentPage={handlePageChange}
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
          <span className="font-semibold text-slate-800 dark:text-white">PI-Installer</span>
        </header>
        <Sidebar currentPage={currentPage} setCurrentPage={handlePageChange} theme={theme} setTheme={handleThemeChange} isRaspberryPi={platform.isRaspberryPi} freenoveDetected={freenoveDetected} mobileOpen={mobileMenuOpen} onClose={() => setMobileMenuOpen(false)} />
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
  )
}

export default App
