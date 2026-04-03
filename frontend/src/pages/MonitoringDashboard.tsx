import React, { useState, useEffect } from 'react'
import { Activity, TrendingUp, AlertCircle, CheckCircle, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { fetchApi } from '../api'
import SudoPasswordModal from '../components/SudoPasswordModal'
import PageHeader from '../components/layout/PageHeader'
import { PandaCompanion, PandaRail } from '../components/companions'
import { usePlatform } from '../context/PlatformContext'
import { PageSkeleton } from '../components/Skeleton'
import type { ExperienceLevel } from '../components/Sidebar'

interface MonitoringDashboardProps {
  experienceLevel?: ExperienceLevel
}

const MonitoringDashboard: React.FC<MonitoringDashboardProps> = ({ experienceLevel = 'beginner' }) => {
  const { pageSubtitleLabel, isRaspberryPi } = usePlatform()
  const [status, setStatus] = useState<any>(null)
  const [metrics, setMetrics] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [dataLoading, setDataLoading] = useState(true)
  const [sudoModalOpen, setSudoModalOpen] = useState(false)
  const [uninstallComponent, setUninstallComponent] = useState<string | null>(null)
  const [installSelection, setInstallSelection] = useState({
    enable_node_exporter: true,
    enable_prometheus: true,
    enable_grafana: true,
  })

  useEffect(() => {
    loadStatus()
    if (!isRaspberryPi) {
      loadMetrics()
      const interval = setInterval(loadMetrics, 5000)
      return () => clearInterval(interval)
    }
  }, [isRaspberryPi])

  const loadStatus = async () => {
    try {
      const response = await fetchApi('/api/monitoring/status')
      const data = await response.json()
      setStatus(data)
      // Debug: Status in Konsole ausgeben
      if (process.env.NODE_ENV === 'development') {
        console.log('Monitoring Status:', data)
      }
    } catch (error) {
      console.error('Fehler beim Laden des Status:', error)
    } finally {
      setDataLoading(false)
    }
  }

  const loadMetrics = async () => {
    try {
      const response = await fetchApi('/api/system-info?light=1')
      const data = await response.json()
      
      const newMetric = {
        time: new Date().toLocaleTimeString(),
        cpu: data.cpu?.usage || 0,
        memory: data.memory?.percent || 0,
        disk: data.disk?.percent || 0,
        temperature: data.cpu?.temperature || 0,
      }
      
      setMetrics(prev => [...prev, newMetric].slice(-30))
    } catch (error) {
      console.error('Fehler beim Laden der Metriken:', error)
    }
  }

  const runConfigure = async (sudoPassword: string) => {
    setLoading(true)
    try {
      const response = await fetchApi('/api/monitoring/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...installSelection,
          sudo_password: sudoPassword,
        }),
      })
      const data = await response.json()

      if (data.status === 'success') {
        setSudoModalOpen(false)
        try {
          localStorage.setItem('pi-installer-new-monitoring', '1')
        } catch { /* ignore */ }
        toast.success('Monitoring konfiguriert!')
        if (data.results && data.results.length > 0) {
          data.results.forEach((result: string) => {
            toast.success(result, { duration: 3000 })
          })
        }
        loadStatus()
      } else {
        if (data.requires_sudo_password) {
          setSudoModalOpen(true)
        } else {
          toast.error(data.message || 'Fehler bei der Konfiguration')
        }
      }
    } catch (error) {
      toast.error('Fehler bei der Konfiguration')
    } finally {
      setLoading(false)
    }
  }

  const configureMonitoring = async () => {
    const atLeastOne = installSelection.enable_node_exporter || installSelection.enable_prometheus || installSelection.enable_grafana
    if (!atLeastOne) {
      toast.error('Bitte mindestens eine Komponente auswählen.')
      return
    }
    setLoading(true)
    try {
      const response = await fetchApi('/api/monitoring/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(installSelection),
      })
      const data = await response.json()

      if (data.status === 'success') {
        try {
          localStorage.setItem('pi-installer-new-monitoring', '1')
        } catch { /* ignore */ }
        toast.success('Monitoring konfiguriert!')
        if (data.results && data.results.length > 0) {
          data.results.forEach((result: string) => {
            toast.success(result, { duration: 3000 })
          })
        }
        loadStatus()
      } else {
        if (data.requires_sudo_password) {
          setSudoModalOpen(true)
        } else {
          toast.error(data.message || 'Fehler bei der Konfiguration')
        }
      }
    } catch (error) {
      toast.error('Fehler bei der Konfiguration')
    } finally {
      setLoading(false)
    }
  }

  const onSudoConfirm = async (password: string) => {
    if (uninstallComponent) {
      await runUninstall(uninstallComponent, password)
    } else {
      await runConfigure(password)
    }
  }

  const runUninstall = async (component: string, sudoPassword: string) => {
    setLoading(true)
    try {
      const response = await fetchApi('/api/monitoring/uninstall', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ component, sudo_password: sudoPassword }),
      })
      const data = await response.json()
      if (data.status === 'success') {
        setSudoModalOpen(false)
        setUninstallComponent(null)
        toast.success(data.results?.[0] || `${component} entfernt`)
        loadStatus()
      } else {
        if (data.requires_sudo_password) {
          setSudoModalOpen(true)
        } else {
          toast.error(data.message || 'Entfernen fehlgeschlagen')
        }
      }
    } catch {
      toast.error('Entfernen fehlgeschlagen')
    } finally {
      setLoading(false)
    }
  }

  const handleUninstall = (component: string) => {
    setUninstallComponent(component)
    setSudoModalOpen(true)
  }

  if (dataLoading) {
    return <PageSkeleton cards={3} />
  }

  return (
    <div className="space-y-8 animate-fade-in page-transition">
      <PageHeader
        visualStyle="tech-panel"
        tone="monitoring"
        title="Monitoring Dashboard"
        subtitle={`Behalte Systemstatus, Auslastung und Dienste einfach im Blick – ${pageSubtitleLabel}.`}
      />
      {experienceLevel === 'beginner' && (
        <PandaRail>
          <PandaCompanion
            type="debug"
            size="lg"
            surface="dark"
            frame={false}
            showTrafficLight
            trafficLightPosition="bottom-right"
            status="info"
            title="Monitoring-Begleiter"
            subtitle="Ich helfe dir, Last und Dienste Schritt für Schritt zu verstehen."
          />
        </PandaRail>
      )}

      <div className="grid md:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card break-words"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white">Prometheus</h3>
            {status?.prometheus?.installed ? (
              status?.prometheus?.running ? (
                <CheckCircle className="text-green-500 status-icon active" size={24} />
              ) : (
                <CheckCircle className="text-green-500" size={24} />
              )
            ) : (
              <AlertCircle className="text-yellow-500" size={24} />
            )}
          </div>
          <p className="text-sm flex items-center gap-2">
            {status?.prometheus?.installed ? (
              <>
                <CheckCircle className="text-green-500 shrink-0" size={18} />
                <span className="text-green-400 font-medium">Installiert</span>
                {status?.prometheus?.running && <span className="text-green-400 text-xs">(läuft)</span>}
              </>
            ) : (
              <span className="text-slate-400">Nicht installiert</span>
            )}
          </p>
          {status?.prometheus?.running && (
            <a href="http://localhost:9090" target="_blank" rel="noopener noreferrer" className="text-sky-400 text-sm mt-2 block hover:underline">
              → Prometheus öffnen
            </a>
          )}
          {status?.prometheus?.installed && (
            <button
              type="button"
              onClick={() => handleUninstall('prometheus')}
              disabled={loading}
              className="mt-2 flex items-center gap-1.5 text-red-400 hover:text-red-300 text-sm"
            >
              <Trash2 size={16} /> Entfernen
            </button>
          )}
          {status?.prometheus?.installed && (
            <div className="mt-4 pt-3 border-t border-slate-600" style={{ wordBreak: 'break-word', overflowWrap: 'anywhere', maxWidth: '100%' }}>
              <p className="text-xs font-semibold text-slate-300 mb-2">Beispiel: Was Prometheus kann</p>
              <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside" style={{ wordBreak: 'break-word', overflowWrap: 'anywhere', maxWidth: '100%' }}>
                <li style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>Metriken sammeln (z. B. Node Exporter auf Port 9100)</li>
                <li style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>PromQL-Abfragen: <code className="bg-slate-700 px-1 rounded break-all">node_cpu_seconds_total</code>, <code className="bg-slate-700 px-1 rounded break-all">rate(node_network_receive_bytes_total[5m])</code></li>
                <li style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>Targets prüfen unter <a href="http://localhost:9090/targets" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline break-all">localhost:9090/targets</a></li>
                <li style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>Grafana als Frontend: Prometheus als Datenquelle hinzufügen (URL <code className="bg-slate-700 px-1 rounded break-all">http://localhost:9090</code>)</li>
                <li style={{ wordBreak: 'break-word', overflowWrap: 'anywhere' }}>Beispiel-Abfragen: CPU-Auslastung <code className="bg-slate-700 px-1 rounded break-all">{'100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'}</code>, Speicher <code className="bg-slate-700 px-1 rounded break-all">node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes</code></li>
              </ul>
              <a href="https://prometheus.io/docs/prometheus/latest/querying/basics/" target="_blank" rel="noopener noreferrer" className="text-sky-400 text-xs mt-2 inline-block hover:underline">PromQL-Dokumentation</a>
            </div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card break-words"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white">Grafana</h3>
            {status?.grafana?.installed ? (
              status?.grafana?.running ? (
                <CheckCircle className="text-green-500 status-icon active" size={24} />
              ) : (
                <CheckCircle className="text-green-500" size={24} />
              )
            ) : (
              <AlertCircle className="text-yellow-500" size={24} />
            )}
          </div>
          <p className="text-sm flex items-center gap-2">
            {status?.grafana?.installed ? (
              <>
                <CheckCircle className="text-green-500 shrink-0" size={18} />
                <span className="text-green-400 font-medium">Installiert</span>
                {status?.grafana?.running && <span className="text-green-400 text-xs">(läuft)</span>}
              </>
            ) : (
              <span className="text-slate-400">Nicht installiert</span>
            )}
          </p>
          {status?.grafana?.running && (
            <a href="http://localhost:3000" target="_blank" rel="noopener noreferrer" className="text-sky-400 text-sm mt-2 block hover:underline">
              → Grafana öffnen (Standard: admin/admin)
            </a>
          )}
          {status?.grafana?.installed && (
            <button
              type="button"
              onClick={() => handleUninstall('grafana')}
              disabled={loading}
              className="mt-2 flex items-center gap-1.5 text-red-400 hover:text-red-300 text-sm"
            >
              <Trash2 size={16} /> Entfernen
            </button>
          )}
          {status?.grafana?.installed && (
            <div className="mt-4 pt-3 border-t border-slate-600">
              <p className="text-xs font-semibold text-slate-300 mb-2">Was Grafana kann</p>
              <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside break-words">
                <li>Dashboards erstellen: CPU, RAM, Disk, Netzwerk, Temperatur visualisieren</li>
                <li>Prometheus als Datenquelle: In Grafana → Configuration → Data Sources → Prometheus (URL: <code className="bg-slate-700 px-1 rounded break-all">http://localhost:9090</code>)</li>
                <li>Vorgefertigte Dashboards: z. B. "Node Exporter Full" (ID 1860) importieren</li>
                <li>Alerts konfigurieren: Warnungen bei hoher CPU, niedrigem Speicher, etc.</li>
                <li>Grafiken exportieren: PNG/PDF für Reports</li>
              </ul>
            </div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card break-words"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white">Node Exporter</h3>
            {status?.node_exporter?.installed ? (
              status?.node_exporter?.running ? (
                <CheckCircle className="text-green-500 status-icon active" size={24} />
              ) : (
                <CheckCircle className="text-green-500" size={24} />
              )
            ) : (
              <AlertCircle className="text-yellow-500" size={24} />
            )}
          </div>
          <p className="text-sm flex items-center gap-2">
            {status?.node_exporter?.installed ? (
              <>
                <CheckCircle className="text-green-500 shrink-0" size={18} />
                <span className="text-green-400 font-medium">Installiert</span>
                {status?.node_exporter?.running && <span className="text-green-400 text-xs">(läuft)</span>}
              </>
            ) : (
              <span className="text-slate-400">Nicht installiert</span>
            )}
          </p>
          {status?.node_exporter?.running && (
            <a href="http://localhost:9100/metrics" target="_blank" rel="noopener noreferrer" className="text-sky-400 text-sm mt-2 block hover:underline">
              → Metriken anzeigen (Port 9100)
            </a>
          )}
          {status?.node_exporter?.installed && (
            <button
              type="button"
              onClick={() => handleUninstall('node_exporter')}
              disabled={loading}
              className="mt-2 flex items-center gap-1.5 text-red-400 hover:text-red-300 text-sm"
            >
              <Trash2 size={16} /> Entfernen
            </button>
          )}
          {status?.node_exporter?.installed && (
            <div className="mt-4 pt-3 border-t border-slate-600">
              <p className="text-xs font-semibold text-slate-300 mb-2">Was Node Exporter kann</p>
              <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside break-words">
                <li>System-Metriken sammeln: CPU, RAM, Disk, Netzwerk, Temperatur, Boot-Zeit</li>
                <li>Metriken unter <a href="http://localhost:9100/metrics" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline break-all">localhost:9100/metrics</a> abrufbar</li>
                <li>Prometheus sammelt diese Metriken automatisch (wenn konfiguriert)</li>
                <li>Beispiel-Metriken: <code className="bg-slate-700 px-1 rounded break-all">node_cpu_seconds_total</code> (CPU-Zeit), <code className="bg-slate-700 px-1 rounded break-all">node_memory_MemTotal_bytes</code> (RAM), <code className="bg-slate-700 px-1 rounded break-all">node_filesystem_avail_bytes</code> (freier Speicher)</li>
                <li>Grafana-Dashboards nutzen diese Metriken für Visualisierungen</li>
              </ul>
            </div>
          )}
        </motion.div>
      </div>

      {isRaspberryPi && metrics.length === 0 && (
        <p className="text-slate-400 text-sm mb-4">Live-Auslastung nur im Dashboard – hier werden Prometheus, Grafana und Node Exporter verwaltet.</p>
      )}
      {metrics.length > 0 && (
        <div className="grid md:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="card"
          >
            <h3 className="text-xl font-bold text-white mb-4">System Auslastung</h3>
            <ResponsiveContainer width="100%" height={250}>
              <AreaChart data={metrics}>
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
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            className="card"
          >
            <h3 className="text-xl font-bold text-white mb-4">Temperatur & Disk</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={metrics}>
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
                <Line type="monotone" dataKey="temperature" stroke="#f59e0b" strokeWidth={2} name="Temperatur °C" />
                <Line type="monotone" dataKey="disk" stroke="#ef4444" strokeWidth={2} name="Disk %" />
              </LineChart>
            </ResponsiveContainer>
          </motion.div>
        </div>
      )}

      {(!status?.prometheus?.installed || !status?.grafana?.installed || !status?.node_exporter?.installed) && (
        <div className="card bg-gradient-to-r from-green-900/30 to-blue-900/30 border-green-500/30">
          <h3 className="text-lg font-bold text-white mb-2">🚀 Monitoring einrichten</h3>
          <p className="text-slate-300 text-sm mb-4">
            Wählen Sie die gewünschten Komponenten – mindestens eine. Für die Installation wird ggf. ein Sudo-Passwort abgefragt.
          </p>
          <div className="space-y-3 mb-4">
            <label className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg cursor-pointer">
              <input
                type="checkbox"
                checked={installSelection.enable_node_exporter}
                onChange={(e) => setInstallSelection((s) => ({ ...s, enable_node_exporter: e.target.checked }))}
                className="w-5 h-5 accent-sky-600"
              />
              <span className="text-slate-300">Node Exporter</span>
              <span className="text-slate-500 text-sm">(System-Metriken)</span>
            </label>
            <label className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg cursor-pointer">
              <input
                type="checkbox"
                checked={installSelection.enable_prometheus}
                onChange={(e) => setInstallSelection((s) => ({ ...s, enable_prometheus: e.target.checked }))}
                className="w-5 h-5 accent-sky-600"
              />
              <span className="text-slate-300">Prometheus</span>
              <span className="text-slate-500 text-sm">(Metriken sammeln & abfragen)</span>
            </label>
            <label className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-lg cursor-pointer">
              <input
                type="checkbox"
                checked={installSelection.enable_grafana}
                onChange={(e) => setInstallSelection((s) => ({ ...s, enable_grafana: e.target.checked }))}
                className="w-5 h-5 accent-sky-600"
              />
              <span className="text-slate-300">Grafana</span>
              <span className="text-slate-500 text-sm">(Dashboards & Visualisierung)</span>
            </label>
          </div>
          <button
            onClick={configureMonitoring}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? '⏳ Installiere...' : 'Ausgewählte Komponenten installieren'}
          </button>
        </div>
      )}

      {/* Laufende Beispiele */}
      <div className="mt-8">
        <h2 className="text-xl font-bold text-white mb-4">Laufende Beispiele</h2>
        <div className="grid md:grid-cols-3 gap-6">
          {/* Prometheus Beispiel */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card"
          >
            <h3 className="font-bold text-white mb-3">Prometheus Query-Beispiel</h3>
            <div className="bg-slate-800 rounded-lg p-4 mb-3">
              <code className="text-xs text-green-400 block mb-2"># CPU-Auslastung berechnen</code>
              <code className="text-xs text-slate-300 block break-all">
                100 - (avg by(instance) (rate(node_cpu_seconds_total{'{'}mode="idle"{'}'}[5m])) * 100)
              </code>
            </div>
            <p className="text-xs text-slate-400 mb-2">Ergebnis (wenn Node Exporter läuft):</p>
            <div className="bg-slate-800 rounded-lg p-3">
              <code className="text-xs text-sky-400">
                {`{instance="localhost:9100"} => 23.45`}
              </code>
            </div>
            <a 
              href="http://localhost:9090/graph?g0.expr=100%20-%20(avg%20by(instance)%20(rate(node_cpu_seconds_total%7Bmode%3D%22idle%22%7D%5B5m%5D))%20*%20100)" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-sky-400 text-xs mt-2 inline-block hover:underline"
            >
              → In Prometheus ausführen
            </a>
          </motion.div>

          {/* Grafana Beispiel */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="card"
          >
            <h3 className="font-bold text-white mb-3">Grafana Dashboard-Beispiel</h3>
            <div className="bg-slate-800 rounded-lg p-4 mb-3">
              <code className="text-xs text-green-400 block mb-2"># Dashboard importieren</code>
              <code className="text-xs text-slate-300 block">
                Dashboard ID: <span className="text-sky-400">1860</span>
              </code>
              <code className="text-xs text-slate-300 block mt-1">
                Name: Node Exporter Full
              </code>
            </div>
            <p className="text-xs text-slate-400 mb-2">Enthält Visualisierungen für:</p>
            <ul className="text-xs text-slate-400 list-disc list-inside space-y-1 mb-3">
              <li>CPU-Auslastung (alle Kerne)</li>
              <li>RAM-Verbrauch</li>
              <li>Disk I/O</li>
              <li>Netzwerk-Traffic</li>
              <li>System-Load</li>
            </ul>
            <a 
              href="http://localhost:3000/dashboard/import" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-sky-400 text-xs mt-2 inline-block hover:underline"
            >
              → Dashboard importieren
            </a>
          </motion.div>

          {/* Node Exporter Beispiel */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="card"
          >
            <h3 className="font-bold text-white mb-3">Node Exporter Metriken-Beispiel</h3>
            <div className="bg-slate-800 rounded-lg p-4 mb-3">
              <code className="text-xs text-green-400 block mb-2"># Beispiel-Metriken (localhost:9100/metrics)</code>
              <code className="text-xs text-slate-300 block break-all">
                <span className="text-sky-400">node_cpu_seconds_total</span>{'{'}cpu="0",mode="user"{'}'} 1234.56
              </code>
              <code className="text-xs text-slate-300 block break-all mt-1">
                <span className="text-sky-400">node_memory_MemTotal_bytes</span> 8589934592
              </code>
              <code className="text-xs text-slate-300 block break-all mt-1">
                <span className="text-sky-400">node_filesystem_avail_bytes</span>{'{'}device="/dev/sda1",fstype="ext4",mountpoint="/"{'}'} 1234567890
              </code>
            </div>
            <p className="text-xs text-slate-400 mb-2">Prometheus sammelt diese Metriken alle 15 Sekunden</p>
            <a 
              href="http://localhost:9100/metrics" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-sky-400 text-xs mt-2 inline-block hover:underline"
            >
              → Alle Metriken anzeigen
            </a>
          </motion.div>
        </div>

        {/* Workflow-Beispiel */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card mt-6"
        >
          <h3 className="font-bold text-white mb-4">Workflow-Beispiel: Monitoring einrichten</h3>
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-sky-600 text-white flex items-center justify-center text-xs font-bold">1</div>
              <div>
                <p className="text-sm text-white font-medium">Node Exporter starten</p>
                <p className="text-xs text-slate-400 mt-1">Sammelt System-Metriken auf Port 9100</p>
                <code className="text-xs text-slate-500 block mt-1 bg-slate-800 px-2 py-1 rounded">curl http://localhost:9100/metrics</code>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-sky-600 text-white flex items-center justify-center text-xs font-bold">2</div>
              <div>
                <p className="text-sm text-white font-medium">Prometheus konfigurieren</p>
                <p className="text-xs text-slate-400 mt-1">Prometheus sammelt Metriken von Node Exporter</p>
                <code className="text-xs text-slate-500 block mt-1 bg-slate-800 px-2 py-1 rounded">scrape_configs: - job_name: 'node' static_configs: - targets: ['localhost:9100']</code>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-sky-600 text-white flex items-center justify-center text-xs font-bold">3</div>
              <div>
                <p className="text-sm text-white font-medium">Grafana Dashboard erstellen</p>
                <p className="text-xs text-slate-400 mt-1">Prometheus als Datenquelle hinzufügen (http://localhost:9090)</p>
                <p className="text-xs text-slate-400 mt-1">Dashboard "Node Exporter Full" (ID 1860) importieren</p>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full bg-green-600 text-white flex items-center justify-center text-xs font-bold">✓</div>
              <div>
                <p className="text-sm text-white font-medium">Fertig: Live-Monitoring läuft</p>
                <p className="text-xs text-slate-400 mt-1">CPU, RAM, Disk, Netzwerk werden in Echtzeit visualisiert</p>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      <SudoPasswordModal
        open={sudoModalOpen}
        title="Sudo-Passwort erforderlich"
        subtitle={uninstallComponent
          ? `Zum Entfernen von ${uninstallComponent === 'node_exporter' ? 'Node Exporter' : uninstallComponent === 'grafana' ? 'Grafana' : 'Prometheus'} werden Administrator-Rechte benötigt.`
          : 'Für die Monitoring-Installation werden Administrator-Rechte benötigt.'}
        confirmText={uninstallComponent ? 'Komponente entfernen' : 'Installation starten'}
        onCancel={() => { setSudoModalOpen(false); setUninstallComponent(null) }}
        onConfirm={onSudoConfirm}
      />
    </div>
  )
}

export default MonitoringDashboard
