import React, { useEffect, useState, useMemo, useCallback } from 'react'
import { fetchApi } from '../api'
import { usePlatform } from '../context/PlatformContext'
import {
  LayoutDashboard,
  Shield,
  Users,
  Code,
  Globe,
  Mail,
  HardDrive,
  Home,
  Music,
  Zap,
  LogOut,
  Settings,
  BookOpen,
  Activity,
  Database,
  Cpu,
  Moon,
  Sun,
  Monitor,
  Scan,
  Tv,
} from 'lucide-react'

type Theme = 'light' | 'dark' | 'system'

interface SidebarProps {
  currentPage: string
  setCurrentPage: (page: any) => void
  theme: Theme
  setTheme: (theme: Theme) => void
  isRaspberryPi?: boolean
}

const NEW_BADGE_KEY = 'pi-installer-new-'

const SidebarComponent: React.FC<SidebarProps> = ({ currentPage, setCurrentPage, theme, setTheme, isRaspberryPi = false }) => {
  const { systemLabel } = usePlatform()
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
    // Logisch sortiert: Übersicht → Einrichtung → System → Dienste → Wartung → Pi (optional)
    const items: Array<{ id?: string; type?: string; label?: string; icon?: any }> = [
      { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { id: 'wizard', label: 'Assistent', icon: Zap },
      { id: 'presets', label: 'Voreinstellungen', icon: Settings },
      { type: 'divider' },
      { id: 'settings', label: 'Einstellungen', icon: Settings },
      { id: 'security', label: 'Sicherheit', icon: Shield },
      { id: 'users', label: 'Benutzer', icon: Users },
      { type: 'divider' },
      { id: 'devenv', label: 'Dev-Umgebung', icon: Code },
      { id: 'webserver', label: 'Webserver', icon: Globe },
      { id: 'mailserver', label: 'Mailserver', icon: Mail },
      { id: 'nas', label: 'NAS', icon: HardDrive },
      { id: 'homeautomation', label: 'Hausautomatisierung', icon: Home },
      { id: 'musicbox', label: 'Musikbox', icon: Music },
      { id: 'kino-streaming', label: 'Kino / Streaming', icon: Tv },
      { id: 'learning', label: 'Lerncomputer', icon: BookOpen },
      { type: 'divider' },
      { id: 'monitoring', label: 'Monitoring', icon: Activity },
      { id: 'backup', label: 'Backup & Restore', icon: Database },
      { id: 'control-center', label: 'Control Center', icon: Settings },
      { id: 'periphery-scan', label: 'Peripherie-Scan (Assimilation)', icon: Scan },
    ]
    if (isRaspberryPi) {
      items.splice(items.length - 1, 0, { id: 'raspberry-pi-config', label: 'Raspberry Pi Config', icon: Cpu })
    }
    return items
  }, [isRaspberryPi])
  
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
    <div className="w-64 bg-slate-200 dark:bg-slate-800 border-r border-slate-300 dark:border-slate-700 flex flex-col h-screen shadow-2xl">
      {/* Logo */}
      <div className="p-6 border-b border-slate-300 dark:border-slate-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-sky-400 to-sky-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-lg">π</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-white">{isRaspberryPi ? 'PI-Installer' : systemLabel}</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">v{version}</p>
          </div>
        </div>
      </div>

      {/* Menu */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {menuItems.map((item, index) => {
          if (item.type === 'divider') {
            return <div key={`divider-${index}`} className="h-px bg-slate-300 dark:bg-slate-700 my-1" />
          }

          const isPiConfigDisabled = item.id === 'raspberry-pi-config' && !isRaspberryPi
          const Icon = item.icon
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
              <Icon size={18} />
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
          <p className="text-green-600 dark:text-green-400 font-semibold">🟢 Bereit</p>
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
            <BookOpen size={14} />
            <span>Dokumentation</span>
          </button>
          <button className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-red-600/50 hover:bg-red-600/70 text-red-100 rounded-lg transition-colors duration-150 text-xs font-medium">
            <LogOut size={16} />
            <span>Beenden</span>
          </button>
        </div>
      </div>
    </div>
  )
}

SidebarComponent.displayName = 'Sidebar'

const Sidebar = React.memo(SidebarComponent)

export default Sidebar
