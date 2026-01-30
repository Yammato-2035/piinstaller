import React, { useState, useEffect } from 'react'
import { Activity, TrendingUp, AlertCircle, CheckCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts'
import { fetchApi } from '../api'

const MonitoringDashboard: React.FC = () => {
  const [status, setStatus] = useState<any>(null)
  const [metrics, setMetrics] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

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

  const configureMonitoring = async () => {
    const sudoPassword = prompt('Sudo-Passwort eingeben (für Installation):')
    if (!sudoPassword) {
      toast.error('Sudo-Passwort erforderlich')
      return
    }

    setLoading(true)
    try {
      const response = await fetchApi('/api/monitoring/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          enable_node_exporter: true,
          enable_prometheus: true,
          enable_grafana: true,
          sudo_password: sudoPassword,
        }),
      })
      const data = await response.json()

      if (data.status === 'success') {
        toast.success('Monitoring konfiguriert!')
        if (data.results && data.results.length > 0) {
          data.results.forEach((result: string) => {
            toast.success(result, { duration: 3000 })
          })
        }
        loadStatus()
      } else {
        toast.error(data.message || 'Fehler bei der Konfiguration')
      }
    } catch (error) {
      toast.error('Fehler bei der Konfiguration')
    } finally {
      setLoading(false)
    }
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
        <p className="text-slate-400">
          System-Überwachung mit Prometheus & Grafana
        </p>
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
          <p className="text-slate-400 text-sm">
            {status?.prometheus?.installed ? 'Installiert' : 'Nicht installiert'}
          </p>
          {status?.prometheus?.running && (
            <a href="http://localhost:9090" target="_blank" rel="noopener noreferrer" className="text-sky-400 text-sm mt-2 block hover:underline">
              → Prometheus öffnen
            </a>
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
          <p className="text-slate-400 text-sm">
            {status?.grafana?.installed ? 'Installiert' : 'Nicht installiert'}
          </p>
          {status?.grafana?.running && (
            <a href="http://localhost:3000" target="_blank" rel="noopener noreferrer" className="text-sky-400 text-sm mt-2 block hover:underline">
              → Grafana öffnen (Standard: admin/admin)
            </a>
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
          <p className="text-slate-400 text-sm">
            {status?.node_exporter?.installed ? 'Installiert' : 'Nicht installiert'}
          </p>
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

      {(!status?.prometheus?.installed || !status?.grafana?.installed) && (
        <div className="card bg-gradient-to-r from-green-900/30 to-blue-900/30 border-green-500/30">
          <h3 className="text-lg font-bold text-white mb-2">🚀 Monitoring einrichten</h3>
          <p className="text-slate-300 text-sm mb-4">
            Installieren Sie Prometheus, Grafana und Node Exporter für vollständige System-Überwachung.
          </p>
          <button
            onClick={configureMonitoring}
            disabled={loading}
            className="btn-primary"
          >
            {loading ? '⏳ Installiere...' : 'Monitoring installieren'}
          </button>
        </div>
      )}
    </div>
  )
}

export default MonitoringDashboard
