import React, { useEffect, useState, useMemo, useCallback } from 'react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'
import { usePlatform } from '../context/PlatformContext'
import { useUIMode, type UIMode } from '../context/UIModeContext'
import AppIcon from './AppIcon'
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

interface SidebarProps {
  currentPage: string
  setCurrentPage: (page: any) => void
  theme: Theme
  setTheme: (theme: Theme) => void
  isRaspberryPi?: boolean
  freenoveDetected?: boolean
  mobileOpen?: boolean
  onClose?: () => void
}

const NEW_BADGE_KEY = 'pi-installer-new-'

const SidebarComponent: React.FC<SidebarProps> = ({ currentPage, setCurrentPage, theme, setTheme, isRaspberryPi = false, freenoveDetected = false, mobileOpen = false, onClose }) => {
  const { appTitle } = usePlatform()
  const { mode, setMode } = useUIMode()
  const [version, setVersion] = useState<string>('…')
  const [newBadges, setNewBadges] = useState<Record<string, boolean>>({})

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

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetchApi('/api/version')
        if (!res.ok) return
        const data = await res.json()
        if (!cancelled && data?.version) setVersion(String(data.version))
      } catch {
        // ignore
      }
    })()
    return () => {
      cancelled = true
    }
  }, [])

  const menuItems = useMemo(() => {
    type Item = { id?: string; type?: string; label?: string; icon?: any; appIcon?: string; modes?: UIMode[] }
    const items: Item[] = [
      { id: 'dashboard', label: 'Dashboard', appIcon: 'dashboard', modes: ['basic'] },
      { id: 'remote', label: 'Remote Companion', icon: Smartphone, modes: ['advanced'] },
      { id: 'app-store', label: 'App Store', appIcon: 'app-store', modes: ['basic'] },
      ...(freenoveDetected ? [{ id: 'dsi-radio-settings', label: 'DSI-Radio Einstellungen', icon: Radio, modes: ['basic', 'advanced'] as UIMode[] }] : []),
      { id: 'wizard', label: 'Assistent', appIcon: 'wizard', modes: ['basic'] },
      { id: 'presets', label: 'Voreinstellungen', icon: Settings, modes: ['basic'] },
      { type: 'divider' },
      { id: 'settings', label: 'Einstellungen', appIcon: 'settings', modes: ['basic', 'diagnose'] },
      { id: 'security', label: 'Sicherheit', icon: Shield, modes: ['basic'] },
      { id: 'users', label: 'Benutzer', icon: Users, modes: ['basic'] },
      { type: 'divider' },
      { id: 'devenv', label: 'Dev-Umgebung', icon: Code, modes: ['advanced'] },
      { id: 'webserver', label: 'Webserver', icon: Globe, modes: ['advanced'] },
      { id: 'mailserver', label: 'Mailserver', icon: Mail, modes: ['advanced'] },
      { id: 'nas', label: 'NAS', icon: HardDrive, modes: ['advanced'] },
      { id: 'homeautomation', label: 'Hausautomatisierung', icon: Home, modes: ['advanced'] },
      { id: 'musicbox', label: 'Musikbox', icon: Music, modes: ['advanced'] },
      { id: 'kino-streaming', label: 'Kino / Streaming', icon: Tv, modes: ['advanced'] },
      { id: 'learning', label: 'Lerncomputer', icon: BookOpen, modes: ['advanced'] },
      { type: 'divider' },
      { id: 'monitoring', label: 'Monitoring', appIcon: 'monitoring', modes: ['advanced', 'diagnose'] },
      { id: 'backup', label: 'Backup & Restore', appIcon: 'backup', modes: ['basic'] },
      { id: 'pi-installer-update', label: 'PI-Installer Update', icon: Upload, modes: ['basic'] },
      { id: 'control-center', label: 'Control Center', appIcon: 'control-center', modes: ['advanced'] },
      { id: 'periphery-scan', label: 'Peripherie-Scan', appIcon: 'periphery-scan', modes: ['advanced', 'diagnose'] },
    ]
    if (isRaspberryPi) {
      items.splice(items.length - 1, 0, { id: 'raspberry-pi-config', label: 'Raspberry Pi Config', icon: Cpu, modes: ['advanced'] })
    }
    return items
  }, [isRaspberryPi, freenoveDetected])

  const filteredItems = useMemo(() => {
    return menuItems.filter((item) => {
      if (item.type === 'divider') return true
      return item.modes?.includes(mode)
    })
  }, [menuItems, mode])
  
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
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">{appTitle}</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">v{version}</p>
          </div>
        </div>
        {mobileOpen && onClose && (
          <button type="button" onClick={onClose} className="md:hidden p-2 rounded-lg text-slate-600 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700" aria-label="Menü schließen">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        )}
        </div>
        {/* Phase 5: Grundlagen / Erweitert / Diagnose */}
        <div className="flex gap-0.5 p-0.5 bg-slate-300/50 dark:bg-slate-800/50 rounded-lg" role="tablist" aria-label="Ansichtsmodus">
          {([
            { id: 'basic' as const, label: 'Grundlagen', title: 'Häufig genutzte Funktionen für Einsteiger', appIcon: 'dashboard' as const },
            { id: 'advanced' as const, label: 'Erweitert', title: 'Technische Einstellungen für erfahrene Nutzer', appIcon: 'advanced' as const },
            { id: 'diagnose' as const, label: 'Diagnose', title: 'Diagnosewerkzeuge zur Fehlersuche', appIcon: 'diagnose' as const },
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

          return (
            <button
              key={item.id}
              onClick={() => !isPiConfigDisabled && handlePageChange(item.id)}
              disabled={isPiConfigDisabled}
              title={isPiConfigDisabled ? 'Nur auf Raspberry Pi verfügbar' : undefined}
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
              <span className="font-medium text-sm">{item.label}</span>
              {newBadges[item.id] && (
                <span className="ml-auto px-1.5 py-0.5 text-[10px] font-bold bg-sky-500 text-white rounded animate-pulse">Neu</span>
              )}
            </button>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-slate-300 dark:border-slate-700 space-y-2">
        <div className="text-xs px-2">
          <p className="font-semibold mb-1.5 text-slate-600 dark:text-slate-300">System Status</p>
          <p className="text-green-600 dark:text-green-400 font-semibold flex items-center gap-1.5">
            <AppIcon name="ok" category="status" size={16} statusColor="ok" />
            Bereit
          </p>
          <div className="mt-2.5 pt-2.5 border-t border-slate-300 dark:border-slate-700 space-y-2">
            <p className="text-slate-500 dark:text-slate-400 text-xs mb-2">© 01.2026 by Volker Glienke</p>
            {/* Theme Toggle */}
            <div className="flex gap-1 p-1 bg-slate-300/50 dark:bg-slate-800/50 rounded-lg">
              <button
                onClick={() => handleThemeChange('light')}
                className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded text-xs transition-colors duration-150 ${
                  theme === 'light' ? 'bg-sky-600 text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
                title="Hell"
              >
                <Sun size={14} />
              </button>
              <button
                onClick={() => handleThemeChange('dark')}
                className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded text-xs transition-colors duration-150 ${
                  theme === 'dark' ? 'bg-sky-600 text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
                title="Dunkel"
              >
                <Moon size={14} />
              </button>
              <button
                onClick={() => handleThemeChange('system')}
                className={`flex-1 flex items-center justify-center gap-1 px-2 py-1.5 rounded text-xs transition-colors duration-150 ${
                  theme === 'system' ? 'bg-sky-600 text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200'
                }`}
                title="System"
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
            <span>Dokumentation</span>
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
                    toast('Bitte Fenster oder Tab manuell schließen (Strg+W).', { duration: 4000 })
                  }
                }, 200)
              }
            }}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-red-600/50 hover:bg-red-600/70 text-red-100 rounded-lg transition-colors duration-150 text-xs font-medium"
          >
            <LogOut size={16} />
            <span>Beenden</span>
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
