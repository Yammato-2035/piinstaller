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

type Theme = 'light' | 'dark' | 'system'

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('dashboard')
  const [systemInfo, setSystemInfo] = useState<any>(null)
  const [backendError, setBackendError] = useState(false)
  const [sudoPasswordReady, setSudoPasswordReady] = useState(false)
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('pi-installer-theme')
    return (saved as Theme) || 'system'
  })

  const handleSudoPasswordSaved = useCallback(() => {
    setSudoPasswordReady(true)
  }, [])
  
  const handlePageChange = useCallback((page: Page) => {
    setCurrentPage(page)
  }, [])
  
  const handleThemeChange = useCallback((newTheme: Theme) => {
    setTheme(newTheme)
  }, [])

  useEffect(() => {
    const fetchSystemInfo = async () => {
      setBackendError(false)
      try {
        const response = await fetchApi('/api/system-info')
        const data = await response.json()
        setSystemInfo(data)
      } catch (error) {
        console.error('Fehler beim Laden der Systeminfo:', error)
        setBackendError(true)
      }
    }
    fetchSystemInfo()
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
      default:
        return <Dashboard systemInfo={systemInfo} backendError={backendError} setCurrentPage={handlePageChange} />
    }
  }

  const platform = useMemo(() => platformFromSystemInfo(systemInfo), [systemInfo])

  return (
    <PlatformProvider value={platform}>
      <div className="flex h-screen bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100">
        <SudoPasswordDialog onPasswordSaved={handleSudoPasswordSaved} />
        <Sidebar currentPage={currentPage} setCurrentPage={handlePageChange} theme={theme} setTheme={handleThemeChange} isRaspberryPi={platform.isRaspberryPi} />
      <main className="flex-1 overflow-auto bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
        <div className="p-8 min-h-full">
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
