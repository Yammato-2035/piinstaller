import React, { useState, useEffect } from 'react'
import { Home, Zap, Settings } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'

const HomeAutomationSetup: React.FC = () => {
  const [config, setConfig] = useState({
    automation_type: 'homeassistant',
    enable_homeassistant: false,
    enable_openhab: false,
    enable_nodered: false,
    port: 8123,
  })

  const [loading, setLoading] = useState(false)
  const [automationStatus, setAutomationStatus] = useState<any>(null)

  useEffect(() => {
    loadAutomationStatus()
  }, [])

  const loadAutomationStatus = async () => {
    try {
      const response = await fetchApi('/api/homeautomation/status')
      const data = await response.json()
      setAutomationStatus(data)
    } catch (error) {
      console.error('Fehler beim Laden des Homeautomation-Status:', error)
    }
  }

  const automationTypes = [
    { id: 'homeassistant', label: '🏠 Home Assistant', desc: 'Open-Source Smart Home Platform', port: 8123, docsLink: 'https://www.home-assistant.io/docs/' },
    { id: 'openhab', label: '⚡ OpenHAB', desc: 'Vernetzte Hausautomation', port: 8080, docsLink: 'https://www.openhab.org/docs/' },
    { id: 'nodered', label: '🔌 Node-RED', desc: 'Flow-basierte Programmierung', port: 1880, docsLink: 'https://nodered.org/docs/' },
  ]

  const applyConfig = async () => {
    const sudoPassword = prompt('Sudo-Passwort eingeben:')
    if (!sudoPassword) {
      toast.error('Sudo-Passwort erforderlich')
      return
    }

    setLoading(true)
    try {
      const response = await fetchApi('/api/homeautomation/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...config,
          sudo_password: sudoPassword,
        }),
      })
      const data = await response.json()

      if (data.status === 'success') {
        toast.success('Homeautomation konfiguriert!')
        await loadAutomationStatus()
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
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
          <Home className="text-purple-500" />
          Hausautomatisierung
        </h1>
        <p className="text-slate-400">Richten Sie ein Smart Home System ein</p>
      </div>

      {/* Status */}
      {automationStatus && (
        <div className="card">
          <h2 className="text-2xl font-bold text-white mb-4">Status</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {automationTypes.map((type) => {
              const status = automationStatus[type.id]
              return (
                <div key={type.id} className="p-4 bg-slate-800/50 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-300 font-semibold">{type.label}</span>
                    {status?.installed ? (
                      <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">✓ Installiert</span>
                    ) : (
                      <span className="px-2 py-1 bg-red-900/50 text-white rounded text-xs">Nicht installiert</span>
                    )}
                  </div>
                  {status?.running && (
                    <div className="mt-2">
                      <a
                        href={`http://localhost:${type.port}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sky-400 hover:text-sky-300 text-sm"
                      >
                        🔗 Öffnen (Port {type.port})
                      </a>
                    </div>
                  )}
                  {type.docsLink && (
                    <div className="mt-1">
                      <a
                        href={type.docsLink}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sky-400 hover:text-sky-300 text-sm"
                      >
                        📖 Dokumentation
                      </a>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Automation Type Selection */}
      <div className="card">
        <h2 className="text-2xl font-bold text-white mb-4">System auswählen</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {automationTypes.map((type) => (
            <div
              key={type.id}
              onClick={() => setConfig({ ...config, automation_type: type.id, port: type.port })}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                config.automation_type === type.id
                  ? 'bg-sky-600/20 border-sky-500'
                  : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
              }`}
            >
              <p className="font-bold text-white">{type.label}</p>
              <p className="text-sm text-slate-400 mt-1">{type.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Apply Button */}
      <div className="flex justify-end">
        <button
          onClick={applyConfig}
          disabled={loading}
          className="px-6 py-3 bg-sky-600 hover:bg-sky-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
        >
          {loading ? 'Installieren...' : 'Installation starten'}
        </button>
      </div>
    </div>
  )
}

export default HomeAutomationSetup
