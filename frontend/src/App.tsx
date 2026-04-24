import React, { useState, useEffect, useLayoutEffect, useMemo, useCallback } from 'react'
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
import BootSplash from './components/BootSplash'
import { fetchApi, setScreenshotMode, fetchExperienceLevelFromApi, readStoredExperienceLevel } from './api'
import { getThemeShot, isThemeScreenshotCapture } from './themeScreenshot'
import { PlatformProvider, platformRawFromSystemInfo, usePlatform } from './context/PlatformContext'
import { MainStatusBarProvider, useMainStatusBar, useOptionalMainStatusBar } from './context/MainStatusBarContext'
import { UIModeProvider } from './context/UIModeContext'
import i18n, { setAppLocale } from './i18n'
import { useTranslation } from 'react-i18next'
import './App.css'

function AppDocumentTitle({ dsiRadioView }: { dsiRadioView: boolean }) {
  const { brandTitle, identitySubtitle } = usePlatform()
  useEffect(() => {
    if (!dsiRadioView && brandTitle) {
      document.title = identitySubtitle ? `${brandTitle} · ${identitySubtitle}` : brandTitle
    }
  }, [dsiRadioView, brandTitle, identitySubtitle])
  return null
}

function MobileAppTitle() {
  const { brandTitle, identitySubtitle } = usePlatform()
  return (
    <div className="flex flex-col min-w-0 text-left">
      <span className="font-semibold text-slate-800 dark:text-white truncate">{brandTitle}</span>
      {identitySubtitle ? (
        <span className="text-xs text-slate-500 dark:text-slate-400 truncate">{identitySubtitle}</span>
      ) : null}
    </div>
  )
}

function MobileMainStatusLine() {
  const { t } = useTranslation()
  const ctx = useOptionalMainStatusBar()
  const status = ctx?.status
  if (!status?.lines?.length) {
    return (
      <p className="text-[10px] leading-tight line-clamp-2 text-center w-full mt-1 text-slate-500 dark:text-slate-400" role="status">
        {t('app.header.statusFallback')}
      </p>
    )
  }
  const toneCls =
    status.tone === 'danger'
      ? 'text-red-700 dark:text-red-300'
      : status.tone === 'soft'
        ? 'text-amber-800 dark:text-amber-200'
        : status.tone === 'calm'
          ? 'text-emerald-800 dark:text-emerald-300'
          : 'text-slate-600 dark:text-slate-400'
  return (
    <p className={`text-[10px] leading-tight line-clamp-2 text-center w-full mt-1 ${toneCls}`} role="status">
      {status.lines.join(' · ')}
    </p>
  )
}

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

