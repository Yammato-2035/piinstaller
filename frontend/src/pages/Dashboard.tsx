import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import toast from 'react-hot-toast'
import { fetchApi, getApiBase } from '../api'
import { usePlatform } from '../context/PlatformContext'
import { useUIMode } from '../context/UIModeContext'
import AppIcon from '../components/AppIcon'
import i18n from '../i18n'
import { 
  Cpu, 
  HardDrive, 
  Zap, 
  Clock,
  Shield,
  Users,
  Code,
  Globe,
  Mail,
  Home,
  Music,
  Settings,
  BookOpen,
  Activity,
  Database,
  Thermometer,
  Wind,
  Monitor,
  Package,
} from 'lucide-react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { motion } from 'framer-motion'
import { SkeletonCard as SharedSkeletonCard } from '../components/Skeleton'
import HelpTooltip from '../components/HelpTooltip'

interface DashboardProps {
  systemInfo: any
  backendError?: boolean
  backendErrorReason?: 'timeout' | 'connection' | 'other' | null
  onRetryBackend?: () => void
  setCurrentPage?: (page: string) => void
  experienceLevel?: 'beginner' | 'advanced' | 'developer'
}

/** Tooltip-Text für Sensoren: was es ist, wo es sitzt, Normalwert lt. Hersteller/typisch. */
function getSensorTooltip(s: { name?: string; zone?: string }): string {
  const name = (s.name || '').toLowerCase()
  const zone = (s.zone || '').toLowerCase()
  if (zone === 'vcgencmd' || (name === 'cpu' && zone.includes('vcgencmd'))) {
    return i18n.t('dashboard.tooltip.sensor.vcgencmd')
  }
  if (name.includes('x86_pkg_temp') || name.includes('cpu package')) {
    return i18n.t('dashboard.tooltip.sensor.cpuPackage')
  }
  if (name.includes('nvme')) {
    return i18n.t('dashboard.tooltip.sensor.nvme')
  }
  if (name.includes('gpu') || name.includes('radeon') || name.includes('nvidia') || name.includes('amd')) {
    return i18n.t('dashboard.tooltip.sensor.gpu')
  }
  if (name.includes('acpitz') || name.includes('igpu') || name.includes('apu')) {
    return i18n.t('dashboard.tooltip.sensor.apu')
  }
  if (zone.startsWith('thermal_zone')) {
    return i18n.t('dashboard.tooltip.sensor.thermalZone', { name: s.name || zone, zone })
  }
  return i18n.t('dashboard.tooltip.sensor.generic', {
    name: s.name || i18n.t('dashboard.tooltip.sensor.fallbackName'),
    zone: s.zone || i18n.t('dashboard.tooltip.sensor.fallbackZone'),
  })
}

/** Tooltip für Laufwerke. */
function getDiskTooltip(d: { label?: string; mountpoint?: string; device?: string }): string {
  const where = d.mountpoint || d.device || i18n.t('dashboard.tooltip.disk.unknown')
  return i18n.t('dashboard.tooltip.disk.body', { where })
}

/** Tooltip für Lüfter. */
function getFanTooltip(_f: { name?: string }): string {
  return i18n.t('dashboard.tooltip.fan')
}

/** Tooltip für Displays. */
function getDisplayTooltip(d: { output?: string; mode?: string }): string {
  return i18n.t('dashboard.tooltip.display', {
    output: d.output || i18n.t('dashboard.tooltip.display.fallbackOutput'),
    mode: d.mode || i18n.t('dashboard.tooltip.display.dash'),
  })
}

// StatCard außerhalb der Komponente definieren, um Re-Renders zu vermeiden
const StatCard = React.memo(({ icon: Icon, label, value, unit = '', trend }: any) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.3 }}
      layout={false}
      className="card bg-gradient-to-br from-slate-800/60 to-slate-900/60 backdrop-blur-xl"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-slate-400 text-sm font-medium mb-1">{label}</p>
          <div className="flex items-baseline gap-2">
            <p className="text-3xl font-bold text-sky-400">
              {value}{unit}
            </p>
            {trend && (
              <span className={`text-xs ${trend > 0 ? 'text-red-400' : 'text-green-400'}`}>
                {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}%
              </span>
            )}
          </div>
        </div>
        <div className="p-3 bg-sky-600/20 rounded-lg backdrop-blur-sm">
          <Icon className="text-sky-500" size={32} />
        </div>
      </div>
    </motion.div>
  )
})

type DashboardSection = 'overview' | 'charts' | 'hardware'

