import React, { useEffect, useState } from 'react'
import { Zap, Server, Home, Music, BookOpen, CheckCircle, ArrowRight } from 'lucide-react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
import { fetchApi } from '../api'
import { usePlatform } from '../context/PlatformContext'

const PresetsSetup: React.FC = () => {
  const { pageSubtitleLabel } = usePlatform()
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [availablePresets, setAvailablePresets] = useState<{ id: string; name: string; description: string }[]>([])
  const [selectedConfigPreset, setSelectedConfigPreset] = useState<string>('')

  useEffect(() => {
    const loadPresets = async () => {
      try {
        const response = await fetchApi('/api/presets/list')
        const data = await response.json()
        if (data.status === 'success' && Array.isArray(data.items)) {
          setAvailablePresets(data.items)
        }
      } catch (e) {
        console.error('Fehler beim Laden der Presets', e)
      }
    }
    loadPresets()
  }, [])

  const presets = [
    {
      id: 'nas',
      name: 'NAS Server',
      icon: Server,
      description: 'Netzwerk-Speicher für Dateien, Backups und Media',
      color: 'from-blue-600 to-blue-800',
      features: [
        'Samba (Windows-kompatibel)',
        'NFS (Linux/Unix)',
        'FTP Server',
        'Automatische Backups',
        'RAID Support',
        'Media Streaming',
      ],
      config: {
        nas_type: 'samba',
        enable_samba: true,
        enable_nfs: true,
        enable_ftp: true,
        share_name: 'pi-nas',
        share_path: '/mnt/nas',
      }
    },
    {
      id: 'webserver',
      name: 'Webserver',
      icon: Zap,
      description: 'Vollständiger Webserver mit CMS und SSL',
      color: 'from-green-600 to-green-800',
      features: [
        'Nginx Webserver',
        'PHP Support',
        'SSL/TLS (Let\'s Encrypt)',
        'WordPress/Drupal/Nextcloud',
        'Cockpit Webadmin',
        'Firewall & Sicherheit',
      ],
      config: {
        server_type: 'nginx',
        enable_ssl: true,
        enable_php: true,
        cms_type: 'wordpress',
        install_webadmin: true,
        webadmin_type: 'cockpit',
      }
    },
    {
      id: 'homeautomation',
      name: 'Home Automation',
      icon: Home,
      description: 'Smart Home Server für Hausautomatisierung',
      color: 'from-purple-600 to-purple-800',
      features: [
        'Home Assistant',
        'OpenHAB',
        'Node-RED',
        'MQTT Broker',
        'Zigbee/Zwave Gateway',
        'Automation Rules',
      ],
      config: {
        enable_homeassistant: true,
        enable_openhab: false,
        enable_nodered: true,
        enable_mqtt: true,
      }
    },
    {
      id: 'musicbox',
      name: 'Musikbox',
      icon: Music,
      description: 'Media Server für Musik, Podcasts und Streaming',
      color: 'from-pink-600 to-pink-800',
      features: [
        'Mopidy Music Server',
        'Plex Media Server',
        'AirPlay Support',
        'Spotify Integration',
        'Podcast Support',
        'Multi-Room Audio',
      ],
      config: {
        enable_mopidy: true,
        enable_plex: true,
        enable_airplay: true,
        enable_spotify: false,
      }
    },
    {
      id: 'learning',
      name: 'Lerncomputer',
      icon: BookOpen,
      description: 'Lernumgebung für Kinder ab 14 Jahren',
      color: 'from-orange-600 to-orange-800',
      features: [
        'Scratch Programmierung',
        'Python Lernumgebung',
        'Robotik (Raspberry Pi GPIO)',
        'Elektronik Grundlagen',
        'Mathematik-Tools',
        'Programmier-Tutorials',
      ],
      config: {
        enable_scratch: true,
        enable_python_learning: true,
        enable_robotics: true,
        enable_electronics: true,
        enable_math_tools: true,
      }
    },
  ]

  const applyConfigPreset = async () => {
    if (!selectedConfigPreset) {
      toast.error('Bitte ein Konfigurations-Preset auswählen.')
      return
    }
    setLoading(true)
    try {
      const response = await fetchApi('/api/presets/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ preset: selectedConfigPreset }),
      })
      const data = await response.json()
      if (data.status === 'success') {
        toast.success(`Konfigurations-Preset "${selectedConfigPreset}" wurde angewendet.`)
      } else {
        toast.error(data.message || 'Fehler beim Anwenden des Konfigurations-Presets')
      }
    } catch (e) {
      console.error(e)
      toast.error('Fehler beim Anwenden des Konfigurations-Presets')
    } finally {
      setLoading(false)
    }
  }

  const applyPreset = async (preset: typeof presets[0]) => {
    const sudoPassword = prompt('Sudo-Passwort eingeben (für Installation):')
    if (!sudoPassword) {
      toast.error('Sudo-Passwort erforderlich')
      return
    }

    setLoading(true)
    try {
      // Je nach Preset-Type die entsprechende Konfiguration anwenden
      let endpoint = ''
      let payload: any = {
        sudo_password: sudoPassword,
      }

      switch (preset.id) {
        case 'nas':
          endpoint = '/api/nas/configure'
          payload = { ...payload, ...preset.config }
          break
        case 'webserver':
          endpoint = '/api/webserver/configure'
          payload = { ...payload, config: preset.config }
          break
        case 'homeautomation':
          endpoint = '/api/homeautomation/configure'
          payload = { ...payload, ...preset.config }
          break
        case 'musicbox':
          endpoint = '/api/musicbox/configure'
          payload = { ...payload, ...preset.config }
          break
        case 'learning':
          endpoint = '/api/learning/configure'
          payload = { ...payload, ...preset.config }
          break
      }

      const response = await fetchApi(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      const data = await response.json()

      if (data.status === 'success') {
        toast.success(`${preset.name} Preset erfolgreich angewendet!`)
        if (data.results && data.results.length > 0) {
          data.results.forEach((result: string) => {
            if (result.includes('⚠️') || result.includes('Fehler')) {
              toast.error(result, { duration: 5000 })
            } else {
              toast.success(result, { duration: 3000 })
            }
          })
        }
      } else {
        toast.error(data.message || 'Fehler beim Anwenden des Presets')
      }
    } catch (error) {
      toast.error('Fehler beim Anwenden des Presets')
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8 animate-fade-in page-transition">
      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <Zap className="text-yellow-400" />
            Voreinstellungen & Profile
          </h1>
        </div>
        <p className="text-slate-400">Voreinstellungen – {pageSubtitleLabel}</p>
      </div>

      {/* Globale Konfigurations-Presets (config.json) */}
      <div className="card bg-slate-900/60 border border-slate-700/60 mb-4">
        <h2 className="text-lg font-semibold text-white mb-2">Schnellstart-Presets für die Gesamt-Konfiguration</h2>
        <p className="text-slate-300 text-sm mb-3">
          Wähle ein Profil, um die globale Konfiguration (z. B. Home Assistant, NAS, High Security) mit sinnvollen
          Standardwerten vorzufüllen. Du kannst die Einstellungen später in den Modulen weiter anpassen.
        </p>
        <div className="flex flex-col md:flex-row gap-3 items-start md:items-end">
          <div className="flex-1">
            <select
              className="w-full bg-slate-900 border border-slate-700 text-slate-100 rounded-lg px-3 py-2 text-sm"
              value={selectedConfigPreset}
              onChange={(e) => setSelectedConfigPreset(e.target.value)}
            >
              <option value="">Kein Preset ausgewählt</option>
              {availablePresets.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            {selectedConfigPreset && (
              <p className="text-slate-400 text-xs mt-2">
                {
                  availablePresets.find((p) => p.id === selectedConfigPreset)
                    ?.description
                }
              </p>
            )}
          </div>
          <button
            onClick={applyConfigPreset}
            disabled={loading || !selectedConfigPreset}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white font-semibold text-sm flex items-center gap-2"
          >
            {loading ? 'Wende Preset an…' : 'Konfigurations-Preset anwenden'}
            <ArrowRight size={16} />
          </button>
        </div>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
        {presets.map((preset, index) => {
          const Icon = preset.icon
          return (
            <motion.div
              key={preset.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
              className={`card bg-gradient-to-br ${preset.color} cursor-pointer group relative overflow-hidden`}
              onClick={() => setSelectedPreset(selectedPreset === preset.id ? null : preset.id)}
            >
              {/* Hover Overlay */}
              <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              
              <div className="relative z-10">
                <div className="flex items-start justify-between mb-4">
                  <div className={`p-3 rounded-lg bg-white/10 backdrop-blur-sm`}>
                    <Icon className="text-white" size={32} />
                  </div>
                  {selectedPreset === preset.id && (
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      className="p-1 bg-green-500 rounded-full"
                    >
                      <CheckCircle className="text-white" size={20} />
                    </motion.div>
                  )}
                </div>

                <h3 className="text-2xl font-bold text-white mb-2">{preset.name}</h3>
                <p className="text-white/80 text-sm mb-4">{preset.description}</p>

                {/* Features List */}
                <div className="space-y-2 mb-4">
                  {preset.features.slice(0, 3).map((feature, i) => (
                    <div key={i} className="flex items-center gap-2 text-white/70 text-sm">
                      <div className="w-1.5 h-1.5 bg-white/50 rounded-full" />
                      {feature}
                    </div>
                  ))}
                  {preset.features.length > 3 && (
                    <div className="text-white/60 text-xs">
                      + {preset.features.length - 3} weitere Features
                    </div>
                  )}
                </div>

                {/* Action Button */}
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={(e) => {
                    e.stopPropagation()
                    applyPreset(preset)
                  }}
                  disabled={loading}
                  className="w-full bg-white/20 hover:bg-white/30 text-white font-semibold py-2 px-4 rounded-lg transition-all flex items-center justify-center gap-2 backdrop-blur-sm"
                >
                  {loading ? (
                    <>⏳ Installiere...</>
                  ) : (
                    <>
                      Preset anwenden
                      <ArrowRight size={18} />
                    </>
                  )}
                </motion.button>
              </div>

              {/* Expanded Details */}
              {selectedPreset === preset.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mt-4 pt-4 border-t border-white/20"
                >
                  <h4 className="text-white font-semibold mb-2">Alle Features:</h4>
                  <div className="space-y-1">
                    {preset.features.map((feature, i) => (
                      <div key={i} className="flex items-center gap-2 text-white/80 text-sm">
                        <CheckCircle size={14} className="text-green-300" />
                        {feature}
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </motion.div>
          )
        })}
      </div>

      {/* Info Box */}
      <div className="card bg-gradient-to-r from-blue-900/30 to-purple-900/30 border-blue-500/30">
        <h3 className="text-lg font-bold text-white mb-2">💡 Hinweis</h3>
        <p className="text-slate-300 text-sm">
          Presets konfigurieren Ihr System automatisch mit den empfohlenen Einstellungen. 
          Sie können die Konfiguration später in den einzelnen Modulen anpassen.
        </p>
      </div>
    </div>
  )
}

export default PresetsSetup