function AppTopHeader({ headerBackendOk }: { headerBackendOk: boolean | null }) {
  const { t } = useTranslation()
  const { identitySubtitle } = usePlatform()
  const { status } = useMainStatusBar()
  const [uiLang, setUiLang] = useState<'de' | 'en'>(() => (i18n.language?.startsWith('en') ? 'en' : 'de'))

  useEffect(() => {
    const onLang = (lng: string) => setUiLang(lng.startsWith('en') ? 'en' : 'de')
    i18n.on('languageChanged', onLang)
    return () => {
      i18n.off('languageChanged', onLang)
    }
  }, [])

  const hostLabel = identitySubtitle || ''

  const statusToneClass =
    status?.tone === 'danger'
      ? 'text-red-700 dark:text-red-300'
      : status?.tone === 'soft'
        ? 'text-amber-800 dark:text-amber-200'
        : status?.tone === 'calm'
          ? 'text-emerald-800 dark:text-emerald-300'
          : 'text-slate-600 dark:text-slate-300'

  return (
    <header className="hidden md:flex shrink-0 items-stretch gap-2 px-4 sm:px-6 min-h-10 py-1 border-b border-slate-300/80 dark:border-slate-700/80 bg-slate-50/90 dark:bg-slate-900/90 backdrop-blur-sm">
      <div className="text-xs font-semibold text-slate-700 dark:text-slate-200 truncate max-w-[28%] sm:max-w-xs shrink-0 flex items-center">
        {hostLabel}
      </div>
      <div
        className="flex-1 min-w-0 flex flex-col items-center justify-center px-2"
        role="status"
        aria-live="polite"
      >
        {status && status.lines.length > 0 ? (
          <p className={`text-[11px] sm:text-xs text-center leading-snug line-clamp-2 ${statusToneClass}`}>
            {status.lines.join(' · ')}
          </p>
        ) : (
          <p className="text-[11px] sm:text-xs text-center leading-snug line-clamp-2 text-slate-500 dark:text-slate-400">
            {t('app.header.statusFallback')}
          </p>
        )}
      </div>
      <div
        className="shrink-0 self-center flex items-center gap-2 pr-0.5"
        title={
          headerBackendOk === true
            ? t('app.header.backendLed.ok')
            : headerBackendOk === false
              ? t('app.header.backendLed.error')
              : t('app.header.backendLed.checking')
        }
      >
        <span className="sr-only">
          {headerBackendOk === true
            ? t('app.header.backendLed.ok')
            : headerBackendOk === false
              ? t('app.header.backendLed.error')
              : t('app.header.backendLed.checking')}
        </span>
        <span
          className={`h-2.5 w-2.5 rounded-full shrink-0 ring-2 ring-offset-1 ring-offset-slate-50 dark:ring-offset-slate-900 ${
            headerBackendOk === true
              ? 'bg-emerald-500 ring-emerald-500/50 shadow-[0_0_10px_rgba(16,185,129,0.75)]'
              : headerBackendOk === false
                ? 'bg-red-500 ring-red-500/50 shadow-[0_0_10px_rgba(239,68,68,0.75)]'
                : 'bg-slate-400 dark:bg-slate-500 ring-slate-400/30 animate-pulse'
          }`}
          aria-hidden
        />
      </div>
      <div
        className="inline-flex shrink-0 self-center rounded-lg border border-slate-300 dark:border-slate-600 overflow-hidden shadow-sm text-[11px] leading-none"
        role="group"
        aria-label={i18n.t('sidebar.language.aria')}
      >
        <button
          type="button"
          onClick={() => setAppLocale('de')}
          aria-pressed={uiLang === 'de'}
          title={i18n.t('settings.language.de')}
          className={`px-3 py-1 flex items-center justify-center transition-colors ${
            uiLang === 'de'
              ? 'bg-sky-600 text-white'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700'
          }`}
        >
          DE
        </button>
        <button
          type="button"
          onClick={() => setAppLocale('en')}
          aria-pressed={uiLang === 'en'}
          title={i18n.t('settings.language.en')}
          className={`px-3 py-1 flex items-center justify-center border-l border-slate-300 dark:border-slate-600 transition-colors ${
            uiLang === 'en'
              ? 'bg-sky-600 text-white'
              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-700'
          }`}
        >
          EN
        </button>
      </div>
    </header>
  )
}

