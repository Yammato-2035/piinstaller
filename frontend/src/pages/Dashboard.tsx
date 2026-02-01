import React, { useEffect, useState } from 'react'
import { fetchApi } from '../api'
import { usePlatform } from '../context/PlatformContext'
import { 
  Cpu, 
  HardDrive, 
  Zap, 
  Clock,
  CheckCircle,
  AlertCircle,
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
  LayoutDashboard,
  Thermometer,
  Wind,
  Monitor,
} from 'lucide-react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { motion } from 'framer-motion'

interface DashboardProps {
  systemInfo: any
  backendError?: boolean
  setCurrentPage?: (page: string) => void
}

/** Tooltip-Text für Sensoren: was es ist, wo es sitzt, Normalwert lt. Hersteller/typisch. */
function getSensorTooltip(s: { name?: string; zone?: string }): string {
  const name = (s.name || '').toLowerCase()
  const zone = (s.zone || '').toLowerCase()
  if (zone === 'vcgencmd' || (name === 'cpu' && zone.includes('vcgencmd'))) {
    return 'Was: Raspberry-Pi-SoC-Temperatur (CPU/GPU).\nWo: Onboard (vcgencmd).\nNormal: ca. 40–70°C im Betrieb, > 80°C kritisch – Kühlung prüfen.'
  }
  if (name.includes('x86_pkg_temp') || name.includes('cpu package')) {
    return 'Was: CPU-Package-Temperatur.\nWo: Onboard (thermal_zone).\nNormal: je nach Hersteller oft < 90°C unter Last.'
  }
  if (name.includes('nvme')) {
    return 'Was: NVMe-SSD-Temperatur.\nWo: M.2-Steckplatz oder PCIe.\nNormal: typisch 30–70°C, Herstellerangaben beachten.'
  }
  if (name.includes('gpu') || name.includes('radeon') || name.includes('nvidia') || name.includes('amd')) {
    return 'Was: Grafikkarten-(GPU-)Temperatur.\nWo: PCIe oder onboard.\nNormal: unter Last oft < 85°C (Herstellerangaben beachten).'
  }
  if (name.includes('acpitz') || name.includes('igpu') || name.includes('apu')) {
    return 'Was: APU/iGPU oder ACPI-Thermal-Zone.\nWo: Onboard.\nNormal: je nach Hersteller.'
  }
  if (zone.startsWith('thermal_zone')) {
    return `Was: Temperatursensor (${s.name || zone}).\nWo: /sys/class/thermal/${zone}.\nNormal: Herstellerangaben beachten (z. B. CPU < 90°C).`
  }
  return `Was: ${s.name || 'Temperatursensor'}.\nWo: ${s.zone || 'Onboard'}.\nNormal: Herstellerangaben beachten.`
}

/** Tooltip für Laufwerke. */
function getDiskTooltip(d: { label?: string; mountpoint?: string; device?: string }): string {
  const where = d.mountpoint || d.device || 'Unbekannt'
  return `Was: Speicherlaufwerk (Festplatte/SSD).\nWo: ${where}.\nNormal: Auslastung je nach Nutzung; > 90 % kann Performance beeinträchtigen.`
}

/** Tooltip für Lüfter. */
function getFanTooltip(f: { name?: string }): string {
  return `Was: Lüfter (RPM = U/min).\nWo: Gehäuse/CPU-Kühler (hwmon).\nNormal: Drehzahl je nach Hersteller und Last; 0 RPM = Lüfter aus oder nicht erkannt.`
}

/** Tooltip für Displays. */
function getDisplayTooltip(d: { output?: string; mode?: string }): string {
  return `Was: Bildschirmausgabe.\nWo: ${d.output || 'Display'}.\nNormal: Verbunden und Auflösung (${d.mode || '—'}) passend.`
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
        <motion.div
          animate={{ rotate: [0, 5, -5, 0] }}
          transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
          className="p-3 bg-sky-600/20 rounded-lg backdrop-blur-sm"
        >
          <Icon className="text-sky-500" size={32} />
        </motion.div>
      </div>
    </motion.div>
  )
})

