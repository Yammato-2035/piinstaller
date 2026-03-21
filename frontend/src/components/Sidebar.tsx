import React, { useEffect, useState, useMemo, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import i18n, { setAppLocale } from '../i18n'
import { usePlatform } from '../context/PlatformContext'
import { useUIMode, type UIMode } from '../context/UIModeContext'
import AppIcon from './AppIcon'
import RiskLevelBadge from './RiskLevelBadge'
import { getPageRisk } from '../config/riskLevels'
import type { TFunction } from 'i18next'
import {
  Shield,
  Users,
  Code,
  Globe,
  Mail,
  HardDrive,
  Home,
  Music,
  LogOut,
  Settings,
  BookOpen,
  Cpu,
  Moon,
  Sun,
  Monitor,
  Tv,
  Radio,
  Upload,
  Smartphone,
} from 'lucide-react'

type Theme = 'light' | 'dark' | 'system'

export type ExperienceLevel = 'beginner' | 'advanced' | 'developer'

interface SidebarProps {
  currentPage: string
  setCurrentPage: (page: any) => void
  theme: Theme
  setTheme: (theme: Theme) => void
  isRaspberryPi?: boolean
  freenoveDetected?: boolean
  mobileOpen?: boolean
  onClose?: () => void
  /** Aus First-Run-Wizard / API: steuert vereinfachte Sidebar für Einsteiger (Phase 5). */
  experienceLevel?: ExperienceLevel
  /** app_edition vom Backend: nur bei 'repo' wird PI-Installer Update (Expertenmodul) angezeigt */
  appEdition?: 'repo' | 'release'
}

const NEW_BADGE_KEY = 'pi-installer-new-'

/** Phase 5: Für Einsteiger diese Einträge – klare Aufgaben + Einstellungen (u. a. Erfahrungslevel ändern). */
const BEGINNER_MENU_IDS = ['dashboard', 'wizard', 'app-store', 'backup', 'monitoring', 'documentation', 'settings'] as const

function buildMenuItems(
  t: TFunction,
  isRaspberryPi: boolean,
  freenoveDetected: boolean,
  appEdition: 'repo' | 'release'
) {
  type Item = { id?: string; type?: string; labelKey?: string; icon?: any; appIcon?: string; modes?: UIMode[]; developerOnly?: boolean }
  const items: Item[] = [
    { id: 'dashboard', labelKey: 'sidebar.menu.dashboard', appIcon: 'dashboard', modes: ['basic'] },
    { id: 'wizard', labelKey: 'sidebar.menu.wizard', appIcon: 'wizard', modes: ['basic'] },
    { id: 'app-store', labelKey: 'sidebar.menu.appStore', appIcon: 'app-store', modes: ['basic'] },
    { id: 'backup', labelKey: 'sidebar.menu.backup', appIcon: 'backup', modes: ['basic'] },
    { id: 'monitoring', labelKey: 'sidebar.menu.monitoring', appIcon: 'monitoring', modes: ['basic', 'advanced', 'diagnose'] },
    { id: 'documentation', labelKey: 'sidebar.menu.documentation', appIcon: 'documentation', modes: ['basic'] },
    { type: 'divider' },
    { id: 'remote', labelKey: 'sidebar.menu.remote', icon: Smartphone, modes: ['advanced'] },
    ...(freenoveDetected ? [{ id: 'dsi-radio-settings', labelKey: 'sidebar.menu.dsiRadio', icon: Radio, modes: ['basic', 'advanced'] as UIMode[] }] : []),
    { id: 'presets', labelKey: 'sidebar.menu.presets', icon: Settings, modes: ['advanced'] },
    { type: 'divider' },
    { id: 'settings', labelKey: 'sidebar.menu.settings', appIcon: 'settings', modes: ['advanced', 'diagnose'] },
    { id: 'security', labelKey: 'sidebar.menu.security', icon: Shield, modes: ['advanced'] },
    { id: 'users', labelKey: 'sidebar.menu.users', icon: Users, modes: ['advanced'] },
    { type: 'divider' },
    { id: 'control-center', labelKey: 'sidebar.menu.controlCenter', appIcon: 'control-center', modes: ['advanced'] },
    { id: 'periphery-scan', labelKey: 'sidebar.menu.peripheryScan', appIcon: 'periphery-scan', modes: ['advanced', 'diagnose'] },
    { id: 'webserver', labelKey: 'sidebar.menu.webserver', icon: Globe, modes: ['advanced'] },
    { id: 'nas', labelKey: 'sidebar.menu.nas', icon: HardDrive, modes: ['advanced'] },
    { id: 'homeautomation', labelKey: 'sidebar.menu.homeAutomation', icon: Home, modes: ['advanced'] },
    { id: 'musicbox', labelKey: 'sidebar.menu.musicbox', icon: Music, modes: ['advanced'] },
    { id: 'kino-streaming', labelKey: 'sidebar.menu.kinoStreaming', icon: Tv, modes: ['advanced'] },
    { id: 'learning', labelKey: 'sidebar.menu.learning', icon: BookOpen, modes: ['advanced'] },
    ...(appEdition === 'repo' ? [{ id: 'pi-installer-update', labelKey: 'sidebar.menu.setuphelferUpdate', icon: Upload, modes: ['advanced'] as UIMode[] }] : []),
    { id: 'devenv', labelKey: 'sidebar.menu.devenv', icon: Code, modes: ['advanced'], developerOnly: true },
    { id: 'mailserver', labelKey: 'sidebar.menu.mailserver', icon: Mail, modes: ['advanced'], developerOnly: true },
  ]
  if (isRaspberryPi) {
    items.push({ id: 'raspberry-pi-config', labelKey: 'sidebar.menu.raspberryPiConfig', icon: Cpu, modes: ['advanced'] })
  }
  return items
}

const SidebarComponent: React.FC<SidebarProps> = ({ currentPage, setCurrentPage, theme, setTheme, isRaspberryPi = false, freenoveDetected = false, mobileOpen = false, onClose, experienceLevel = 'beginner', appEdition = 'release' }) => {
  const { t } = useTranslation()
  const { appTitle } = usePlatform()
  const { mode, setMode } = useUIMode()
  const isBeginnerSidebar = experienceLevel === 'beginner'
  // Build-Zeit-Version (package.json) – zeigt die Version der laufenden App/Frontend
  const [version] = useState<string>(typeof __APP_VERSION__ !== 'undefined' ? __APP_VERSION__ : '…')
  const [newBadges, setNewBadges] = useState<Record<string, boolean>>({})
  const [uiLang, setUiLang] = useState<'de' | 'en'>(() => (i18n.language?.startsWith('en') ? 'en' : 'de'))

  useEffect(() => {
    const onLang = (lng: string) => setUiLang(lng.startsWith('en') ? 'en' : 'de')
    i18n.on('languageChanged', onLang)
    return () => {
      i18n.off('languageChanged', onLang)
    }
  }, [])

  useEffect(() => {
    const badges: Record<string, boolean> = {}
    const ids = ['monitoring', 'periphery-scan', 'security', 'webserver', 'nas', 'homeautomation', 'musicbox', 'devenv', 'backup']
    ids.forEach(id => {
      try {
        if (typeof localStorage !== 'undefined' && localStorage.getItem(NEW_BADGE_KEY + id)) badges[id] = true
      } catch { /* ignore */ }
    })
    setNewBadges(badges)
  }, [currentPage])

  const menuItems = useMemo(() => buildMenuItems(t, isRaspberryPi, freenoveDetected, appEdition), [t, isRaspberryPi, freenoveDetected, appEdition])

  const filteredItems = useMemo(() => {
    if (isBeginnerSidebar) {
      return menuItems.filter((item) => {
        if (item.type === 'divider') return false
        return item.id && BEGINNER_MENU_IDS.includes(item.id as typeof BEGINNER_MENU_IDS[number])
      })
    }
    return menuItems.filter((item) => {
      if (item.type === 'divider') return true
      if (item.developerOnly && experienceLevel !== 'developer') return false
      return item.modes?.includes(mode)
    })
  }, [menuItems, mode, isBeginnerSidebar, experienceLevel])
  
  const handlePageChange = useCallback((pageId: string) => {
    try {
      localStorage.removeItem(NEW_BADGE_KEY + pageId)
      setNewBadges(prev => ({ ...prev, [pageId]: false }))
    } catch { /* ignore */ }
    setCurrentPage(pageId)
  }, [setCurrentPage])
  
  const handleThemeChange = useCallback((newTheme: Theme) => {
    setTheme(newTheme)
  }, [setTheme])

  return (
    <>
      {mobileOpen && <div className="fixed inset-0 bg-black/50 z-30 md:hidden" aria-hidden onClick={onClose} />}
      <div
        className={`w-64 bg-slate-200 dark:bg-slate-800 border-r border-slate-300 dark:border-slate-700 flex flex-col h-screen shadow-2xl
          ${mobileOpen ? 'flex fixed inset-y-0 left-0 z-40' : 'hidden'} md:flex md:relative md:inset-auto`}
      >
      {/* Logo + Mobile Schließen */}
      <div className="p-4 border-b border-slate-300 dark:border-slate-700">
        <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="w-10 h-10 bg-gradient-to-br from-sky-400 to-sky-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">π</span>
          </div>
          <div className="min-w-0">
            <h1 className="text-xl font-bold text-slate-900 dark:text-white truncate">{appTitle}</h1>
            <div
              className="mt-1.5 mb-1"
              role="group"
              aria-label={t('sidebar.language.aria')}
            >
              <div className="inline-flex rounded-lg border border-slate-300 dark:border-slate-600 overflow-hidden shadow-sm">
                <button
                  type="button"
                  onClick={() => setAppLocale('de')}
                  aria-pressed={uiLang === 'de'}
                  title={t('settings.language.de')}
                  className={`flex items-center justify-center gap-1 px-2.5 py-1 text-sm leading-none transition-colors ${
                    uiLang === 'de'
                      ? 'bg-sky-600 text-white'
                      : 'bg-slate-100 dark:bg-slate-700/80 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-600'
                  }`}
                >
                  <span className="text-base" aria-hidden>
                    🇩🇪
                  </span>
                  <span className="text-[11px] font-semibold">{t('sidebar.language.deShort')}</span>
                </button>
                <button
                  type="button"
                  onClick={() => setAppLocale('en')}
                  aria-pressed={uiLang === 'en'}
                  title={t('settings.language.en')}
                  className={`flex items-center justify-center gap-1 px-2.5 py-1 text-sm leading-none border-l border-slate-300 dark:border-slate-600 transition-colors ${
                    uiLang === 'en'
                      ? 'bg-sky-600 text-white'
                      : 'bg-slate-100 dark:bg-slate-700/80 text-slate-700 dark:text-slate-200 hover:bg-slate-200 dark:hover:bg-slate-600'
                  }`}
                >
                  <span className="text-base" aria-hidden>
                    🇬🇧
                  </span>
                  <span className="text-[11px] font-semibold">{t('sidebar.language.enShort')}</span>
                </button>
              </div>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">v{version}</p>
          </div>
        </div>
        {mobileOpen && onClose && (
          <button type="button" onClick={onClose} className="md:hidden p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700" aria-label={t('sidebar.closeMenu')}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        )}
        </div>
        {/* Phase 5: Tabs nur für Fortgeschrittene/Entwickler – Einsteiger sehen nur die 6 Hauptpunkte. */}
        {!isBeginnerSidebar && (
          <div className="flex gap-0.5 p-0.5 bg-slate-300/50 dark:bg-slate-800/50 rounded-lg" role="tablist" aria-label={t('sidebar.modeTabs.aria')}>
            {([
              { id: 'basic' as const, label: t('sidebar.modeTabs.basic'), title: t('sidebar.modeTabs.basicTitle'), appIcon: 'dashboard' as const },
              { id: 'advanced' as const, label: t('sidebar.modeTabs.advanced'), title: t('sidebar.modeTabs.advancedTitle'), appIcon: 'advanced' as const },
              { id: 'diagnose' as const, label: t('sidebar.modeTabs.diagnose'), title: t('sidebar.modeTabs.diagnoseTitle'), appIcon: 'diagnose' as const },
            ]).map(({ id, label, title, appIcon }) => (
              <button
                key={id}
                role="tab"
                aria-selected={mode === id}
                title={title}
                onClick={() => setMode(id)}
                className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded text-xs font-medium transition-colors duration-150 ${
                  mode === id ? 'bg-sky-600 text-white shadow' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
              >
                <AppIcon name={appIcon} category="navigation" size={16} />
                {label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Menu */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {filteredItems.map((item, index) => {
          if (item.type === 'divider') {
            return <div key={`divider-${index}`} className="h-px bg-slate-300 dark:bg-slate-700 my-1" />
          }

          const isPiConfigDisabled = item.id === 'raspberry-pi-config' && !isRaspberryPi
          const Icon = item.icon
          const appIconName = item.appIcon
          const isActive = currentPage === item.id
          const pageRisk = getPageRisk(item.id, t)

          return (
            <button
              key={item.id}
              onClick={() => !isPiConfigDisabled && handlePageChange(item.id)}
              disabled={isPiConfigDisabled}
              title={isPiConfigDisabled ? t('sidebar.raspberryOnly') : undefined}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors duration-150 ${
                isPiConfigDisabled
                  ? 'text-slate-400 dark:text-slate-500 cursor-not-allowed opacity-60'
                  : isActive
                    ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/50'
                    : 'text-slate-600 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              {appIconName ? (
                <AppIcon name={appIconName} category="navigation" size={24} className={isActive ? 'opacity-90' : ''} />
              ) : (
                Icon && <Icon size={18} />
              )}
              <span className="font-medium text-sm flex-1 truncate">{item.labelKey ? t(item.labelKey) : ''}</span>
              {pageRisk && (
                <RiskLevelBadge level={pageRisk.level} showLabel={false} title={pageRisk.label} className={isActive ? 'border-white/50' : ''} />
              )}
              {newBadges[item.id] && (
                <span className="px-1.5 py-0.5 text-[10px] font-bold bg-sky-500 text-white rounded animate-pulse">{t('sidebar.newBadge')}</span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-slate-300 dark:border-slate-700 space-y-2">
        <div className="text-xs px-2">
          <p className="font-semibold mb-1.5 text-slate-600 dark:text-slate-300">{t('sidebar.systemStatus')}</p>
          <p className="text-green-600 dark:text-green-400 font-semibold flex items-center gap-1.5">
            <AppIcon name="ok" category="status" size={16} statusColor="ok" />
            {t('sidebar.ready')}
          </p>
          <div className="mt-2.5 pt-2.5 border-t border-slate-300 dark:border-slate-700 space-y-2">
            <p className="text-slate-500 dark:text-slate-400 text-xs mb-2">{t('sidebar.copyright')}</p>
            {/* Theme Toggle */}
            <div className="flex gap-1 p-1 bg-slate-300/50 dark:bg-slate-800/50 rounded-lg">
              <button
                onClick={() => handleThemeChange('light')}
                className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded text-xs transition-colors duration-150 ${
                  theme === 'light' ? 'bg-sky-600 text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
                title={t('sidebar.theme.light')}
              >
                <Sun size={14} />
              </button>
              <button
                onClick={() => handleThemeChange('dark')}
                className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded text-xs transition-colors duration-150 ${
                  theme === 'dark' ? 'bg-sky-600 text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
                title={t('sidebar.theme.dark')}
              >
                <Moon size={14} />
              </button>
              <button
                onClick={() => handleThemeChange('system')}
                className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded text-xs transition-colors duration-150 ${
                  theme === 'system' ? 'bg-sky-600 text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
                title={t('sidebar.theme.system')}
              >
                <Monitor size={14} />
              </button>
            </div>
          </div>
        </div>
        {/* Buttons gleich breit - beide auf derselben Ebene */}
        <div className="space-y-2">
          <button
            onClick={() => handlePageChange('documentation')}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-sky-600/60 hover:bg-sky-600/80 text-sky-100 rounded-lg transition-colors duration-150 text-xs font-medium"
          >
            <AppIcon name="documentation" category="navigation" size={24} />
            <span>{t('sidebar.footerDocs')}</span>
          </button>
          <button
            type="button"
            onClick={() => {
              const w = typeof window !== 'undefined' ? window : null
              const tauri = w && (w as any).__TAURI__
              if (tauri?.core?.invoke) {
                (tauri.core.invoke as (cmd: string) => Promise<unknown>)('exit_app').catch(() => {})
              } else {
                w?.close()
                setTimeout(() => {
                  if (typeof document !== 'undefined' && document.visibilityState === 'visible') {
                    toast(t('sidebar.closeWindowHint'), { duration: 4000 })
                  }
                }, 200)
              }
            }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-red-600/50 hover:bg-red-600/70 text-red-100 rounded-lg transition-colors duration-150 text-xs font-medium"
          >
            <LogOut size={16} />
            <span>{t('sidebar.quit')}</span>
          </button>
        </div>
      </div>
    </div>
    </>
  )
}

SidebarComponent.displayName = 'Sidebar'

const Sidebar = React.memo(SidebarComponent)

export default Sidebar