function App() {
  const dsiRadioView = isDsiRadioView()
  const themeShot = typeof window !== 'undefined' ? getThemeShot() : null
  const [showBootSplash, setShowBootSplash] = useState(() => {
    if (themeShot === 'start') return true
    if (themeShot && themeShot !== 'start') return false
    return true
  })
  const [currentPage, setCurrentPage] = useState<Page>(() => {
    if (themeShot === 'webserver') return 'webserver'
    return getInitialPage()
  })
  const [systemInfo, setSystemInfo] = useState<any>(null)
  const [freenoveDetected, setFreenoveDetected] = useState(false)
  const [backendError, setBackendError] = useState(() => themeShot === 'error')
  const [backendErrorReason, setBackendErrorReason] = useState<'timeout' | 'connection' | 'other' | null>(() =>
    themeShot === 'error' ? 'connection' : null,
  )
  /** Top-Header-LED: null = Prüfung läuft, true = Backend erreichbar, false = nicht erreichbar */
  const [headerBackendOk, setHeaderBackendOk] = useState<boolean | null>(() => (themeShot === 'error' ? false : null))
  const [sudoPasswordReady, setSudoPasswordReady] = useState(false)
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('pi-installer-theme')
    return (saved as Theme) || 'system'
  })
  const [firstRunDone, setFirstRunDone] = useState(() => {
    if (themeShot === 'experience') return false
    if (themeShot === 'start' || themeShot === 'webserver' || themeShot === 'error' || themeShot === 'dashboard') {
      return true
    }
    try {
      return localStorage.getItem(FIRST_RUN_DONE_KEY) === '1'
    } catch {
      return true
    }
  })
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [experienceLevel, setExperienceLevel] = useState<'beginner' | 'advanced' | 'developer'>('beginner')
  /** app_edition aus Backend (api/system-info): 'repo' = Expertenmodul sichtbar, 'release' = nur Benutzerfunktionen */
  const appEdition = systemInfo?.app_edition === 'repo' ? 'repo' : 'release'

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

  useLayoutEffect(() => {
    const ts = getThemeShot()
    if (ts && ts !== 'start') {
      setScreenshotMode(true)
    }
  }, [])

  useEffect(() => {
    if (themeShot === 'start') return
    const timer = window.setTimeout(() => setShowBootSplash(false), 950)
    return () => window.clearTimeout(timer)
  }, [themeShot])

  const platformRaw = useMemo(() => platformRawFromSystemInfo(systemInfo), [systemInfo])

  const fetchSystemInfo = useCallback(async () => {
    setHeaderBackendOk(null)
    setBackendError(false)
    setBackendErrorReason(null)
    const timeoutMs = 15000
    const maxRetries = 3

    let lastReason: 'timeout' | 'connection' | 'other' = 'connection'
    let lastError: unknown = null
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs)
      try {
        const response = await fetchApi('/api/system-info', { signal: controller.signal })
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        const data = await response.json()
        setSystemInfo(data)
        setHeaderBackendOk(true)
        return
      } catch (error) {
        lastError = error
        const isAbort = error instanceof Error && error.name === 'AbortError'
        lastReason = isAbort ? 'timeout' : 'connection'
        if (attempt < maxRetries) {
          await new Promise((r) => setTimeout(r, 1500))
        }
      } finally {
        clearTimeout(timeoutId)
      }
    }
    console.error(i18n.t('app.errors.systemInfoLoad'), lastError)
    setBackendErrorReason(lastReason)
    setBackendError(true)
    setHeaderBackendOk(false)
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
    if (themeShot === 'error') return
    fetchSystemInfo()
  }, [fetchSystemInfo, themeShot])

  useEffect(() => {
    fetchFreenoveDetection()
  }, [fetchFreenoveDetection])

  // RELEASE: Experten-Seite pi-installer-update nicht routbar – auf Dashboard umleiten
  useEffect(() => {
    if (appEdition === 'release' && currentPage === 'pi-installer-update') {
      setCurrentPage('dashboard')
    }
  }, [appEdition, currentPage, setCurrentPage])

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        if (cancelled) return
        const fromApi = await fetchExperienceLevelFromApi()
        const level = fromApi || readStoredExperienceLevel()
        if (cancelled || !level) return
        if (level === 'advanced' || level === 'developer') setExperienceLevel(level)
        else setExperienceLevel('beginner')
      } catch {
        const loc = readStoredExperienceLevel()
        if (!cancelled && loc) {
          if (loc === 'advanced' || loc === 'developer') setExperienceLevel(loc)
          else setExperienceLevel('beginner')
        }
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
          (w.title || '').includes('SetupHelfer') || (w.title || '').includes('Sabrina Tuner') || (w.title || '').includes('Raspberry')
        )
        const windowId = main?.id ?? windows[0]?.id
        if (windowId == null) {
          toast.error(i18n.t('app.screenshot.noWindow'))
          return
        }
        const path = await getWindowScreenshot(windowId)
        toast.success(i18n.t('app.screenshot.saved', { path }), { duration: 5000 })
      } catch (e: any) {
        console.error('F10 Screenshot:', e)
        toast.error(e?.message || i18n.t('app.screenshot.failed'))
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
        return <MailServerSetup experienceLevel={experienceLevel} />
      case 'nas':
        return <NASSetup />
      case 'homeautomation':
        return <HomeAutomationSetup />
      case 'musicbox':
        return <MusicBoxSetup experienceLevel={experienceLevel} />
      case 'kino-streaming':
        return <KinoStreaming experienceLevel={experienceLevel} />
      case 'wizard':
        return <InstallationWizard />
      case 'presets':
        return <PresetsSetup />
      case 'learning':
        return <LearningComputerSetup />
      case 'monitoring':
        return <MonitoringDashboard />
      case 'backup':
        return <BackupRestore experienceLevel={experienceLevel} />
      case 'raspberry-pi-config':
        return platformRaw.isRaspberryPi ? (
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
        return <ControlCenter isRaspberryPi={platformRaw.isRaspberryPi} />
      case 'periphery-scan':
        return <PeripheryScan setCurrentPage={handlePageChange} />
      case 'settings':
        return <SettingsPage setCurrentPage={handlePageChange} onExperienceLevelChange={setExperienceLevel} />
      case 'documentation':
        return <Documentation />
      case 'app-store':
        return <AppStore freenoveDetected={freenoveDetected} setCurrentPage={handlePageChange} />
      case 'pi-installer-update':
        return appEdition === 'repo' ? <PiInstallerUpdate /> : (
          <Dashboard
            systemInfo={systemInfo}
            backendError={backendError}
            backendErrorReason={backendErrorReason}
            onRetryBackend={fetchSystemInfo}
            setCurrentPage={handlePageChange}
            experienceLevel={experienceLevel}
          />
        )
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
    <PlatformProvider systemInfo={systemInfo}>
      <AppDocumentTitle dsiRadioView={dsiRadioView} />
      {showBootSplash ? <BootSplash /> : null}
      <div className="flex h-screen max-h-screen flex-col overflow-hidden bg-slate-100 dark:bg-slate-900 text-slate-900 dark:text-slate-100">
        {!firstRunDone && (
          <FirstRunWizard
            initialStep={themeShot === 'experience' ? 2 : 1}
            onComplete={(level) => {
              setFirstRunDone(true)
              if (level) setExperienceLevel(level)
            }}
            setCurrentPage={handlePageChange}
            systemInfo={systemInfo}
          />
        )}
        {!isThemeScreenshotCapture() ? (
          <SudoPasswordDialog onPasswordSaved={handleSudoPasswordSaved} />
        ) : null}
        <RunningBackupModal />
        <MainStatusBarProvider>
          {/* Spalte auf schmalen Screens (oben Menüzeile, unten Inhalt); Zeile ab md: Sidebar | Hauptteil */}
          <div className="flex min-h-0 flex-1 flex-col md:flex-row">
            <header className="flex flex-none flex-col gap-0 border-b border-slate-300 bg-slate-200 px-4 py-2 dark:border-slate-700 dark:bg-slate-800 md:hidden">
              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setMobileMenuOpen(true)}
                  className="rounded-lg p-2 text-slate-600 hover:bg-slate-300 dark:text-slate-300 dark:hover:bg-slate-700"
                  aria-label={i18n.t('app.mobile.openMenu')}
                >
                  <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  </svg>
                </button>
                <MobileAppTitle />
              </div>
              <MobileMainStatusLine />
            </header>
            <Sidebar
              currentPage={currentPage}
              setCurrentPage={handlePageChange}
              theme={theme}
              setTheme={handleThemeChange}
              isRaspberryPi={platformRaw.isRaspberryPi}
              freenoveDetected={freenoveDetected}
              mobileOpen={mobileMenuOpen}
              onClose={() => setMobileMenuOpen(false)}
              experienceLevel={experienceLevel}
              appEdition={appEdition}
            />
            <main className="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden bg-gradient-to-br from-slate-100 via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900">
              <AppTopHeader headerBackendOk={headerBackendOk} />
              <div className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden p-4 sm:p-8">
                <AnimatePresence mode="wait" initial={false}>
                  <motion.div
                    key={currentPage}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2, ease: [0.25, 0.1, 0.25, 1] }}
                    className="min-h-0"
                  >
                    {renderPage()}
                  </motion.div>
                </AnimatePresence>
              </div>
            </main>
          </div>
        </MainStatusBarProvider>
        <Toaster position="bottom-right" />
      </div>
    </PlatformProvider>
    </UIModeProvider>
  )
}

export default App