const Dashboard: React.FC<DashboardProps> = ({ systemInfo, backendError, setCurrentPage }) => {
  const { systemLabel } = usePlatform()
  const [stats, setStats] = useState<any>(null)
  const [securityConfig, setSecurityConfig] = useState<any>(null)
  const [historyData, setHistoryData] = useState<any[]>([])
  const [updatesData, setUpdatesData] = useState<{ total: number; categories?: Record<string, number>; updates?: { package: string; version: string; category: string }[] } | null>(null)
  const [updatesModalOpen, setUpdatesModalOpen] = useState(false)
  const [updateTerminalLoading, setUpdateTerminalLoading] = useState(false)
  const [updateTerminalError, setUpdateTerminalError] = useState<{ message?: string; copyable_command?: string } | null>(null)
  const [servicesStatus, setServicesStatus] = useState<{ dev?: { installed_count: number; total_parts: number; basic_ok: boolean }; webserver?: { running: boolean; reachable: boolean }; musicbox?: { installed: boolean; basic_ok: boolean } } | null>(null)
  const loading = !systemInfo && !backendError

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
    const interval = setInterval(async () => {
      try {
        const response = await fetchApi('/api/system-info')
        const data = await response.json()
        if (data) {
          setStats(data)
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
    }, 5000)
    
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
        toast.success(data.message || 'Terminal geöffnet – Passwort dort eingeben.')
      } else {
        setUpdateTerminalError({ message: data.message, copyable_command: data.copyable_command })
        toast.error(data.message || 'Terminal konnte nicht geöffnet werden.')
      }
    } catch (e) {
      setUpdateTerminalError({ message: 'Fehler beim Öffnen des Terminals.', copyable_command: 'sudo apt update && sudo apt upgrade' })
      toast.error('Fehler beim Öffnen des Terminals.')
    } finally {
      setUpdateTerminalLoading(false)
    }
  }
  const copyUpdateCommand = () => {
    const cmd = updateTerminalError?.copyable_command || 'sudo apt update && sudo apt upgrade'
    navigator.clipboard?.writeText(cmd).then(() => toast.success('Befehl in Zwischenablage kopiert.')).catch(() => {})
  }

  const getSecurityStatus = () => {
    if (!securityConfig) return 'inactive'
    
    // Zähle aktivierte Sicherheitsfeatures
    let activeCount = 0
    let totalCount = 0
    
    if (securityConfig.ufw) {
      totalCount++
      if (securityConfig.ufw.active) activeCount++
    }
    if (securityConfig.fail2ban) {
      totalCount++
      if (securityConfig.fail2ban.active) activeCount++
    }
    if (securityConfig.auto_updates) {
      totalCount++
      if (securityConfig.auto_updates.enabled) activeCount++
    }
    if (securityConfig.ssh_hardening) {
      totalCount++
      if (securityConfig.ssh_hardening.enabled) activeCount++
    }
    if (securityConfig.audit_logging) {
      totalCount++
      if (securityConfig.audit_logging.enabled) activeCount++
    }
    
    // Wenn mehr als 50% aktiviert sind, zeige als "active"
    if (totalCount > 0 && activeCount / totalCount >= 0.5) {
      return 'active'
    }
    return 'inactive'
  }

  const getSecurityStatusText = () => {
    if (!securityConfig) return 'Nicht konfiguriert'
    
    let activeCount = 0
    let totalCount = 0
    
    if (securityConfig.ufw) {
      totalCount++
      if (securityConfig.ufw.active) activeCount++
    }
    if (securityConfig.fail2ban) {
      totalCount++
      if (securityConfig.fail2ban.active) activeCount++
    }
    if (securityConfig.auto_updates) {
      totalCount++
      if (securityConfig.auto_updates.enabled) activeCount++
    }
    if (securityConfig.ssh_hardening) {
      totalCount++
      if (securityConfig.ssh_hardening.enabled) activeCount++
    }
    if (securityConfig.audit_logging) {
      totalCount++
      if (securityConfig.audit_logging.enabled) activeCount++
    }
    
    if (totalCount === 0) return 'Nicht konfiguriert'
    if (activeCount === totalCount) return 'Vollständig konfiguriert'
    return `${activeCount}/${totalCount} aktiviert`
  }

  const SkeletonCard = () => (
    <div className="card">
      <div className="animate-pulse">
        <div className="h-4 bg-slate-700 rounded w-1/2 mb-4"></div>
        <div className="h-8 bg-slate-700 rounded w-1/3"></div>
      </div>
    </div>
  )

  const StatusItem = ({ label, status, value, tooltip }: any) => (
    <div className="flex items-center justify-between p-4 border-b border-slate-700 last:border-0">
      <div className="flex items-center gap-3">
        <div className="relative group">
          {status === 'active' ? (
            <CheckCircle className="text-green-500" size={20} />
          ) : (
            <AlertCircle className="text-yellow-500" size={20} />
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
          ? 'bg-green-900 text-green-200' 
          : 'bg-yellow-900 text-yellow-200'
      }`}>
        {value}
      </span>
    </div>
  )

  const chartColors = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
  
  const diskData = stats ? [
    { name: 'Belegt', value: stats.disk?.percent || 0, color: '#ef4444' },
    { name: 'Frei', value: 100 - (stats.disk?.percent || 0), color: '#10b981' },
  ] : []

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="space-y-8 page-transition"
    >
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <LayoutDashboard className="text-sky-400" />
            Dashboard
          </h1>
        </div>
        <p className="text-slate-400">Übersicht – {systemLabel}</p>
      </motion.div>

      {backendError && !stats && (
        <div className="card-warning flex items-start gap-3">
          <AlertCircle className="shrink-0 mt-0.5 opacity-90" size={24} />
          <div>
            <h3 className="font-semibold">Backend nicht erreichbar</h3>
            <p className="text-sm mt-1 opacity-95">
              Dashboard-Daten und Sudo-Passwort-Speicherung funktionieren nur, wenn das Backend läuft.
              Backend starten: <code className="opacity-90 px-1 rounded">./start.sh</code> oder <code className="opacity-90 px-1 rounded">./start-backend.sh</code> im Projektordner.
              Log-Datei: Einstellungen → Logs → „Logs laden“ (Pfad wird angezeigt).
            </p>
            {setCurrentPage && (
              <button
                onClick={() => setCurrentPage('settings')}
                className="mt-3 text-sm underline hover:opacity-90"
              >
                Einstellungen → Logs öffnen
              </button>
            )}
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
                {updatesData.total} {updatesData.total === 1 ? 'Update' : 'Updates'} verfügbar
              </h3>
              {updatesData.categories && (
                <p className="text-sm text-slate-400 mt-0.5">
                  {updatesData.categories.security > 0 && <span className="text-red-300">{updatesData.categories.security} Sicherheit</span>}
                  {updatesData.categories.security > 0 && (updatesData.categories.critical! > 0 || updatesData.categories.necessary! > 0 || updatesData.categories.optional! > 0) && ' · '}
                  {updatesData.categories.critical! > 0 && <span className="text-amber-300">{updatesData.categories.critical} Kritisch</span>}
                  {(updatesData.categories.critical! > 0) && (updatesData.categories.necessary! > 0 || updatesData.categories.optional! > 0) && ' · '}
                  {updatesData.categories.necessary! > 0 && <span className="text-slate-300">{updatesData.categories.necessary} Notwendig</span>}
                  {(updatesData.categories.necessary! > 0) && updatesData.categories.optional! > 0 && ' · '}
                  {updatesData.categories.optional! > 0 && <span className="text-slate-400">{updatesData.categories.optional} Optional</span>}
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
              Welche Updates?
            </button>
            <button
              type="button"
              onClick={runUpdateInTerminal}
              disabled={updateTerminalLoading}
              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium disabled:opacity-50"
            >
              {updateTerminalLoading ? '…' : 'Update im Terminal ausführen'}
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
              <strong className="text-white">System-Update (apt update &amp; upgrade):</strong> Terminal öffnen, dort Passwort eingeben.
            </p>
            {updateTerminalError?.copyable_command && (
              <p className="text-slate-400 text-xs mt-2 flex items-center gap-2 flex-wrap">
                <span>Befehl manuell ausführen:</span>
                <code className="bg-slate-700 px-2 py-1 rounded text-slate-200 font-mono text-xs">{updateTerminalError.copyable_command}</code>
                <button type="button" onClick={copyUpdateCommand} className="px-2 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-xs">Kopieren</button>
              </p>
            )}
          </div>
          <button
            type="button"
            onClick={runUpdateInTerminal}
            disabled={updateTerminalLoading}
            className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium disabled:opacity-50 shrink-0"
          >
            {updateTerminalLoading ? '…' : 'Im Terminal ausführen'}
          </button>
        </motion.div>
      )}

      {/* Modal: Liste der Updates */}
      {updatesModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60" onClick={() => setUpdatesModalOpen(false)}>
          <div className="bg-slate-800 border border-slate-600 rounded-xl shadow-xl max-w-2xl w-full max-h-[80vh] flex flex-col" onClick={e => e.stopPropagation()}>
            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">Verfügbare Updates</h3>
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
                        {u.category === 'security' ? 'Sicherheit' : u.category === 'critical' ? 'Kritisch' : u.category === 'necessary' ? 'Notwendig' : 'Optional'}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-slate-400">Keine Details geladen.</p>
              )}
              <p className="text-slate-500 text-xs mt-4">Installation z. B. über Terminal: <code className="bg-slate-700 px-1 rounded">sudo apt update && sudo apt upgrade</code></p>
              <button
                type="button"
                onClick={runUpdateInTerminal}
                disabled={updateTerminalLoading}
                className="mt-3 px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium disabled:opacity-50"
              >
                {updateTerminalLoading ? '…' : 'Update im Terminal ausführen'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* System Stats */}
      {loading ? (
        <div className="grid-responsive">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : stats && (
        <>
          <div className="grid-responsive">
            <StatCard
              key="cpu-usage"
              icon={Cpu}
              label="CPU Auslastung"
              value={stats.cpu?.usage?.toFixed(1) || 0}
              unit="%"
            />
            <StatCard
              key="ram-usage"
              icon={HardDrive}
              label="RAM Auslastung"
              value={stats.memory?.percent?.toFixed(1) || 0}
              unit="%"
            />
            <StatCard
              key="disk-free"
              icon={Zap}
              label="Speicher Frei"
              value={Math.round((stats.disk?.free || 0) / 1024 / 1024 / 1024)}
              unit=" GB"
            />
            <StatCard
              key="uptime"
              icon={Clock}
              label="System Uptime"
              value={stats.uptime || 'N/A'}
            />
            {stats.cpu?.temperature && (
              <StatCard
                key="cpu-temp"
                icon={Cpu}
                label="CPU Temperatur"
                value={stats.cpu.temperature}
                unit="°C"
              />
            )}
            {stats.cpu?.fan_speed && (
              <StatCard
                key="fan-speed"
                icon={Zap}
                label="Lüfter Geschwindigkeit"
                value={typeof stats.cpu.fan_speed === 'number' ? stats.cpu.fan_speed : stats.cpu.fan_speed}
                unit={typeof stats.cpu.fan_speed === 'number' ? ' RPM' : ''}
              />
            )}
          </div>

          {/* IP-Adressen & Hostname – immer anzeigen wenn vorhanden */}
          {(stats.network?.ips?.length > 0 || stats.network?.hostname) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.06 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-3 flex items-center gap-2">
                <Globe className="text-slate-400" />
                Netzwerk – IP-Adressen
              </h2>
              <div className="flex flex-wrap items-center gap-4 text-sm">
                {stats.network.hostname && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-0.5">Hostname</span>
                    <span className="text-white font-mono">{stats.network.hostname}</span>
                  </div>
                )}
                {stats.network.ips && stats.network.ips.length > 0 && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">IP-Adressen</span>
                    <div className="flex flex-wrap gap-2">
                      {stats.network.ips.map((ip: string, i: number) => (
                        <span key={i} className="font-mono text-sky-300 bg-slate-800 px-2 py-1 rounded" title={`z. B. http://${ip}:6680/iris (Mopidy), http://${ip}:8000 (Backend)`}>
                          {ip}
                        </span>
                      ))}
                    </div>
                    <p className="text-slate-700 dark:text-slate-300 text-xs mt-2 font-medium">Mit dieser IP von anderen Geräten erreichbar (z. B. <span className="font-mono">http://{stats.network.ips[0]}:6680/iris</span> für Mopidy Iris).</p>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Systeminformationen – CPU-Name, Motherboard, OS, RAM-Typ/Geschwindigkeit */}
          {(stats.cpu_name || (stats.motherboard && Object.keys(stats.motherboard).length > 0) || stats.os?.name || (stats.ram_info && stats.ram_info.length > 0)) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.08 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Cpu className="text-slate-400" />
                Systeminformationen
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                {stats.cpu_name && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">CPU</span>
                    <span className="text-white">{stats.cpu_name}</span>
                  </div>
                )}
                {(stats.memory?.total != null) && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">Hauptspeicher</span>
                    <span className="text-white">{Math.round((stats.memory.total || 0) / 1024 / 1024 / 1024)} GB</span>
                  </div>
                )}
                {stats.motherboard && Object.keys(stats.motherboard).length > 0 && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">Motherboard</span>
                    <span className="text-white">
                      {[stats.motherboard.vendor, stats.motherboard.name].filter(Boolean).join(' – ') || stats.motherboard.product || '–'}
                    </span>
                  </div>
                )}
                {stats.hardware?.gpus?.length > 0 && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">Grafikkarte / Grafikspeicher</span>
                    <ul className="text-white text-xs space-y-0.5">
                      {stats.hardware.gpus.slice(0, 3).map((g: any, i: number) => (
                        <li key={i}>
                          {g.name || g.description || 'GPU'} {g.memory_mb != null ? ` · ${g.memory_mb} MB` : ''}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {stats.os?.name && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">Betriebssystem</span>
                    <span className="text-white">{stats.os.name}</span>
                  </div>
                )}
                {stats.ram_info && stats.ram_info.length > 0 && (
                  <div className="p-3 bg-slate-700/30 rounded-lg">
                    <span className="text-slate-400 block mb-1">RAM (Typ & Geschwindigkeit)</span>
                    <ul className="text-white text-xs space-y-0.5">
                      {stats.ram_info.slice(0, 4).map((r: any, i: number) => (
                        <li key={i}>
                          {r.Size} {r.Type || ''} {r.Speed ? `@ ${r.Speed}` : ''}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* Charts Section */}
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
                System Auslastung
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
                    <Area type="monotone" dataKey="cpu" stroke="#0ea5e9" fillOpacity={1} fill="url(#colorCpu)" name="CPU %" />
                    <Area type="monotone" dataKey="memory" stroke="#10b981" fillOpacity={1} fill="url(#colorMemory)" name="RAM %" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[200px] flex items-center justify-center text-slate-400">
                  Sammle Daten...
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
                Speicher Auslastung
              </h2>
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
                  Lade Daten...
                </div>
              )}
            </motion.div>
          </div>

          {/* Detailed Stats */}
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
                System Information
              </h2>
              <StatusItem
                label="Betriebssystem"
                status="active"
                value={stats.os?.name || stats.platform?.system || "Linux"}
              />
              <StatusItem
                label="OS Version"
                status="active"
                value={stats.os?.version || "Unbekannt"}
              />
              <StatusItem
                label="Kernel Version"
                status="active"
                value={stats.os?.kernel || stats.platform?.release?.substring(0, 20) || "Unbekannt"}
              />
              <StatusItem
                label="CPU Kerne"
                status="active"
                value={stats.cpu?.count}
              />
              <StatusItem
                label="Speicher Gesamt"
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
                <CheckCircle className={`text-green-500 status-icon ${getSecurityStatus() === 'active' ? 'active' : ''}`} />
                Installation Status
              </h2>
              <StatusItem
                label="Sicherheit"
                status={getSecurityStatus()}
                value={getSecurityStatusText()}
                tooltip={"Hier legst du die Basis-Sicherheit fest:\n- Firewall (UFW) aktivieren + Regeln prüfen\n- Fail2Ban aktivieren\n- SSH härten (z.B. Passwortlogin aus)\n- Automatische Sicherheitsupdates"}
              />
              <StatusItem
                label="Benutzer"
                status="inactive"
                value="Standard"
                tooltip={"Lege zusätzliche Benutzer an:\n- Admin vs. Standardnutzer\n- Starke Passwörter\n- Optional: SSH-Keys, Gruppen/Rechte"}
              />
              <StatusItem
                label="Dev-Umgebung"
                status={servicesStatus?.dev?.basic_ok ? 'active' : 'inactive'}
                value={servicesStatus?.dev != null ? `${servicesStatus.dev.installed_count}/${servicesStatus.dev.total_parts} Teile – ${servicesStatus.dev.basic_ok ? 'Grundbetrieb möglich' : 'nicht vollständig'}` : '…'}
                tooltip={"Installiere Tools fürs Entwickeln:\n- Python/Node\n- C/C++ Compiler (gcc/g++)\n- Java (JDK)\n- Git, Docker (optional)\n- Editor/IDE (z.B. VS Code Server/Cursor)"}
              />
              <StatusItem
                label="Webserver"
                status={servicesStatus?.webserver?.reachable ? 'active' : 'inactive'}
                value={servicesStatus?.webserver != null ? (servicesStatus.webserver.reachable ? 'Läuft – Webseiten erreichbar' : servicesStatus.webserver.running ? 'Läuft' : 'Nicht installiert') : '…'}
                tooltip={"Richte Hosting ein:\n- Nginx oder Apache\n- PHP (falls nötig)\n- Websites/Apps erkennen & zuordnen\n- Optional: CMS (WordPress/Nextcloud)\n- Admin-Panels (Cockpit/Webmin)"}
              />
              <StatusItem
                label="Musikbox"
                status={servicesStatus?.musicbox?.basic_ok ? 'active' : 'inactive'}
                value={servicesStatus?.musicbox != null ? (servicesStatus.musicbox.basic_ok ? 'Grundbetrieb möglich' : servicesStatus.musicbox.installed ? 'Installiert, nicht gestartet' : 'Nicht installiert') : '…'}
                tooltip={"Mopidy, Volumio oder Plex – Abspielen möglich wenn Dienst läuft."}
              />
            </motion.div>
          </div>

          {/* CPU & Grafik – CPUs, GPUs, Thread-Auslastung (Kerne) */}
          {(stats.hardware?.cpus?.length > 0 || stats.hardware?.gpus?.length > 0 || stats.cpu_name || (stats.cpu?.per_core_usage?.length ?? 0) > 0 || (stats.cpu?.per_cpu_usage?.length ?? 0) > 0) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.35 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Cpu className="text-sky-500 status-icon active" />
                CPU & Grafik
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                <div>
                  <h3 className="text-sm font-semibold text-slate-300 mb-2">CPUs</h3>
                  {(stats.hardware?.cpus?.length > 0 || stats.cpu_name) ? (
                    <ul className="space-y-2">
                      {(stats.hardware?.cpus?.length ? stats.hardware.cpus : [{ model: stats.cpu_name || 'Unbekannt' }]).map((cpu: any, idx: number) => (
                        <li key={idx} className="p-3 bg-slate-700/30 rounded-lg border border-slate-600">
                          <div className="font-medium text-white">
                            {typeof cpu.processor_id === 'number' ? `Prozessor ${cpu.processor_id}` : `CPU ${idx + 1}`}: {cpu.model || 'Unbekannt'}
                          </div>
                          <div className="text-xs text-slate-400 mt-1 flex flex-wrap gap-3">
                            {cpu.current_mhz != null && <span>Aktuell: {cpu.current_mhz} MHz</span>}
                            {cpu.recommended_mhz != null && <span>Empfohlen: {cpu.recommended_mhz} MHz</span>}
                          </div>
                          {((cpu.model || stats.cpu_name || '').toLowerCase().includes('intel') && (
                            <a href="https://www.intel.de/content/www/de/de/support/detect.html" target="_blank" rel="noopener noreferrer" className="text-xs text-sky-400 hover:text-sky-300 mt-1 inline-block">Treiber beim Hersteller (Intel) suchen</a>
                          )) || ((cpu.model || stats.cpu_name || '').toLowerCase().includes('amd') && (
                            <a href="https://www.amd.com/de/support" target="_blank" rel="noopener noreferrer" className="text-xs text-sky-400 hover:text-sky-300 mt-1 inline-block">Treiber beim Hersteller (AMD) suchen</a>
                          ))}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-slate-500 text-sm">Keine CPU-Daten</p>
                  )}
                  {stats.cpu?.count != null && (
                    <p className="text-slate-400 text-xs mt-2">Threads gesamt: {stats.cpu.count}</p>
                  )}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-300 mb-2">GPUs (Grafikkarte & Speicher)</h3>
                  {stats.hardware?.gpus && stats.hardware.gpus.length > 0 ? (
                    <ul className="space-y-2">
                      {stats.hardware.gpus.map((gpu: any, idx: number) => {
                        const name = gpu.name || gpu.description || 'Unbekannt'
                        const isNvidia = (name || '').toLowerCase().includes('nvidia')
                        return (
                          <li key={idx} className={`p-3 rounded-lg border ${isNvidia ? 'bg-slate-700/50 border-green-600/50' : 'bg-slate-700/30 border-slate-600'}`}>
                            <div className="font-medium text-white">{name}</div>
                            {gpu.memory_mb != null && (
                              <div className="text-xs text-slate-400 mt-1">Grafikspeicher: {gpu.memory_mb} MB</div>
                            )}
                            {isNvidia && gpu.driver && (
                              <div className="text-xs text-slate-400 mt-0.5">Treiber: {gpu.driver}</div>
                            )}
                          </li>
                        )
                      })}
                    </ul>
                  ) : (
                    <p className="text-slate-500 text-sm">Keine GPU-Daten</p>
                  )}
                </div>
                {(stats.cpu?.per_core_usage?.length ?? 0) > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-2">Auslastung physikalische Kerne ({stats.cpu.per_core_usage.length}) – horizontal</h3>
                    <div className="space-y-1.5">
                      {stats.cpu.per_core_usage.map((pct: number, idx: number) => (
                        <div key={idx} className="flex items-center gap-2">
                          <span className="text-xs text-slate-500 w-5 shrink-0">K{idx + 1}</span>
                          <div className="flex-1 h-4 bg-slate-700 rounded overflow-hidden" title={`Kern ${idx + 1}: ${pct.toFixed(0)}%`}>
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
                {(!stats.cpu?.per_core_usage || stats.cpu.per_core_usage.length === 0) && stats.cpu?.per_cpu_usage && stats.cpu.per_cpu_usage.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-2">Threads gesamt: {stats.cpu.per_cpu_usage.length} – Auslastung (horizontal)</h3>
                    <div className="space-y-1.5">
                      {stats.cpu.per_cpu_usage.map((pct: number, idx: number) => (
                        <div key={idx} className="flex items-center gap-2">
                          <span className="text-xs text-slate-500 w-5 shrink-0">{idx + 1}</span>
                          <div className="flex-1 h-3 bg-slate-700 rounded overflow-hidden" title={`Thread ${idx + 1}: ${pct.toFixed(0)}%`}>
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

          {/* Sensoren & Schnittstellen – alle Temperatur-, Laufwerk-, Lüfter-, Display-Daten */}
          {(stats.sensors?.length > 0 || stats.disks?.length > 0 || stats.fans?.length > 0 || stats.displays?.length > 0) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.4 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Thermometer className="text-amber-500" />
                Sensoren & Schnittstellen
              </h2>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                {stats.sensors && stats.sensors.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-1">
                      <Thermometer size={14} /> Temperatursensoren
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
                      <HardDrive size={14} /> Laufwerke
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
                            {d.percent != null ? `${d.used_gb}/${d.total_gb} GB (${d.percent}%)` : `${d.total_gb} GB gesamt`}
                          </span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {stats.fans && stats.fans.length > 0 && (
                  <div>
                    <h3 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-1">
                      <Wind size={14} /> Lüfter
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
                      <Monitor size={14} /> Displays
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

          {/* Systembezogene Treiber (Kernel-Module) */}
          {stats.drivers && stats.drivers.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, delay: 0.45 }}
              className="card"
            >
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Settings className="text-slate-400" />
                Systembezogene Treiber (Kernel-Module)
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

          {/* Module Overview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: 0.5 }}
            className="card"
          >
            <h2 className="text-xl font-bold text-white mb-6">Module Übersicht</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              <ModuleCard
                icon={Shield}
                title="Sicherheit"
                description="Härtung, Firewall, SSH & Updates"
                tooltip={"Empfohlen als Erstes:\n- Firewall (UFW) aktivieren & Regeln pflegen\n- Fail2Ban gegen Login-Angriffe\n- SSH härten (Ports/Keys/Passwortlogin)\n- Automatische Sicherheitsupdates"}
                status="ready"
                page="security"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Users}
                title="Benutzer"
                description="Benutzer, Rollen, Rechte"
                tooltip={"Mehrbenutzer-Setup:\n- Admin/Standardnutzer anlegen\n- Starke Passwörter & Gruppen\n- Optional: SSH-Keys / sudo-Rechte\n- Aufräumen: Benutzer löschen/prüfen"}
                status="ready"
                page="users"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Code}
                title="Entwicklung"
                description="Programmierumgebung & Tools"
                tooltip={"Für Entwicklung auf dem Pi:\n- Python & Node.js\n- C/C++ (gcc/g++)\n- Java (JDK)\n- Git, Docker (optional)\n- Editoren/IDE (VS Code Server/Cursor)\n- Versionsinfos + Links zu Doku/Admin"}
                status="ready"
                page="devenv"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Globe}
                title="Webserver"
                description="Webhosting, Apps & Admin-Panels"
                tooltip={"Webhosting auf dem Pi:\n- Nginx/Apache + (optional) PHP\n- Websites/Apps erkennen & zuordnen\n- CMS (z.B. WordPress/Nextcloud)\n- Admin-Panels (Cockpit/Webmin)\n- Hardening & Zertifikate"}
                status="ready"
                page="webserver"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Mail}
                title="Mailserver"
                description="Mailversand/Empfang (optional)"
                tooltip={"Nur wenn du wirklich Mail auf dem Pi brauchst:\n- Domain/DNS (MX/SPF/DKIM/DMARC) planen\n- TLS/Ports/Freigaben\n- Spam-/Brute-Force-Schutz\n- Externe Verbindung/Relay konfigurieren"}
                status="ready"
                page="mailserver"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Database}
                title="NAS"
                description="Dateifreigaben im Netzwerk"
                tooltip={"Pi als Netzwerkspeicher:\n- Samba (Windows/macOS)\n- NFS (Linux)\n- FTP/SFTP (extern)\n- Shares/Ordnerrechte/Optionen\n- Optional: Gastzugang & Verschlüsselung"}
                status="ready"
                page="nas"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Home}
                title="Hausautomation"
                description="Smart-Home Server"
                tooltip={"Smart Home auf dem Pi:\n- Home Assistant / OpenHAB / Node-RED\n- Ports & Autostart\n- Add-ons/Integrationen\n- Zugriff von außen (sicher!)"}
                status="ready"
                page="homeautomation"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Music}
                title="Musikbox"
                description="Audio/Streaming im Wohnzimmer"
                tooltip={"Pi als Musik-/Media-Station:\n- Mopidy / Volumio / Plex\n- AirPlay/Spotify (optional)\n- Ports & Autostart\n- Web-UI Links & Hinweise"}
                status="ready"
                page="musicbox"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Settings}
                title="Voreinstellungen"
                description="Profile für typische Einsätze"
                tooltip={"Schnell-Setups per Profil:\n- NAS / Webserver / Homeautomation / Musikbox / Lerncomputer\n- Installiert passende Pakete\n- Setzt sinnvolle Defaults\n- Spart Klicks & vermeidet Fehler"}
                status="ready"
                page="presets"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={BookOpen}
                title="Lerncomputer"
                description="Tools & Projekte für Lernen"
                tooltip={"Für Lernen/Schule/Projekte:\n- Scratch, Python/Jupyter\n- GPIO/Robotics Libraries\n- Elektronik-Tools\n- Mathe/Science Tools + Ideen/Links"}
                status="ready"
                page="learning"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={Activity}
                title="Monitoring"
                description="Prometheus/Grafana Überblick"
                tooltip={"Monitoring/Transparenz:\n- Node Exporter, Prometheus, Grafana\n- Dashboards & Health-Checks\n- Links zu UIs\n- Basis für Alerts/Logs"}
                status="ready"
                page="monitoring"
                setCurrentPage={setCurrentPage}
              />
              <ModuleCard
                icon={HardDrive}
                title="Backup & Restore"
                description="Sicherungen & Wiederherstellung"
                tooltip={"Datensicherung:\n- Backups erstellen (voll/inkrementell)\n- Backups auflisten\n- Restore (mit Warnhinweisen)\n- Grundlage für „Pi neu aufsetzen ohne Datenverlust“"}
                status="ready"
                page="backup"
                setCurrentPage={setCurrentPage}
              />
            </div>
          </motion.div>

          {/* Quick Actions / Schnellstart – Kontrast: Anthrazit-Schrift */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.6 }}
            className="bg-gradient-to-r from-sky-600/20 to-blue-600/20 border border-sky-500/30 rounded-lg p-6 backdrop-blur-sm"
          >
            <h2 className="text-xl font-bold text-slate-800 dark:text-white mb-4">Schnellstart</h2>
            <p className="text-slate-700 dark:text-slate-300 mb-4 font-medium">
              Verwenden Sie den Installationsassistenten, um Ihr System in wenigen Schritten zu konfigurieren.
            </p>
            <button 
              onClick={() => setCurrentPage && setCurrentPage('wizard')}
              className="btn-primary"
            >
              → Installation starten
            </button>
          </motion.div>
        </>
      )}

      {/* Loading State */}
      {!stats && !loading && (
        <div className="card flex items-center justify-center p-12">
          <div className="animate-spin-slow">
            <Zap className="text-sky-500" size={48} />
          </div>
          <p className="ml-4 text-slate-300">Lade Systeminfo...</p>
        </div>
      )}
    </motion.div>
  )
}

const ModuleCard = ({ icon: Icon, title, description, tooltip, status, page, setCurrentPage }: any) => (
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
        Bereit
      </span>
    </div>
    <h3 className="font-bold text-white">{title}</h3>
    <p className="text-sm text-slate-400">{description}</p>
  </motion.div>
)

export default Dashboard
