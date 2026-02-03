import React, { useState, useEffect } from 'react'
import { Activity, TrendingUp, AlertCircle, CheckCircle, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { fetchApi } from '../api'
import SudoPasswordModal from '../components/SudoPasswordModal'
import { usePlatform } from '../context/PlatformContext'
import { PageSkeleton } from '../components/Skeleton'

const MonitoringDashboard: React.FC = () => {
  const { pageSubtitleLabel } = usePlatform()
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
    loadMetrics()
    
    const interval = setInterval(() => {
      loadMetrics()
    }, 5000)
    
    return () => clearInterval(interval)
  }, [])

  const loadStatus = async () => {
    try {
      const response = await fetchApi('/api/monitoring/status')
      const data = await response.json()
      setStatus(data)
    } catch (error) {
      console.error('Fehler beim Laden des Status:', error)
    } finally {
      setDataLoading(false)
    }
  }

  const loadMetrics = async () => {
    try {
      const response = await fetchApi('/api/system-info')
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
      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <Activity className="text-green-500" />
            Monitoring Dashboard
          </h1>
        </div>
        <p className="text-slate-400">Monitoring – {pageSubtitleLabel}</p>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white">Prometheus</h3>
            {status?.prometheus?.running ? (
              <CheckCircle className="text-green-500 status-icon active" size={24} />
            ) : (
              <AlertCircle className="text-yellow-500" size={24} />
            )}
          </div>
          <p className="text-sm flex items-center gap-2">
            {status?.prometheus?.installed ? (
              <>
                <CheckCircle className="text-green-500 shrink-0" size={18} />
                <span className="text-green-400 font-medium">Installiert</span>
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
            <div className="mt-4 pt-3 border-t border-slate-600">
              <p className="text-xs font-semibold text-slate-300 mb-2">Beispiel: Was Prometheus kann</p>
              <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
                <li>Metriken sammeln (z. B. Node Exporter auf Port 9100)</li>
                <li>PromQL-Abfragen: <code className="bg-slate-700 px-1 rounded">node_cpu_seconds_total</code>, <code className="bg-slate-700 px-1 rounded">rate(node_network_receive_bytes_total[5m])</code></li>
                <li>Targets prüfen unter <a href="http://localhost:9090/targets" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">localhost:9090/targets</a></li>
                <li>Grafana als Frontend: Prometheus als Datenquelle hinzufügen (URL <code className="bg-slate-700 px-1 rounded">http://localhost:9090</code>)</li>
              </ul>
              <a href="https://prometheus.io/docs/prometheus/latest/querying/basics/" target="_blank" rel="noopener noreferrer" className="text-sky-400 text-xs mt-2 inline-block hover:underline">PromQL-Dokumentation</a>
            </div>
          )}
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white">Grafana</h3>
            {status?.grafana?.running ? (
              <CheckCircle className="text-green-500 status-icon active" size={24} />
            ) : (
              <AlertCircle className="text-yellow-500" size={24} />
            )}
          </div>
          <p className="text-sm flex items-center gap-2">
            {status?.grafana?.installed ? (
              <>
                <CheckCircle className="text-green-500 shrink-0" size={18} />
                <span className="text-green-400 font-medium">Installiert</span>
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
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card"
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-white">Node Exporter</h3>
            {status?.node_exporter?.running ? (
              <CheckCircle className="text-green-500 status-icon active" size={24} />
            ) : (
              <AlertCircle className="text-yellow-500" size={24} />
            )}
          </div>
          <p className="text-sm flex items-center gap-2">
            {status?.node_exporter?.installed ? (
              <>
                <CheckCircle className="text-green-500 shrink-0" size={18} />
                <span className="text-green-400 font-medium">Installiert</span>
              </>
            ) : (
              <span className="text-slate-400">Nicht installiert</span>
            )}
          </p>
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
        </motion.div>
      </div>

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
