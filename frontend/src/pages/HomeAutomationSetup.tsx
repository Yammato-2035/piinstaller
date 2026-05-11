import React, { useState, useEffect, useMemo } from 'react'
import { Home, Zap, Search, Trash2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'
import SudoPasswordModal from '../components/SudoPasswordModal'
import { usePlatform } from '../context/PlatformContext'
import { PandaCompanion, PandaRail, type PandaStatus } from '../components/companions'

type DiscoveredAutomationDevice = {
  name: string
  kind: string
  group: string
  function: string
  ip: string
  hostname?: string
  ports?: number[]
  source?: string[]
  hint?: string
}

type DiscoveryResult = {
  found: DiscoveredAutomationDevice[]
  groups: Record<string, DiscoveredAutomationDevice[]>
  stats?: {
    total_found?: number
    scanned_candidates?: number
    neighbor_candidates?: number
    fritzbox_ip?: string | null
  }
}

const HomeAutomationSetup: React.FC = () => {
  const { pageSubtitleLabel } = usePlatform()
  const [config, setConfig] = useState({
    automation_type: 'homeassistant',
    enable_homeassistant: false,
    enable_openhab: false,
    enable_nodered: false,
    port: 8123,
  })

  const [loading, setLoading] = useState(false)
  const [searching, setSearching] = useState(false)
  const [assimilated, setAssimilated] = useState(false)
  const [discoveryResult, setDiscoveryResult] = useState<DiscoveryResult | null>(null)
  const [automationStatus, setAutomationStatus] = useState<any>(null)
  const [uninstallComponent, setUninstallComponent] = useState<string | null>(null)
  const [sudoModalOpen, setSudoModalOpen] = useState(false)

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
    { id: 'homeassistant', label: '🏠 Home Assistant', desc: 'Open-Source Smart Home Platform', port: 8123, docsLink: 'https://www.home-assistant.io/docs/', providers: 'Zigbee, Z-Wave, MQTT, Philips Hue, IKEA, viele Hersteller' },
    { id: 'openhab', label: '⚡ OpenHAB', desc: 'Vernetzte Hausautomation', port: 8080, docsLink: 'https://www.openhab.org/docs/', providers: 'Z-Wave, Zigbee, KNX, MQTT, Bindings für viele Geräte' },
    { id: 'nodered', label: '🔌 Node-RED', desc: 'Flow-basierte Programmierung', port: 1880, docsLink: 'https://nodered.org/docs/', providers: 'MQTT, HTTP, GPIO (Pi), oft mit Home Assistant kombiniert' },
  ]

  const startSearch = async () => {
    setSearching(true)
    setAssimilated(false)
    setDiscoveryResult(null)
    try {
      const response = await fetchApi('/api/homeautomation/search', { method: 'POST' })
      const data = await response.json().catch(() => ({}))
      setDiscoveryResult({
        found: data.found || [],
        groups: data.groups || {},
        stats: data.stats || {},
      })
      setAssimilated(true)
      if (data.found != null) {
        toast.success(`Suche abgeschlossen. Gefunden: ${data.found.length || 0} Elemente.`)
      }
    } catch {
      setAssimilated(true)
      toast.success('Suche abgeschlossen.')
    } finally {
      setSearching(false)
    }
  }

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

  const homeAutomationCompanionStatus = useMemo((): PandaStatus => {
    if (searching) return 'info'
    if (discoveryResult && (discoveryResult.found?.length ?? 0) > 0) return 'success'
    const st = automationStatus as Record<string, { installed?: boolean; running?: boolean }> | null
    if (!st) return 'info'
    const keys = ['homeassistant', 'home_assistant', 'openhab', 'nodered', 'node_red'] as const
    for (const k of keys) {
      const svc = st[k]
      if (svc?.running) return 'success'
      if (svc?.installed) return 'warning'
    }
    return 'info'
  }, [automationStatus, discoveryResult, searching])

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <Home className="text-purple-500" />
            Hausautomatisierung
          </h1>
        </div>
        <p className="text-slate-400">Hausautomatisierung – {pageSubtitleLabel}</p>
      </div>

      <PandaRail>
        <PandaCompanion
          type="start"
          size="sm"
          surface="dark"
          frame={false}
          showTrafficLight
          trafficLightPosition="bottom-right"
          status={homeAutomationCompanionStatus}
          title="Smart-Home-Begleiter"
          subtitle="Suche, Installation und Status – Ampel: grün wenn Geräte gefunden oder ein Dienst läuft, gelb wenn installiert aber nicht aktiv."
        />
      </PandaRail>

      {/* Suche nach Elementen – roter Start-Button + Assimilation-Text */}
      <div className="card flex flex-col items-center py-8">
        <button
          type="button"
          onClick={startSearch}
          disabled={searching}
          className="w-24 h-24 rounded-full bg-red-600 hover:bg-red-500 disabled:opacity-60 shadow-lg shadow-red-600/40 flex items-center justify-center transition-all hover:scale-105 disabled:scale-100"
          title="Suche nach Geräten und Integrationen im Haus"
        >
          <Search className="text-white" size={36} />
        </button>
        <p className="mt-3 text-slate-300 font-medium">Suche nach Elementen im Haus</p>
        <p className="text-sm text-slate-400 mt-1">Geräte, Integrationen, Kompatibilität prüfen</p>
        {searching && (
          <div className="mt-6 text-center">
            <p className="text-xl font-bold text-red-400">Das Haus wird assimiliert!</p>
            <p className="text-slate-400 mt-1">Widerstand ist zwecklos.</p>
            <div className="mt-4 h-2 w-48 bg-slate-700 rounded overflow-hidden mx-auto">
              <div className="h-full bg-red-500 animate-pulse rounded" style={{ width: '60%' }} />
            </div>
          </div>
        )}
        {assimilated && !searching && (
          <p className="mt-4 text-green-400 font-semibold">Haus assimiliert!</p>
        )}
      </div>

      {discoveryResult && (
        <div className="card bg-slate-800/60 border border-slate-600">
          <h2 className="text-xl font-bold text-slate-100 mb-2">Gefundene Geräte & Dienste</h2>
          <p className="text-sm text-slate-400 mb-4">
            {discoveryResult.stats?.total_found ?? discoveryResult.found.length} Einträge erkannt
            {discoveryResult.stats?.fritzbox_ip ? ` · Fritzbox/Gateway: ${discoveryResult.stats.fritzbox_ip}` : ''}
          </p>

          {Object.keys(discoveryResult.groups).length === 0 ? (
            <p className="text-slate-400 text-sm">Keine Geräte gefunden. Tipp: Geräte einschalten und Suche erneut starten.</p>
          ) : (
            <div className="space-y-4">
              {Object.entries(discoveryResult.groups).map(([group, devices]) => (
                <div key={group} className="rounded-lg border border-slate-700 bg-slate-900/40">
                  <div className="px-4 py-2 border-b border-slate-700 flex items-center justify-between">
                    <span className="text-slate-200 font-semibold">{group}</span>
                    <span className="text-xs text-slate-400">{devices.length} Einträge</span>
                  </div>
                  <div className="p-3 space-y-2">
                    {devices.map((device, index) => (
                      <div key={`${device.kind}-${device.ip || index}`} className="rounded-md bg-slate-800/60 p-3">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-slate-100 font-medium">{device.name}</span>
                          {device.ip && <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-200">{device.ip}</span>}
                          {device.ports && device.ports.length > 0 && (
                            <span className="text-xs px-2 py-0.5 rounded bg-sky-900/40 text-sky-300">
                              Ports: {device.ports.join(', ')}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-slate-400 mt-1">
                          Funktion: {device.function}
                          {device.hostname ? ` · Hostname: ${device.hostname}` : ''}
                        </p>
                        {device.source && device.source.length > 0 && (
                          <p className="text-xs text-slate-500 mt-1">Quelle: {device.source.join(', ')}</p>
                        )}
                        {device.hint && <p className="text-xs text-amber-300 mt-1">{device.hint}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Empfehlung & Systembeschreibung – Kontrast: dunkle Schrift auf neutralem Hintergrund */}
      <div className="card bg-slate-800/60 border border-slate-600">
        <h2 className="text-xl font-bold text-slate-100 mb-3">Empfehlung & Systeme</h2>
        <p className="text-slate-400 text-sm mb-4">
          Welches System passt? Home Assistant eignet sich für Einsteiger und große Ökosysteme (viele Hersteller).
          OpenHAB ist mächtig und bindet KNX/Z-Wave stark ein. Node-RED ist ideal für Automatisierungs-Logik und lässt sich mit Home Assistant kombinieren.
        </p>
        <ul className="space-y-3 text-sm">
          {automationTypes.map((t) => (
            <li key={t.id} className="p-3 bg-slate-700/50 rounded-lg">
              <span className="font-semibold text-slate-200">{t.label}</span>
              <p className="text-slate-400 mt-0.5">{t.desc}</p>
              <p className="text-slate-500 text-xs mt-1">Kompatibel mit: {t.providers}</p>
            </li>
          ))}
        </ul>
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
                  {status?.installed && (
                    <button
                      type="button"
                      onClick={() => { setUninstallComponent(type.id); setSudoModalOpen(true); }}
                      className="mt-2 flex items-center gap-1.5 text-red-400 hover:text-red-300 text-sm"
                    >
                      <Trash2 size={14} /> Deinstallieren
                    </button>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      <SudoPasswordModal
        isOpen={sudoModalOpen}
        onClose={() => { setSudoModalOpen(false); setUninstallComponent(null); }}
        onSubmit={async (sudoPassword: string) => {
          if (!uninstallComponent) return
          setLoading(true)
          try {
            const response = await fetchApi('/api/homeautomation/uninstall', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ component: uninstallComponent, sudo_password: sudoPassword }),
            })
            const data = await response.json()
            if (data.status === 'success') {
              toast.success(data.message || 'Deinstallation durchgeführt.')
              setSudoModalOpen(false)
              setUninstallComponent(null)
              loadAutomationStatus()
            } else {
              if (data.requires_sudo_password) return
              toast.error(data.message || 'Deinstallation fehlgeschlagen.')
            }
          } catch {
            toast.error('Deinstallation fehlgeschlagen.')
          } finally {
            setLoading(false)
          }
        }}
      />

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