const Dashboard: React.FC<DashboardProps> = ({ systemInfo, backendError, backendErrorReason, onRetryBackend, setCurrentPage, experienceLevel }) => {
  const { t } = useTranslation()
  const { pageSubtitleLabel } = usePlatform()
  const { mode } = useUIMode()
  const [dashboardSection, setDashboardSection] = useState<DashboardSection>('overview')
  const [stats, setStats] = useState<any>(null)
  const [securityConfig, setSecurityConfig] = useState<any>(null)
  const [historyData, setHistoryData] = useState<any[]>([])
  const [updatesData, setUpdatesData] = useState<{ total: number; categories?: Record<string, number>; updates?: { package: string; version: string; category: string }[] } | null>(null)
  const [updatesModalOpen, setUpdatesModalOpen] = useState(false)
  const [updateTerminalLoading, setUpdateTerminalLoading] = useState(false)
  const [updateTerminalError, setUpdateTerminalError] = useState<{ message?: string; copyable_command?: string } | null>(null)
  const [servicesStatus, setServicesStatus] = useState<{ dev?: { installed_count: number; total_parts: number; basic_ok: boolean }; webserver?: { running: boolean; reachable: boolean }; musicbox?: { installed: boolean; basic_ok: boolean } } | null>(null)
  const loading = !systemInfo && !backendError

  const isBeginnerMode = mode === 'basic'
  const isBeginnerExperience = experienceLevel === 'beginner'
  const isBeginnerView = isBeginnerMode && isBeginnerExperience

  const handleTaskNavigate = (page: string) => {
    if (!setCurrentPage) return
    setCurrentPage(page)
  }

  const loadServicesStatus = async () => {
    try {
      const response = await fetchApi('/api/dashboard/services-status')
      const data = await response.json()
      if (data && !data.error) setServicesStatus(data)
    } catch (e) {
      console.error('Services-Status:', e)
    }
  }

  useEffect(() => {
    if (systemInfo) {
      setStats(systemInfo)
      setHistoryData(prev => {
        const newData = {
          time: new Date().toLocaleTimeString(),
          cpu: systemInfo.cpu?.usage || 0,
          memory: systemInfo.memory?.percent || 0,
        }
        return [...prev, newData].slice(-20)
      })
    }
    loadSecurityConfig()
    loadUpdates()
    loadServicesStatus()
    const pollInterval = systemInfo?.is_raspberry_pi ? 30000 : 5000
    const interval = setInterval(async () => {
      try {
        const response = await fetchApi('/api/system-info?light=1')
        const data = await response.json()
        if (data) {
          setStats(prev => {
            const next = !prev ? data : {
              ...prev,
              cpu: { ...prev.cpu, ...data.cpu, usage: data.cpu?.usage, temperature: data.cpu?.temperature ?? prev.cpu?.temperature },
              memory: data.memory ?? prev.memory,
              disk: data.disk ?? prev.disk,
              uptime: data.uptime ?? prev.uptime,
              cpu_name: data.cpu_name ?? prev.cpu_name,
              cpu_summary: data.cpu_summary ?? prev.cpu_summary,
            }
            return next
          })
          setHistoryData(prev => {
            const newData = {
              time: new Date().toLocaleTimeString(),
              cpu: data.cpu?.usage || 0,
              memory: data.memory?.percent || 0,
            }
            return [...prev, newData].slice(-20)
          })
        }
      } catch (error) {
        console.error('Fehler beim Aktualisieren:', error)
      }
    }, pollInterval)
    
    return () => clearInterval(interval)
  }, [systemInfo])

  const loadSecurityConfig = async () => {
    try {
      const response = await fetchApi('/api/system/security-config')
      const data = await response.json()
      if (data.config) {
        setSecurityConfig(data.config)
      }
    } catch (error) {
      console.error('Fehler beim Laden der Security-Config:', error)
    }
  }

  const loadUpdates = async () => {
    try {
      const response = await fetchApi('/api/system/updates')
      const data = await response.json()
      if (data.status === 'success' && data.total !== undefined) {
        setUpdatesData({
          total: data.total,
          categories: data.categories,
          updates: data.updates || [],
        })
      }
    } catch (error) {
      console.error('Fehler beim Laden der Updates:', error)
    }
  }

  const runUpdateInTerminal = async () => {
    setUpdateTerminalError(null)
    setUpdateTerminalLoading(true)
    try {
      const response = await fetchApi('/api/system/run-update-in-terminal', { method: 'POST' })
      const data = await response.json()
      if (data.status === 'success') {
        toast.success(data.message || t('dashboard.toast.terminalOpened'))
      } else {
        setUpdateTerminalError({ message: data.message, copyable_command: data.copyable_command })
        toast.error(data.message || t('dashboard.toast.terminalFailed'))
      }
    } catch (e) {
      setUpdateTerminalError({ message: t('dashboard.toast.terminalOpenError'), copyable_command: 'sudo apt update && sudo apt upgrade' })
      toast.error(t('dashboard.toast.terminalOpenError'))
    } finally {
      setUpdateTerminalLoading(false)
    }
  }
  const copyUpdateCommand = () => {
    const cmd = updateTerminalError?.copyable_command || 'sudo apt update && sudo apt upgrade'
    navigator.clipboard?.writeText(cmd).then(() => toast.success(t('dashboard.toast.commandCopied'))).catch(() => {})
  }

  const SECURITY_TOTAL = 5 // Firewall, Fail2Ban, Auto-Updates, SSH-Härtung, Audit-Logging

  /** UFW als aktiv werten, wenn active: true ODER Status-String "active"/"aktiv" enthält (wie auf Sicherheits-Seite). */
  const effectiveUfwActive = (() => {
    if (!securityConfig?.ufw) return false
    if (securityConfig.ufw.active) return true
    const status = (securityConfig.ufw.status || '').toLowerCase()
    if (!securityConfig.ufw.installed) return false
    return status.includes('active') || status.includes('aktiv') || status.includes('enabled=yes') || status.includes('via systemctl') || status.includes('wahrscheinlich')
  })()

  const getSecurityStatus = () => {
    if (!securityConfig) return 'inactive'
    const activeCount =
      (effectiveUfwActive ? 1 : 0) +
      (securityConfig.fail2ban?.active ? 1 : 0) +
      (securityConfig.auto_updates?.enabled ? 1 : 0) +
      (securityConfig.ssh_hardening?.enabled ? 1 : 0) +
      (securityConfig.audit_logging?.enabled ? 1 : 0)
    return activeCount / SECURITY_TOTAL >= 0.5 ? 'active' : 'inactive'
  }

  const getSecurityStatusText = () => {
    if (!securityConfig) return t('dashboard.security.notConfigured')
    const activeCount =
      (effectiveUfwActive ? 1 : 0) +
      (securityConfig.fail2ban?.active ? 1 : 0) +
      (securityConfig.auto_updates?.enabled ? 1 : 0) +
      (securityConfig.ssh_hardening?.enabled ? 1 : 0) +
      (securityConfig.audit_logging?.enabled ? 1 : 0)
    if (activeCount === 0) return t('dashboard.security.notConfigured')
    if (activeCount === SECURITY_TOTAL) return t('dashboard.security.fullyConfigured')
    return t('dashboard.security.partial', { count: activeCount, total: SECURITY_TOTAL })
  }

  const StatusItem = ({ label, status, value, tooltip }: any) => (
    <div className="flex items-center justify-between p-4 border-b border-slate-700 last:border-0">
      <div className="flex items-center gap-3">
        <div className="relative group">
          {status === 'active' ? (
            <AppIcon name="ok" category="status" size={20} statusColor="ok" />
          ) : (
            <AppIcon name="warning" category="status" size={20} statusColor="warning" />
          )}
          {tooltip && (
            <div className="pointer-events-none absolute left-1/2 -translate-x-1/2 -top-2 -translate-y-full opacity-0 group-hover:opacity-100 transition-opacity z-20">
              <div className="max-w-xs whitespace-pre-line text-xs text-slate-100 bg-slate-900/95 border border-slate-700 rounded-lg px-3 py-2 shadow-xl">
                {tooltip}
              </div>
              <div className="mx-auto w-2 h-2 bg-slate-900/95 border border-slate-700 rotate-45 -mt-1" />
            </div>
          )}
        </div>
        <span className="font-medium">{label}</span>
      </div>
      <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
        status === 'active' 
          ? 'bg-emerald-900 text-emerald-200' 
          : 'bg-yellow-900 text-yellow-200'
      }`}>
        {value}
      </span>
    </div>
  )

  const diskData = stats ? [
    { name: t('dashboard.chart.disk.used'), value: stats.disk?.percent || 0, color: '#ef4444' },
    { name: t('dashboard.chart.disk.free'), value: 100 - (stats.disk?.percent || 0), color: '#10b981' },
  ] : []

  const needsAction = !!(updatesData && updatesData.total > 0) || getSecurityStatus() === 'inactive'
  const statusLabel = backendError ? t('dashboard.status.backendFailed') : needsAction ? t('dashboard.status.actionNeeded') : t('dashboard.status.allOk')
  const statusColor = backendError ? 'red' : needsAction ? 'yellow' : 'green'

  const cpuPercent = stats?.cpu?.usage ?? 0
  const memPercent = stats?.memory?.percent ?? 0
  const diskPercent = stats?.disk?.percent ?? 0
  const resourceLevel = (p: number) => (p >= 90 ? 'red' : p >= 70 ? 'yellow' : 'green')

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="space-y-8 page-transition"
    >
      {/* Beginner-First Task Cards (Beginner-View: Aufgaben statt Modul-Liste im Fokus) */}
      {isBeginnerView && setCurrentPage && !backendError && (
        <section className="grid gap-4 md:grid-cols-3">
          <button
            type="button"
            onClick={() => handleTaskNavigate('wizard')}
            className="flex items-start gap-3 p-4 rounded-2xl bg-sky-600/20 hover:bg-sky-600/30 border border-sky-500/40 transition-colors text-left"
          >
            <AppIcon name="installation" category="navigation" size={32} className="mt-1" />
            <div>
              <p className="text-sm font-semibold text-sky-100">{t('firstRun.firstStep.wizard.title')}</p>
              <p className="text-xs text-slate-200/80">{t('firstRun.firstStep.wizard.desc')}</p>
            </div>
          </button>
          <button
            type="button"
            onClick={() => handleTaskNavigate('app-store')}
            className="flex items-start gap-3 p-4 rounded-2xl bg-emerald-600/15 hover:bg-emerald-600/25 border border-emerald-500/40 transition-colors text-left"
          >
            <AppIcon name="app-store" category="navigation" size={32} className="mt-1" />
            <div>
              <p className="text-sm font-semibold text-emerald-100">{t('firstRun.firstStep.appStore.title')}</p>
              <p className="text-xs text-slate-200/80">{t('firstRun.firstStep.appStore.desc')}</p>
            </div>
          </button>
          <button
            type="button"
            onClick={() => handleTaskNavigate('backup')}
            className="flex items-start gap-3 p-4 rounded-2xl bg-indigo-600/20 hover:bg-indigo-600/30 border border-indigo-500/40 transition-colors text-left"
          >
            <AppIcon name="backup" category="navigation" size={32} className="mt-1" />
            <div>
              <p className="text-sm font-semibold text-indigo-100">{t('firstRun.firstStep.backup.title')}</p>
              <p className="text-xs text-slate-200/80">{t('firstRun.firstStep.backup.desc')}</p>
            </div>
          </button>
          <button
            type="button"
            onClick={() => handleTaskNavigate('monitoring')}
            className="flex items-start gap-3 p-4 rounded-2xl bg-amber-600/15 hover:bg-amber-600/25 border border-amber-500/40 transition-colors text-left"
          >
            <AppIcon name="monitoring" category="navigation" size={32} className="mt-1" />
            <div>
              <p className="text-sm font-semibold text-amber-100">{t('firstRun.firstStep.monitoring.title')}</p>
              <p className="text-xs text-slate-200/80">{t('firstRun.firstStep.monitoring.desc')}</p>
            </div>
          </button>
          <button
            type="button"
            onClick={() => handleTaskNavigate('learning')}
            className="flex items-start gap-3 p-4 rounded-2xl bg-teal-600/15 hover:bg-teal-600/25 border border-teal-500/40 transition-colors text-left"
          >
            <AppIcon name="documentation" category="navigation" size={32} className="mt-1" />
            <div>
              <p className="text-sm font-semibold text-teal-100">{t('firstRun.firstStep.learning.title')}</p>
              <p className="text-xs text-slate-200/80">{t('firstRun.firstStep.learning.desc')}</p>
            </div>
          </button>
          <button
            type="button"
            onClick={() => handleTaskNavigate('control-center')}
            className="flex items-start gap-3 p-4 rounded-2xl bg-slate-700/40 hover:bg-slate-700/60 border border-slate-500/60 transition-colors text-left"
          >
            <AppIcon name="advanced" category="navigation" size={32} className="mt-1" />
            <div>
              <p className="text-sm font-semibold text-slate-50">{t('firstRun.firstStep.controlCenter.title')}</p>
              <p className="text-xs text-slate-200/80">{t('firstRun.firstStep.controlCenter.desc')}</p>
            </div>
          </button>
        </section>
      )}

      {/* Hero: Dein Raspberry Pi läuft! (Transformationsplan 5.2) */}
      {!backendError && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-slate-600 dark:border-slate-600 bg-gradient-to-br from-slate-800/80 to-slate-900/80 dark:from-slate-800/80 dark:to-slate-900/80 p-6 sm:p-8"
        >
          <h2 className="text-2xl sm:text-3xl font-bold text-white dark:text-white mb-2">
            {t('dashboard.hero.title', {
              device: systemInfo?.is_raspberry_pi ? t('dashboard.hero.raspberryPi') : t('dashboard.hero.system'),
            })}
          </h2>
          <div className="flex flex-wrap items-center gap-4 mb-6">
            <div
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-xl font-semibold ${
                statusColor === 'green'
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                  : statusColor === 'yellow'
                    ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                    : 'bg-red-500/20 text-red-300 border border-red-500/40'
              }`}
            >
              {statusColor === 'green' && <AppIcon name="ok" category="status" size={20} statusColor="ok" />}
              {statusColor === 'yellow' && <AppIcon name="warning" category="status" size={20} statusColor="warning" />}
              {statusColor === 'red' && <AppIcon name="error" category="status" size={20} statusColor="error" />}
              {statusLabel}
            </div>
            <div className="flex items-center gap-3 text-sm text-slate-400">
              <span className="flex items-center gap-1.5">
                <span className={`w-2.5 h-2.5 rounded-full ${resourceLevel(cpuPercent) === 'green' ? 'bg-emerald-500' : resourceLevel(cpuPercent) === 'yellow' ? 'bg-amber-500' : 'bg-red-500'}`} />
                CPU {Math.round(cpuPercent)}%
              </span>
              <span className="flex items-center gap-1.5">
                <span className={`w-2.5 h-2.5 rounded-full ${resourceLevel(memPercent) === 'green' ? 'bg-emerald-500' : resourceLevel(memPercent) === 'yellow' ? 'bg-amber-500' : 'bg-red-500'}`} />
                RAM {Math.round(memPercent)}%
              </span>
              <span className="flex items-center gap-1.5">
                <span className={`w-2.5 h-2.5 rounded-full ${resourceLevel(diskPercent) === 'green' ? 'bg-emerald-500' : resourceLevel(diskPercent) === 'yellow' ? 'bg-amber-500' : 'bg-red-500'}`} />
                {t('dashboard.resource.storage')} {Math.round(diskPercent)}%
              </span>
            </div>
          </div>
          {/* Ressourcen-Management (Milestone 3): Temperatur- und Swap-Hinweise */}
          {(stats?.cpu?.temperature != null && stats.cpu.temperature >= 80) && (
            <p className="text-amber-300 text-sm mb-2">
              {t('dashboard.hint.tempHigh', { temp: stats.cpu.temperature })}
            </p>
          )}
          {(stats?.memory?.total != null && stats.memory.total < 2 * 1024 * 1024 * 1024) && (
            <p className="text-sky-300 text-sm mb-2">
              {t('dashboard.hint.lowRam')}
            </p>
          )}
          <div className="flex flex-wrap gap-3">
            {setCurrentPage && (
              <>
                <span className="inline-flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => setCurrentPage('app-store')}
                    className="inline-flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl font-medium text-sm"
                  >
                    <Package className="w-4 h-4" /> {t('dashboard.action.newApp')}
                  </button>
                  <HelpTooltip text={t('dashboard.help.appStore')} size={14} className="text-slate-400" />
                </span>
                <button
                  type="button"
                  onClick={() => setCurrentPage('backup')}
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-slate-600 hover:bg-slate-500 text-white rounded-xl font-medium text-sm"
                >
                  <Database className="w-4 h-4" /> {t('dashboard.action.createBackup')}
                </button>
              </>
            )}
            <button
              type="button"
              onClick={runUpdateInTerminal}
              disabled={updateTerminalLoading}
              className="inline-flex items-center gap-2 px-4 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl font-medium text-sm disabled:opacity-50"
            >
              <Zap className="w-4 h-4" /> {t('dashboard.action.systemUpdate')}
            </button>
          </div>
        </motion.div>
      )}

      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <AppIcon name="dashboard" category="navigation" size={32} />
            {t('dashboard.pageTitle')}
          </h1>
        </div>
        <p className="text-slate-400">{t('dashboard.pageSubtitle', { label: pageSubtitleLabel })}</p>
      </motion.div>

      {backendError && !stats && (
        <div className="card-warning flex items-start gap-3">
          <AppIcon name="error" category="status" size={24} statusColor="error" className="shrink-0 mt-0.5 opacity-90" />
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold">{t('dashboard.backendError.title')}</h3>
            <p className="text-sm mt-1 opacity-95">
              {backendErrorReason === 'timeout' && t('dashboard.backendError.timeout')}
              {backendErrorReason === 'connection' && t('dashboard.backendError.connection')}
              {(!backendErrorReason || backendErrorReason === 'other') && t('dashboard.backendError.other')}
            </p>
            <p className="text-sm mt-2 opacity-90">
              <strong>{t('dashboard.backendError.apiUrlLabel')}</strong>{' '}
              <code className="bg-black/20 px-1.5 py-0.5 rounded text-sky-200 break-all">
                {getApiBase() || t('dashboard.backendError.apiUrlDefault')}
              </code>
            </p>
            <p className="text-sm mt-2 opacity-95">
              <strong>{t('dashboard.backendError.solution')}</strong>{' '}
              {t('dashboard.backendError.solutionBody')}
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              {onRetryBackend && (
                <button
                  type="button"
                  onClick={onRetryBackend}
                  className="px-3 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-sm font-medium"
                >
                  {t('dashboard.backendError.retry')}
                </button>
              )}
              {setCurrentPage && (
                <>
                  <button
                    type="button"
                    onClick={() => setCurrentPage('settings')}
                    className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-medium"
                  >
                    {t('dashboard.backendError.settingsServerUrl')}
                  </button>
                  <button
                    type="button"
                    onClick={() => setCurrentPage('settings')}
                    className="text-sm underline hover:opacity-90"
                  >
                    {t('dashboard.backendError.settingsLogs')}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Updates verfügbar */}
      {!backendError && updatesData && updatesData.total > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl bg-sky-900/30 border border-sky-500/40 p-4 flex flex-wrap items-center justify-between gap-3"
        >
          <div className="flex items-center gap-3">
            <Zap className="text-sky-400 shrink-0" size={24} />
            <div>
              <h3 className="font-semibold text-sky-200">
                {t('dashboard.updates.available', {
                  count: updatesData.total,
                  updatesWord: updatesData.total === 1 ? t('dashboard.updates.wordOne') : t('dashboard.updates.wordMany'),
                })}
              </h3>
              {updatesData.categories && (
                <p className="text-sm text-slate-200 mt-0.5">
                  {updatesData.categories.security > 0 && <span className="text-red-300">{updatesData.categories.security} {t('dashboard.updates.category.security')}</span>}
                  {updatesData.categories.security > 0 && (updatesData.categories.critical! > 0 || updatesData.categories.necessary! > 0 || updatesData.categories.optional! > 0) && ' · '}
                  {updatesData.categories.critical! > 0 && <span className="text-amber-300">{updatesData.categories.critical} {t('dashboard.updates.category.critical')}</span>}
                  {(updatesData.categories.critical! > 0) && (updatesData.categories.necessary! > 0 || updatesData.categories.optional! > 0) && ' · '}
                  {updatesData.categories.necessary! > 0 && <span className="text-slate-100">{updatesData.categories.necessary} {t('dashboard.updates.category.necessary')}</span>}
                  {(updatesData.categories.necessary! > 0) && updatesData.categories.optional! > 0 && ' · '}
                  {updatesData.categories.optional! > 0 && <span className="text-slate-200">{updatesData.categories.optional} {t('dashboard.updates.category.optional')}</span>}
                </p>
              )}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => setUpdatesModalOpen(true)}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-sm font-medium"
            >
              {t('dashboard.updates.which')}
            </button>
            <button
              type="button"
              onClick={runUpdateInTerminal}
              disabled={updateTerminalLoading}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium disabled:opacity-50"
            >
              {updateTerminalLoading ? '…' : t('dashboard.updates.runInTerminal')}
            </button>
          </div>
        </motion.div>
      )}

      {/* System-Update im Terminal – immer anzeigen (auch wenn 0 Updates) */}
      {!backendError && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl bg-slate-800/50 border border-slate-600 p-4 flex flex-wrap items-center justify-between gap-3"
        >
          <div className="flex-1 min-w-0">
            <p className="text-slate-300 text-sm">
              <strong className="text-white">{t('dashboard.updates.aptBlock')}</strong> {t('dashboard.updates.aptHint')}
            </p>
            {updateTerminalError?.copyable_command && (
              <p className="text-slate-400 text-xs mt-2 flex items-center gap-2 flex-wrap">
                <span>{t('dashboard.updates.runCommandManually')}</span>
                <code className="bg-slate-700 px-2 py-1 rounded text-slate-200 font-mono text-xs">{updateTerminalError.copyable_command}</code>
                <button type="button" onClick={copyUpdateCommand} className="px-2 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-xs">{t('dashboard.updates.copy')}</button>
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={runUpdateInTerminal}
            disabled={updateTerminalLoading}
            className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium disabled:opacity-50 shrink-0"
          >
            {updateTerminalLoading ? '…' : t('dashboard.updates.runInTerminalShort')}
          </button>
        </motion.div>
      )}

      {/* Modal: Liste der Updates */}
      {updatesModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60" onClick={() => setUpdatesModalOpen(false)}>
          <div className="bg-slate-800 border border-slate-600 rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">{t('dashboard.updates.modalTitle')}</h3>
              <button type="button" onClick={() => setUpdatesModalOpen(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>
            <div className="p-4 overflow-y-auto flex-1">
              {updatesData?.updates?.length ? (
                <ul className="space-y-2">
                  {updatesData.updates.map((u: { package: string; version: string; category: string }, i: number) => (
                    <li key={i} className="flex items-center justify-between py-2 border-b border-slate-700 last:border-0">
                      <span className="text-white font-mono text-sm">{u.package}</span>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        u.category === 'security' ? 'bg-red-900/50 text-red-300' :
                        u.category === 'critical' ? 'bg-amber-900/50 text-amber-300' :
                        u.category === 'necessary' ? 'bg-slate-600 text-slate-200' : 'bg-slate-700 text-slate-400'
                      }`}>
                        {u.category === 'security' ? t('dashboard.updates.category.security') : u.category === 'critical' ? t('dashboard.updates.category.critical') : u.category === 'necessary' ? t('dashboard.updates.category.necessary') : t('dashboard.updates.category.optional')}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-slate-400">{t('dashboard.updates.noDetails')}</p>
              )}
              <p className="text-slate-500 text-xs mt-4">{t('dashboard.updates.installHint')} <code className="bg-slate-700 px-1 rounded">sudo apt update && sudo apt upgrade</code></p>
              <button
                type="button"
                onClick={runUpdateInTerminal}
                disabled={updateTerminalLoading}
                className="mt-3 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {updateTerminalLoading ? '…' : t('dashboard.updates.runInTerminal')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Dashboard Submenü – Bereiche ein- und ausblenden (für alle Modi sichtbar) */}
      {stats && !loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-wrap gap-2 mb-4"
        >
          <button
            type="button"
            onClick={() => setDashboardSection('overview')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${dashboardSection === 'overview' ? 'bg-sky-600 text-white' : 'bg-slate-700/70 text-slate-200 hover:text-white hover:bg-slate-600'}`}
          >
            {t('dashboard.section.overview')}
          </button>
          <button
            type="button"
            onClick={() => setDashboardSection('charts')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${dashboardSection === 'charts' ? 'bg-sky-600 text-white' : 'bg-slate-700/70 text-slate-200 hover:text-white hover:bg-slate-600'}`}
          >
            {t('dashboard.section.charts')}
          </button>
          <button
            type="button"
            onClick={() => setDashboardSection('hardware')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${dashboardSection === 'hardware' ? 'bg-sky-600 text-white' : 'bg-slate-700/70 text-slate-200 hover:text-white hover:bg-slate-600'}`}
          >
            {t('dashboard.section.hardware')}
          </button>
        </motion.div>
      )}

      {/* System Stats */}
      {loading ? (
        <div className="grid-responsive">
          <SharedSkeletonCard />
          <SharedSkeletonCard />
          <SharedSkeletonCard />
          <SharedSkeletonCard />
        </div>
      ) : stats && (
        <>
          <div className="grid-responsive">
            <StatCard
              key="cpu-usage"
              icon={Cpu}
              label={t('dashboard.stat.cpuUsage')}
              value={stats.cpu?.usage?.toFixed(1) || 0}
              unit="%"
            />
            <StatCard
              key="ram-usage"
              icon={HardDrive}
              label={t('dashboard.stat.ramUsage')}
              value={stats.memory?.percent?.toFixed(1) || 0}
              unit="%"
            />
            <StatCard
              key="disk-free"
              icon={Zap}
              label={t('dashboard.stat.diskFree')}
              value={Math.round((stats.disk?.free || 0) / 1024 / 1024 / 1024)}
              unit=" GB"
            />
            <StatCard
              key="uptime"
              icon={Clock}
              label={t('dashboard.stat.uptime')}
              value={stats.uptime || t('dashboard.stat.na')}
            />
            {stats.cpu?.temperature && (
              <StatCard
                key="cpu-temp"
                icon={Cpu}
                label={t('dashboard.stat.cpuTemp')}
                value={stats.cpu.temperature}
                unit="°C"
              />
            )}
            {stats.cpu?.fan_speed && (
              <StatCard
                key="fan-speed"
                icon={Zap}
                label={t('dashboard.stat.fanSpeed')}
                value={typeof stats.cpu.fan_speed === 'number' ? stats.cpu.fan_speed : stats.cpu.fan_speed}
                unit={typeof stats.cpu.fan_speed === 'number' ? ' RPM' : ''}
              />
            )}
          </div>

          {/* IP-Adressen & Hostname – nur in Übersicht */}
          {(dashboardSection === 'overview') && (stats.network?.ips?.length > 0 || stats.network?.hostname) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.06 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-3 flex items-center gap-2">
                <Globe className="text-slate-400" />
                {t('dashboard.network.title')}
              </h2>
              <div className="flex flex-wrap items-center gap-4 text-sm">
                {stats.network.hostname && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-0.5">{t('dashboard.network.hostname')}</span>
                    <span className="text-white font-mono">{stats.network.hostname}</span>
                  </div>
                )}
                {stats.network.ips && stats.network.ips.length > 0 && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">{t('dashboard.network.ips')}</span>
                    <div className="flex flex-wrap gap-2">
                      {stats.network.ips.map((ip: string, i: number) => (
                        <span key={i} className="font-mono text-sky-300 bg-slate-800 px-2 py-1 rounded" title={t('dashboard.network.ipHint', { ip })}>
                          {ip}
                        </span>
                      ))}
                    </div>
                    <p className="text-slate-200 text-xs mt-2 font-medium">{t('dashboard.network.reachableFromOthers', { ip: stats.network.ips[0] })}</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Systeminformationen – nur in Übersicht (in Hardware & Sensoren nicht, da redundant) */}
          {dashboardSection === 'overview' && (stats.cpu_name || (stats.motherboard && Object.keys(stats.motherboard).length > 0) || stats.os?.name || (stats.ram_info && stats.ram_info.length > 0) || (stats.hardware?.gpus && stats.hardware.gpus.length > 0)) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.08 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Cpu className="text-slate-400" />
                {t('dashboard.sysinfo.title')}
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                {stats.cpu_name && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">{t('dashboard.sysinfo.cpu')}</span>
                    <span className="text-white">{stats.cpu_name}</span>
                  </div>
                )}
                {(stats.memory?.total != null) && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">{t('dashboard.sysinfo.ramTotal')}</span>
                    <span className="text-white">{Math.round((stats.memory.total || 0) / 1024 / 1024 / 1024)} GB</span>
                  </div>
                )}
                {stats.ram_info && stats.ram_info.length > 0 && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">{t('dashboard.sysinfo.ramModules')}</span>
                    <ul className="text-white text-xs space-y-0.5">
                      {stats.ram_info.slice(0, 4).map((r: any, i: number) => (
                        <li key={i}>
                          {[r.Type, r.Size].filter(Boolean).join(' · ')}
                          {r.Speed ? ` @ ${r.Speed}` : ''}
                          {r.Manufacturer && String(r.Manufacturer).trim() && String(r.Manufacturer) !== 'Unknown' ? ` · ${r.Manufacturer}` : ''}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {stats.motherboard && Object.keys(stats.motherboard).length > 0 && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">{t('dashboard.sysinfo.motherboard')}</span>
                    <span className="text-white">
                      {[stats.motherboard.vendor, stats.motherboard.name].filter(Boolean).join(' – ') || stats.motherboard.product || '–'}
                    </span>
                  </div>
                )}
                {stats.hardware?.gpus && stats.hardware.gpus.length > 0 && (() => {
                  const integrated = stats.hardware.gpus.filter((g: any) => g.gpu_type === 'integrated')
                  const discrete = stats.hardware.gpus.filter((g: any) => g.gpu_type !== 'integrated')
                  const sorted = [...integrated, ...discrete]
                  return (
                    <div className="p-3 bg-slate-700/30 rounded-lg lg:col-span-2">
                      <span className="text-slate-400 block mb-1">{t('dashboard.sysinfo.graphics')}</span>
                      <ul className="text-white text-xs space-y-1">
                        {sorted.slice(0, 4).map((g: any, i: number) => {
                          const label = g.gpu_type === 'integrated' ? t('dashboard.sysinfo.gpu.integrated') : t('dashboard.sysinfo.gpu.discrete')
                          const name = g.display_name || g.name || g.description || t('dashboard.sysinfo.gpu.fallback')
                          const mem = g.memory_display || (g.memory_mb != null ? `${g.memory_mb} MB` : '')
                          return (
                            <li key={i}>
                              <span className="text-slate-400">{label}:</span> {name}{mem ? ` · ${mem}` : ''}
                            </li>
                          )
                        })}
                      </ul>
                    </div>
                  )
                })()}
                {stats.os?.name && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">{t('dashboard.sysinfo.os')}</span>
                    <span className="text-white">{stats.os.name}</span>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Charts Section – nur Auslastung & Grafik */}
          {dashboardSection === 'charts' && (
          <div className="grid md:grid-cols-2 gap-6">
            {/* CPU & Memory Chart */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.1 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Cpu className="text-sky-500 status-icon active" />
                {t('dashboard.chart.systemLoad')}
              </h2>
              {historyData.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={historyData}>
                    <defs>
                      <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="time" stroke="#94a3b8" fontSize={12} />
                    <YAxis stroke="#94a3b8" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(30, 41, 59, 0.95)',
                        border: '1px solid rgba(148, 163, 184, 0.2)',
                        borderRadius: '8px',
                      }}
                    />
                    <Area type="monotone" dataKey="cpu" stroke="#0ea5e9" fillOpacity={1} fill="url(#colorCpu)" name={t('dashboard.chart.series.cpu')} />
                    <Area type="monotone" dataKey="memory" stroke="#10b981" fillOpacity={1} fill="url(#colorMemory)" name={t('dashboard.chart.series.ram')} />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-slate-400">
                  {t('dashboard.chart.collecting')}
                </div>
              )}
            </motion.div>

            {/* Disk Usage Pie Chart */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.2 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <HardDrive className="text-purple-500 status-icon active" />
                {t('dashboard.chart.diskUsage')}
              </h2>
              {stats?.disk && (stats.disk.mountpoint || stats.disk.partition) && (
                <p className="text-slate-400 text-sm mb-2">
                  {t('dashboard.chart.partition', {
                    mount: stats.disk.mountpoint || '/',
                    devicePart: stats.disk.partition ? t('dashboard.chart.partitionDevice', { partition: stats.disk.partition }) : '',
                  })}
                </p>
              )}
              {diskData.length > 0 ? (
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={diskData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {diskData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: 'rgba(30, 41, 59, 0.95)',
                        border: '1px solid rgba(148, 163, 184, 0.2)',
                        borderRadius: '8px',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-slate-400">
                  {t('dashboard.chart.loading')}
                </div>
              )}
              <p className="text-slate-400 text-xs mt-3 border-l-2 border-purple-500/50 pl-2" title="TIP">
                <span className="text-purple-400 font-medium">{t('dashboard.chart.diskTip')}</span> {t('dashboard.chart.diskTipBody')}
              </p>
            </motion.div>
          </div>
          )}

          {/* Detailed Stats – nur Übersicht (System Info + Installation Status) */}
          {dashboardSection === 'overview' && (
          <div className="grid md:grid-cols-2 gap-6">
            {/* System Info */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.3 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Zap className="text-yellow-500 status-icon active" />
                {t('dashboard.systemInfoCard.title')}
              </h2>
              <StatusItem
                label={t('dashboard.systemInfo.os')}
                status="active"
                value={stats.os?.name || stats.platform?.system || "Linux"}
              />
              <StatusItem
                label={t('dashboard.systemInfo.osVersion')}
                status="active"
                value={stats.os?.version || t('dashboard.systemInfo.unknown')}
              />
              <StatusItem
                label={t('dashboard.systemInfo.kernel')}
                status="active"
                value={stats.os?.kernel || stats.platform?.release?.substring(0, 20) || t('dashboard.systemInfo.unknown')}
              />
              <StatusItem
                label={t('dashboard.systemInfo.cpu')}
                status="active"
                value={(() => {
                  const threads = stats.cpu?.count ?? stats.cpu_summary?.threads
                  const cores = stats.cpu_summary?.cores ?? stats.cpu?.physical_cores ?? (threads != null ? Math.max(1, Math.floor(Number(threads) / 2)) : null)
                  if (threads == null) return '—'
                  return (cores != null && cores > 0 && cores !== threads)
                    ? t('dashboard.systemInfo.cpuThreadsCores', { threads, cores })
                    : t('dashboard.systemInfo.cpuThreadsOnly', { threads })
                })()}
              />
              <StatusItem
                label={t('dashboard.systemInfo.memoryTotal')}
                status="active"
                value={`${Math.round((stats.memory?.total || 0) / 1024 / 1024 / 1024)} GB`}
              />
            </motion.div>

            {/* Installation Status */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.4 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <AppIcon name="complete" category="status" size={24} statusColor={getSecurityStatus() === 'active' ? 'ok' : 'muted'} />
                {t('dashboard.installStatus.title')}
              </h2>
              <StatusItem
                label={t('dashboard.installStatus.security')}
                status={getSecurityStatus()}
                value={getSecurityStatusText()}
                tooltip={t('dashboard.installStatus.tooltip.security')}
              />
              <StatusItem
                label={t('dashboard.installStatus.users')}
                status="inactive"
                value={t('dashboard.installStatus.users.value')}
                tooltip={t('dashboard.installStatus.tooltip.users')}
              />
              <StatusItem
                label={t('dashboard.installStatus.dev')}
                status={servicesStatus?.dev?.basic_ok ? 'active' : 'inactive'}
                value={servicesStatus?.dev != null ? t('dashboard.installStatus.dev.value', {
                  installed: servicesStatus.dev.installed_count,
                  total: servicesStatus.dev.total_parts,
                  state: servicesStatus.dev.basic_ok ? t('dashboard.installStatus.dev.ok') : t('dashboard.installStatus.dev.incomplete'),
                }) : t('dashboard.installStatus.ellipsis')}
                tooltip={t('dashboard.installStatus.tooltip.dev')}
              />
              <StatusItem
                label={t('dashboard.installStatus.web')}
                status={servicesStatus?.webserver?.reachable ? 'active' : 'inactive'}
                value={servicesStatus?.webserver != null ? (servicesStatus.webserver.reachable ? t('dashboard.installStatus.web.up') : servicesStatus.webserver.running ? t('dashboard.installStatus.web.running') : t('dashboard.installStatus.web.notInstalled')) : t('dashboard.installStatus.ellipsis')}
                tooltip={t('dashboard.installStatus.tooltip.web')}
              />
              <StatusItem
                label={t('dashboard.installStatus.music')}
                status={servicesStatus?.musicbox?.basic_ok ? 'active' : 'inactive'}
                value={servicesStatus?.musicbox != null ? (servicesStatus.musicbox.basic_ok ? t('dashboard.installStatus.music.ok') : servicesStatus.musicbox.installed ? t('dashboard.installStatus.music.installedNotStarted') : t('dashboard.installStatus.music.notInstalled')) : t('dashboard.installStatus.ellipsis')}
                tooltip={t('dashboard.installStatus.tooltip.music')}
              />
            </motion.div>
          </div>
          )}

          {/* CPU & Grafik – nur Auslastung & Grafik: eine CPU-Zusammenfassung, iGPU/Grafikkarte, Kerne-Auslastung (keine Thread-Liste) */}
          {dashboardSection === 'charts' && (stats.cpu_summary?.name || stats.cpu_name || stats.hardware?.gpus?.length > 0 || (stats.cpu?.per_core_usage?.length ?? 0) > 0) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.35 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Cpu className="text-sky-500 status-icon active" />
                {t('dashboard.cpuGpu.title')}
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <h3 className="text-sm font-semibold text-slate-300 mb-2">{t('dashboard.cpuGpu.cpuHeading')}</h3>
                  {(stats.cpu_summary?.name || stats.cpu_name) ? (
                    <div className="p-3 bg-slate-700/30 rounded-lg border border-slate-600 space-y-2">
                      <div className="font-medium text-white">
                        {stats.cpu_summary?.name || stats.cpu_name || t('dashboard.cpuGpu.unknown')}
                      </div>
                      <div className="text-xs text-slate-300 flex flex-wrap gap-x-3 gap-y-0.5">
                        {(() => {
                          const cores = stats.cpu_summary?.cores ?? stats.cpu?.physical_cores
                          const threads = stats.cpu_summary?.threads ?? stats.cpu?.count
                          const coresDisplay = (cores != null && cores > 0) ? cores : (threads != null && threads > 0 ? Math.max(1, Math.floor(Number(threads) / 2)) : null)
                          return (
                            <>
                              {coresDisplay != null && coresDisplay > 0 && <span>{t('dashboard.cpuGpu.cores', { n: coresDisplay })}</span>}
                              {threads != null && threads > 0 && <span>{t('dashboard.cpuGpu.threads', { n: threads })}</span>}
                            </>
                          )
                        })()}
                      </div>
                      {stats.cpu_summary?.cache && (
                        <div className="text-xs text-slate-400">{t('dashboard.cpuGpu.cache', { v: stats.cpu_summary.cache })}</div>
                      )}
                      {stats.cpu_summary?.flags && (
                        <details className="text-xs text-slate-400">
                          <summary className="cursor-pointer text-sky-400 hover:text-sky-300">{t('dashboard.cpuGpu.showIsas')}</summary>
                          <p className="mt-1 break-all opacity-90">{stats.cpu_summary.flags}</p>
                        </details>
                      )}
                      {stats.motherboard && (stats.motherboard.vendor || stats.motherboard.name) && (
                        <div className="text-xs text-slate-400">
                          {t('dashboard.cpuGpu.mainboard', { v: [stats.motherboard.vendor, stats.motherboard.name].filter(Boolean).join(' – ') || stats.motherboard.product || '–' })}
                        </div>
                      )}
                      {((stats.cpu_summary?.name || stats.cpu_name || '').toLowerCase().includes('intel') && (
                        <a href="https://www.intel.de/content/www/de/de/support/detect.html" target="_blank" rel="noopener noreferrer" className="text-xs text-sky-400 hover:text-sky-300 inline-block">{t('dashboard.cpuGpu.driverIntel')}</a>
                      )) || ((stats.cpu_summary?.name || stats.cpu_name || '').toLowerCase().includes('amd') && (
                        <a href="https://www.amd.com/de/support" target="_blank" rel="noopener noreferrer" className="text-xs text-sky-400 hover:text-sky-300 inline-block">{t('dashboard.cpuGpu.driverAmd')}</a>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500 text-sm">{t('dashboard.cpuGpu.noCpuData')}</p>
                  )}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-300 mb-2">{t('dashboard.cpuGpu.graphicsHeading')}</h3>
                  {stats.hardware?.gpus && stats.hardware.gpus.length > 0 ? (
                    <ul className="space-y-2">
                      {(() => {
                        const tip = stats.manufacturer_driver_tip || ''
                        const nvidiaTip = tip.includes('NVIDIA:') ? (tip.split('NVIDIA:')[1] || '').split('AMD:')[0].split('Intel:')[0].trim() : null
                        const amdTip = tip.includes('AMD:') ? (tip.split('AMD:')[1] || '').split('NVIDIA:')[0].split('Intel:')[0].trim() : null
                        const intelTip = tip.includes('Intel:') ? (tip.split('Intel:')[1] || '').split('NVIDIA:')[0].split('AMD:')[0].trim() : null
                        const integrated = stats.hardware.gpus.filter((g: any) => g.gpu_type === 'integrated')
                        const discrete = stats.hardware.gpus.filter((g: any) => g.gpu_type !== 'integrated')
                        const sorted = [...integrated, ...discrete]
                        return sorted.map((gpu: any, idx: number) => {
                          const name = gpu.display_name || gpu.name || gpu.description || t('dashboard.cpuGpu.unknown')
                          const nameLower = (name || '').toLowerCase()
                          const mem = gpu.memory_display || (gpu.memory_mb != null ? `${gpu.memory_mb} MB` : null)
                          const isNvidia = nameLower.includes('nvidia')
                          const isAmd = nameLower.includes('amd') || nameLower.includes('radeon')
                          const isIntel = nameLower.includes('intel')
                          const driverTip = isNvidia && nvidiaTip ? nvidiaTip : isAmd && amdTip ? amdTip : isIntel && intelTip ? intelTip : null
                          const label = gpu.gpu_type === 'integrated' ? t('dashboard.cpuGpu.label.igpu') : t('dashboard.cpuGpu.label.discrete')
                          return (
                            <li key={idx} className={`p-3 rounded-lg border ${isNvidia ? 'bg-slate-700/50 border-green-600/50' : 'bg-slate-700/30 border-slate-600'}`}>
                              <div className="text-xs text-slate-400 mb-0.5">{label}</div>
                              <div className="font-medium text-white">{name}</div>
                              {mem && (
                                <div className="text-xs text-slate-400 mt-1">{t('dashboard.cpuGpu.vram', { v: mem })}</div>
                              )}
                              {isNvidia && gpu.driver && (
                                <div className="text-xs text-slate-400 mt-0.5">{t('dashboard.cpuGpu.driver', { v: gpu.driver })}</div>
                              )}
                              {driverTip && (
                                <p className="text-slate-400 text-xs border-l-2 border-sky-500/50 pl-2 mt-1.5" title="TIP">
                                  <span className="text-sky-400 font-medium">{t('dashboard.cpuGpu.tipPrefix')}</span> {driverTip}
                                </p>
                              )}
                            </li>
                          )
                        })
                      })()}
                    </ul>
                  ) : (
                    <p className="text-slate-500 text-sm">{t('dashboard.cpuGpu.noGpuData')}</p>
                  )}
                </div>
                {(stats.cpu?.per_core_usage?.length ?? 0) > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-2">{t('dashboard.cpuGpu.perCoreTitle', { n: stats.cpu.per_core_usage.length })}</h3>
                    <div className="space-y-1.5">
                      {stats.cpu.per_core_usage.map((pct: number, idx: number) => (
                        <div key={idx} className="flex items-center gap-2">
                          <span className="text-xs text-slate-400 w-5 shrink-0">{t('dashboard.cpuGpu.coreShort', { n: idx + 1 })}</span>
                          <div className="flex-1 h-4 bg-slate-700 rounded overflow-hidden" title={t('dashboard.cpuGpu.coreTitle', { n: idx + 1, pct: pct.toFixed(0) })}>
                            <div
                              className="h-full bg-sky-500 transition-all"
                              style={{ width: `${Math.min(100, pct)}%`, minWidth: pct > 0 ? '2px' : 0 }}
                            />
                          </div>
                          <span className="text-xs text-slate-400 w-8">{pct.toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Sensoren & Schnittstellen – nur Hardware & Sensoren */}
          {dashboardSection === 'hardware' && (stats.sensors?.length > 0 || stats.disks?.length > 0 || stats.fans?.length > 0 || stats.displays?.length > 0) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.4 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Thermometer className="text-amber-500" />
                {t('dashboard.sensors.title')}
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.sensors && stats.sensors.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-1">
                      <Thermometer size={14} /> {t('dashboard.sensors.temp')}
                    </h3>
                    <ul className="space-y-1">
                      {stats.sensors.map((s: any, idx: number) => (
                        <li
                          key={idx}
                          className="p-2 bg-slate-700/30 rounded text-sm cursor-help"
                          title={getSensorTooltip(s)}
                        >
                          <span className="text-white">{s.name || s.zone}</span>
                          <span className="text-amber-400 ml-2">{s.temperature} °C</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {stats.disks && stats.disks.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-1">
                      <HardDrive size={14} /> {t('dashboard.sensors.disks')}
                    </h3>
                    <ul className="space-y-1">
                      {stats.disks.map((d: any, idx: number) => (
                        <li
                          key={idx}
                          className="p-2 bg-slate-700/30 rounded text-sm cursor-help"
                          title={getDiskTooltip(d)}
                        >
                          <span className="text-white">{d.label || d.mountpoint || d.device}</span>
                          <span className="text-slate-400 ml-2">
                            {d.percent != null ? `${d.used_gb}/${d.total_gb} GB (${d.percent}%)` : t('dashboard.sensors.diskTotal', { total: d.total_gb })}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {stats.fans && stats.fans.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-1">
                      <Wind size={14} /> {t('dashboard.sensors.fans')}
                    </h3>
                    <ul className="space-y-1">
                      {stats.fans.map((f: any, idx: number) => (
                        <li
                          key={idx}
                          className="p-2 bg-slate-700/30 rounded text-sm cursor-help"
                          title={getFanTooltip(f)}
                        >
                          <span className="text-white">{f.name}</span>
                          <span className="text-sky-400 ml-2">{f.rpm} RPM</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {stats.displays && stats.displays.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-1">
                      <Monitor size={14} /> {t('dashboard.sensors.displays')}
                    </h3>
                    <ul className="space-y-1">
                      {stats.displays.map((d: any, idx: number) => (
                        <li
                          key={idx}
                          className="p-2 bg-slate-700/30 rounded text-sm cursor-help"
                          title={getDisplayTooltip(d)}
                        >
                          <span className="text-white">{d.output}</span>
                          {d.mode && <span className="text-slate-400 ml-2">{d.mode}</span>}
                          {d.connected && <span className="text-green-400 ml-1">●</span>}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Systembezogene Treiber – nur Hardware & Sensoren */}
          {dashboardSection === 'hardware' && stats.drivers && stats.drivers.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.45 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Settings className="text-slate-400" />
                {t('dashboard.drivers.title')}
              </h2>
              <ul className="space-y-2 max-h-48 overflow-y-auto">
                {stats.drivers.map((d: any, idx: number) => (
                  <li key={idx} className="p-2 bg-slate-700/30 rounded-lg flex justify-between items-center text-sm">
                    <span className="text-slate-300 truncate mr-2">{d.device}</span>
                    <span className={`font-medium shrink-0 ${d.driver === '—' ? 'text-slate-500' : 'text-green-400'}`}>{d.driver}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          )}

          {/* Module Overview – für Fortgeschrittene/Entwickler, nicht im Beginner-View */}
          {dashboardSection === 'overview' && !isBeginnerView && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.5 }}
            className="card"
          >
            <h2 className="text-xl font-bold text-white mb-6">{t('dashboard.modules.title')}</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              <ModuleCard
                icon={Shield}
                title={t('dashboard.modules.security.title')}
                description={t('dashboard.modules.security.desc')}
                tooltip={t('dashboard.modules.security.tooltip')}
                status="ready"
                page="security"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Users}
                title={t('dashboard.modules.users.title')}
                description={t('dashboard.modules.users.desc')}
                tooltip={t('dashboard.modules.users.tooltip')}
                status="ready"
                page="users"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Code}
                title={t('dashboard.modules.dev.title')}
                description={t('dashboard.modules.dev.desc')}
                tooltip={t('dashboard.modules.dev.tooltip')}
                status="ready"
                page="devenv"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Globe}
                title={t('dashboard.modules.web.title')}
                description={t('dashboard.modules.web.desc')}
                tooltip={t('dashboard.modules.web.tooltip')}
                status="ready"
                page="webserver"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Mail}
                title={t('dashboard.modules.mail.title')}
                description={t('dashboard.modules.mail.desc')}
                tooltip={t('dashboard.modules.mail.tooltip')}
                status="ready"
                page="mailserver"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Database}
                title={t('dashboard.modules.nas.title')}
                description={t('dashboard.modules.nas.desc')}
                tooltip={t('dashboard.modules.nas.tooltip')}
                status="ready"
                page="nas"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Home}
                title={t('dashboard.modules.home.title')}
                description={t('dashboard.modules.home.desc')}
                tooltip={t('dashboard.modules.home.tooltip')}
                status="ready"
                page="homeautomation"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Music}
                title={t('dashboard.modules.music.title')}
                description={t('dashboard.modules.music.desc')}
                tooltip={t('dashboard.modules.music.tooltip')}
                status="ready"
                page="musicbox"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Settings}
                title={t('dashboard.modules.presets.title')}
                description={t('dashboard.modules.presets.desc')}
                tooltip={t('dashboard.modules.presets.tooltip')}
                status="ready"
                page="presets"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={BookOpen}
                title={t('dashboard.modules.learning.title')}
                description={t('dashboard.modules.learning.desc')}
                tooltip={t('dashboard.modules.learning.tooltip')}
                status="ready"
                page="learning"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Activity}
                title={t('dashboard.modules.monitoring.title')}
                description={t('dashboard.modules.monitoring.desc')}
                tooltip={t('dashboard.modules.monitoring.tooltip')}
                status="ready"
                page="monitoring"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={HardDrive}
                title={t('dashboard.modules.backup.title')}
                description={t('dashboard.modules.backup.desc')}
                tooltip={t('dashboard.modules.backup.tooltip')}
                status="ready"
                page="backup"
                setCurrentPage={setCurrentPage}
              />
            </div>
          </motion.div>
          )}

          {/* Quick Actions / Schnellstart – nur Übersicht */}
          {dashboardSection === 'overview' && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.6 }}
            className="bg-gradient-to-r from-sky-600/20 to-blue-600/20 border border-sky-500/30 rounded-lg p-6 backdrop-blur-sm"
          >
            <h2 className="text-xl font-bold text-slate-800 dark:text-white mb-4">{t('dashboard.quickstart.title')}</h2>
            <p className="text-slate-700 dark:text-slate-300 mb-4 font-medium">
              {t('dashboard.quickstart.body')}
            </p>
            <button 
              onClick={() => setCurrentPage && setCurrentPage('wizard')}
              className="btn-primary"
            >
              {t('dashboard.quickstart.button')}
            </button>
          </motion.div>
          )}
        </>
      )}

      {/* Loading State */}
      {!stats && !loading && (
        <div className="card flex items-center justify-center p-12">
          <div className="animate-spin-slow">
            <Zap className="text-sky-500" size={48} />
          </div>
          <p className="ml-4 text-slate-300">{t('dashboard.loading')}</p>
        </div>
      )}
    </motion.div>
  )
}

const ModuleCard = ({ icon: Icon, title, description, tooltip, status, page, setCurrentPage }: any) => {
  const { t } = useTranslation()
  return (
    <motion.div
      whileHover={{ scale: 1.02, y: -4 }}
      whileTap={{ scale: 0.98 }}
      onClick={() => setCurrentPage && setCurrentPage(page)}
      className="relative isolate z-0 hover:z-40 bg-slate-700/50 hover:bg-slate-700/70 border border-slate-600 rounded-lg p-4 transition-all cursor-pointer backdrop-blur-sm"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="relative group">
          <motion.div
            animate={{ rotate: [0, 5, -5, 0] }}
            transition={{ duration: 2, repeat: Infinity, repeatDelay: 5 }}
          >
            <Icon className="text-sky-400" size={24} />
          </motion.div>
          {tooltip && (
            <div className="pointer-events-none absolute left-0 top-8 opacity-0 group-hover:opacity-100 transition-opacity z-50">
              <div className="max-w-xs whitespace-pre-line text-xs text-slate-100 bg-slate-900/95 border border-slate-700 rounded-lg px-3 py-2 shadow-xl">
                {tooltip}
              </div>
            </div>
          )}
        </div>
        <span className="px-2 py-1 bg-green-900/50 text-green-400 text-xs rounded-full font-semibold backdrop-blur-sm">
          {t('dashboard.moduleCard.ready')}
        </span>
      </div>
      <h3 className="font-bold text-white">{title}</h3>
      <p className="text-sm text-slate-400">{description}</p>
    </motion.div>
  )
}

export default Dashboard
