import React, { useEffect, useState } from 'react'
import { fetchApi } from '../api'
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
} from 'lucide-react'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { motion } from 'framer-motion'

interface DashboardProps {
  systemInfo: any
  backendError?: boolean
  setCurrentPage?: (page: string) => void
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
  const [stats, setStats] = useState<any>(null)
  const [securityConfig, setSecurityConfig] = useState<any>(null)
  const [historyData, setHistoryData] = useState<any[]>([])
  const loading = !systemInfo && !backendError

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
        <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-slate-400">Übersicht Ihres Raspberry Pi Systems</p>
      </motion.div>

      {backendError && !stats && (
        <div className="rounded-xl bg-amber-900/30 border border-amber-600/50 p-4 flex items-start gap-3">
          <AlertCircle className="text-amber-400 shrink-0 mt-0.5" size={24} />
          <div>
            <h3 className="font-semibold text-amber-200">Backend nicht erreichbar</h3>
            <p className="text-sm text-amber-200/80 mt-1">
              Dashboard-Daten und Sudo-Passwort-Speicherung funktionieren nur, wenn das Backend läuft.
              Backend starten: <code className="bg-slate-800 px-1 rounded">./start.sh</code> oder <code className="bg-slate-800 px-1 rounded">./start-backend.sh</code> im Projektordner.
              Log-Datei: Einstellungen → Logs → „Logs laden“ (Pfad wird angezeigt).
            </p>
            {setCurrentPage && (
              <button
                onClick={() => setCurrentPage('settings')}
                className="mt-3 text-sm text-sky-400 hover:text-sky-300 underline"
              >
                Einstellungen → Logs öffnen
              </button>
            )}
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
                status="inactive"
                value="Nicht installiert"
                tooltip={"Installiere Tools fürs Entwickeln:\n- Python/Node\n- C/C++ Compiler (gcc/g++)\n- Java (JDK)\n- Git, Docker (optional)\n- Editor/IDE (z.B. VS Code Server/Cursor)"}
              />
              <StatusItem
                label="Webserver"
                status="inactive"
                value="Nicht installiert"
                tooltip={"Richte Hosting ein:\n- Nginx oder Apache\n- PHP (falls nötig)\n- Websites/Apps erkennen & zuordnen\n- Optional: CMS (WordPress/Nextcloud)\n- Admin-Panels (Cockpit/Webmin)"}
              />
            </motion.div>
          </div>

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

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4, delay: 0.6 }}
            className="bg-gradient-to-r from-sky-600/20 to-blue-600/20 border border-sky-500/30 rounded-lg p-6 backdrop-blur-sm"
          >
            <h2 className="text-xl font-bold text-white mb-4">Schnellstart</h2>
            <p className="text-slate-300 mb-4">
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
