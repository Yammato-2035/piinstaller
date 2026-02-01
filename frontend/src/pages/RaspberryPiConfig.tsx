import React, { useEffect, useState } from 'react'
import { Settings, Info, Save, RefreshCw, Power, RotateCcw } from 'lucide-react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
import { fetchApi } from '../api'
import SudoPasswordModal from '../components/SudoPasswordModal'

interface ConfigOption {
  name: string
  description: string
  default: string
  type: 'bool' | 'int' | 'str'
  range?: [number, number]
  options?: (string | number)[]
  unit?: string
  category?: string
  source?: string
}

interface ConfigValue {
  [key: string]: any
}

interface PiInfo {
  model_string?: string
  model?: string
  generation?: number
  ram_mb?: number
  ram_gb?: number
}

interface SystemInfo {
  cpu_model?: string | null
  current_mhz?: number | null
  config_arm_freq?: number | string | null
  config_gpu_mem?: number | string | null
  gpu_info?: string | null
  recommended_mhz?: number | null
  memory_split_hint?: string | null
  over_voltage_hint?: string | null
}

interface CategoryData {
  name: string
  options: Array<[string, ConfigOption]>
}

const RaspberryPiConfig: React.FC = () => {
  const [config, setConfig] = useState<ConfigValue>({})
  const [configOptions, setConfigOptions] = useState<Record<string, ConfigOption>>({})
  const [configCategories, setConfigCategories] = useState<Record<string, CategoryData>>({})
  const [piInfo, setPiInfo] = useState<PiInfo | null>(null)
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [selectedOption, setSelectedOption] = useState<string | null>(null)
  const [showInfoModal, setShowInfoModal] = useState(false)
  const [infoOption, setInfoOption] = useState<ConfigOption | null>(null)
  const [sudoModalOpen, setSudoModalOpen] = useState(false)
  const [pendingAction, setPendingAction] = useState<null | ((sudoPassword: string) => Promise<void>)>(null)

  useEffect(() => {
    loadConfig()
    loadConfigOptions()
    loadSystemInfo()
  }, [])

  const loadSystemInfo = async () => {
    try {
      const r = await fetchApi('/api/raspberry-pi/system-info')
      const d = await r.json()
      if (d.status === 'success' && d.system_info) {
        setSystemInfo(d.system_info)
      } else {
        setSystemInfo(null)
      }
    } catch {
      setSystemInfo(null)
    }
  }

  const loadConfig = async (retryAfterSudo = false) => {
    setLoading(true)
    try {
      const r = await fetchApi('/api/raspberry-pi/config')
      const d = await r.json()
      if (d.status === 'success') {
        setConfig(d.config || {})
        setLoading(false)
        return
      }
      
      // Wenn Sudo-Passwort benötigt wird und noch nicht retry gemacht wurde
      if (d.requires_sudo_password && !retryAfterSudo) {
        setLoading(false)
        // Prüfe zuerst, ob bereits ein Passwort gespeichert ist
        const hasPassword = await hasSavedSudoPassword()
        if (!hasPassword) {
          toast.error('Sudo-Passwort erforderlich zum Lesen der Konfiguration')
          // Versuche sudo-Passwort zu speichern
          await requireSudo(
            {
              title: 'Sudo-Passwort für Config-Lesen',
              subtitle: 'Die config.txt benötigt sudo-Berechtigung zum Lesen.',
              confirmText: 'Bestätigen',
            },
            async () => {
              // Nach dem Speichern erneut versuchen
              await loadConfig(true)
            }
          )
        } else {
          // Passwort ist gespeichert, aber Lesen schlägt trotzdem fehl - erneut versuchen
          await loadConfig(true)
        }
      } else {
        toast.error(d.message || 'Konfiguration konnte nicht geladen werden')
        setLoading(false)
      }
    } catch (e) {
      toast.error('Fehler beim Laden der Konfiguration')
      setLoading(false)
    }
  }

  const loadConfigOptions = async () => {
    try {
      const r = await fetchApi('/api/raspberry-pi/config/options')
      const d = await r.json()
      if (d.status === 'success') {
        setConfigOptions(d.options || {})
        setConfigCategories(d.categories || {})
        setPiInfo(d.pi_info || null)
      }
    } catch (e) {
      // Ignore
    }
  }

  const showOptionInfo = async (key: string) => {
    try {
      const r = await fetchApi(`/api/raspberry-pi/config/option/${encodeURIComponent(key)}`)
      const d = await r.json()
      if (d.status === 'success' && d.option) {
        setInfoOption(d.option)
        setShowInfoModal(true)
      }
    } catch (e) {
      toast.error('Info konnte nicht geladen werden')
    }
  }

  const updateConfigValue = (key: string, value: any) => {
    setConfig((prev) => ({
      ...prev,
      [key]: value,
    }))
  }

  const saveConfig = async () => {
    await requireSudo(
      {
        title: 'Raspberry Pi Konfiguration speichern',
        subtitle: 'Änderungen werden in /boot/firmware/config.txt geschrieben. Ein Neustart ist erforderlich.',
        confirmText: 'Speichern',
      },
      async () => {
        setSaving(true)
        try {
          const r = await fetchApi('/api/raspberry-pi/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config }),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success('Konfiguration gespeichert')
            toast('Neustart erforderlich, damit Änderungen wirksam werden', { duration: 6000, icon: '⚠️' })
            loadConfig()
          } else {
            toast.error(d.message || 'Speichern fehlgeschlagen')
          }
        } catch (e) {
          toast.error('Fehler beim Speichern')
        } finally {
          setSaving(false)
        }
      }
    )
  }

  const hasSavedSudoPassword = async () => {
    try {
      const r = await fetchApi('/api/users/sudo-password/check')
      if (!r.ok) return false
      const d = await r.json()
      return d?.status === 'success' && !!d?.has_password
    } catch {
      return false
    }
  }

  const storeSudoPassword = async (sudoPassword: string) => {
    const resp = await fetchApi('/api/users/sudo-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sudo_password: sudoPassword }),
    })
    const data = await resp.json()
    if (data.status !== 'success') {
      throw new Error(data.message || 'Sudo-Passwort konnte nicht gespeichert werden')
    }
  }

  const requireSudo = async (
    opts: { title: string; subtitle?: string; confirmText?: string },
    action: () => Promise<void>
  ) => {
    if (await hasSavedSudoPassword()) {
      await action()
      return
    }

    setSudoModalOpen(true)
    setPendingAction(() => async (pwd: string) => {
      await storeSudoPassword(pwd)
      await action()
    })
  }

  const renderConfigValue = (key: string, option: ConfigOption) => {
    const currentValue = config[key]
    const defaultValue = option.default

    if (option.type === 'bool') {
      const isOn = currentValue === true || currentValue === 'on' || currentValue === '1'
      return (
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={isOn}
            onChange={(e) => updateConfigValue(key, e.target.checked ? 'on' : 'off')}
            className="w-5 h-5 accent-sky-500"
          />
          <span className="text-sm text-slate-300">{isOn ? 'Aktiviert' : 'Deaktiviert'}</span>
        </label>
      )
    } else if (option.type === 'int') {
      // Konvertiere defaultValue zu einer Zahl, wenn es "auto" oder ein String ist
      let safeDefaultValue: number
      if (typeof defaultValue === 'string' && defaultValue.toLowerCase() === 'auto') {
        safeDefaultValue = option.range?.[0] ?? 0
      } else if (typeof defaultValue === 'number') {
        safeDefaultValue = defaultValue
      } else if (typeof defaultValue === 'string') {
        const parsed = parseInt(defaultValue, 10)
        safeDefaultValue = isNaN(parsed) ? (option.range?.[0] ?? 0) : parsed
      } else {
        safeDefaultValue = option.range?.[0] ?? 0
      }
      
      // Bestimme den Anzeigewert
      let displayValue: number
      if (currentValue !== undefined && currentValue !== null && currentValue !== '') {
        if (typeof currentValue === 'number') {
          displayValue = currentValue
        } else {
          const parsed = parseInt(String(currentValue), 10)
          displayValue = isNaN(parsed) ? safeDefaultValue : parsed
        }
      } else {
        displayValue = safeDefaultValue
      }
      
      return (
        <div className="flex items-center gap-3">
          <input
            type="number"
            value={displayValue}
            onChange={(e) => {
              const val = e.target.value === '' ? safeDefaultValue : parseInt(e.target.value, 10)
              if (!isNaN(val)) {
                updateConfigValue(key, val)
              }
            }}
            min={option.range?.[0]}
            max={option.range?.[1]}
            className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-600"
          />
          {option.unit && <span className="text-sm text-slate-400">{option.unit}</span>}
        </div>
      )
    } else if (option.type === 'str') {
      if (option.options && option.options.length > 0) {
        return (
          <select
            value={currentValue !== undefined ? currentValue : defaultValue}
            onChange={(e) => updateConfigValue(key, e.target.value)}
            className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-600"
          >
            {option.options.map((opt) => (
              <option key={String(opt)} value={String(opt)}>
                {String(opt)}
              </option>
            ))}
          </select>
        )
      } else {
        return (
          <input
            type="text"
            value={currentValue !== undefined ? currentValue : defaultValue}
            onChange={(e) => updateConfigValue(key, e.target.value)}
            className="flex-1 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white focus:outline-none focus:border-sky-600"
          />
        )
      }
    }

    return null
  }

  return (
    <div className="space-y-8 animate-fade-in page-transition">
      <SudoPasswordModal
        open={sudoModalOpen}
        title="Sudo-Passwort erforderlich"
        subtitle="Für diese Aktion werden Administrator-Rechte benötigt."
        confirmText="Bestätigen"
        onCancel={() => {
          setSudoModalOpen(false)
          setPendingAction(null)
        }}
        onConfirm={async (pwd) => {
          try {
            if (!pendingAction) return
            await pendingAction(pwd)
            toast.success('Sudo-Passwort gespeichert (Session)')
            setSudoModalOpen(false)
            setPendingAction(null)
          } catch (e: any) {
            toast.error(e?.message || 'Sudo-Passwort ungültig')
          }
        }}
      />

      {/* Info Modal */}
      {showInfoModal && infoOption && (
        <div className="fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setShowInfoModal(false)} />
          <div className="absolute inset-0 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="card bg-slate-800/95 border border-slate-700 max-w-2xl w-full shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                    <Info className="text-sky-500" />
                    {infoOption.name}
                  </h2>
                </div>
                <button
                  className="px-3 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg"
                  onClick={() => setShowInfoModal(false)}
                >
                  Schließen
                </button>
              </div>
              <div className="space-y-4">
                <div className="p-4 bg-slate-900/40 border border-slate-700 rounded-lg">
                  <div className="text-sm text-slate-300 whitespace-pre-line">{infoOption.description}</div>
                </div>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-slate-400 mb-1">Standardwert</div>
                    <div className="text-white font-semibold">{infoOption.default}</div>
                  </div>
                  <div>
                    <div className="text-slate-400 mb-1">Typ</div>
                    <div className="text-white font-semibold">{infoOption.type}</div>
                  </div>
                  {infoOption.range && (
                    <div className="col-span-2">
                      <div className="text-slate-400 mb-1">Bereich</div>
                      <div className="text-white font-semibold">
                        {infoOption.range[0]} - {infoOption.range[1]} {infoOption.unit || ''}
                      </div>
                    </div>
                  )}
                  {infoOption.source && (
                    <div className="col-span-2">
                      <div className="text-slate-400 mb-1">Quelle</div>
                      <div className="text-white text-xs">{infoOption.source}</div>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      )}

      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <Settings className="text-purple-500" />
            Raspberry Pi Konfiguration
          </h1>
        </div>
        <p className="text-slate-400">
          Konfiguriere Hardware-Einstellungen des Raspberry Pi
          {piInfo && piInfo.model_string && (
            <span className="ml-2 text-sky-400">
              ({piInfo.model_string} - {piInfo.ram_gb ? `${piInfo.ram_gb} GB RAM` : 'RAM unbekannt'})
            </span>
          )}
        </p>
      </div>

      {systemInfo && (
        <div className="card mb-6">
          <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
            <Info className="text-sky-500" />
            CPU & Grafik
          </h2>
          <p className="text-slate-400 text-sm mb-4">
            Die Übersicht zu <strong>jeder CPU</strong> und <strong>jeder gefundenen GPU</strong> (Modell, MHz, Speicher) findest du im <strong>Dashboard</strong>.
          </p>
          {systemInfo.memory_split_hint && (
            <div className="p-3 bg-slate-800/60 border border-slate-600 rounded-lg mb-3">
              <div className="text-slate-400 mb-1 text-sm">Speicheraufteilung (CPU/GPU)</div>
              <div className="text-slate-300 text-xs">{systemInfo.memory_split_hint}</div>
            </div>
          )}
          {systemInfo.over_voltage_hint && (
            <div className="p-3 bg-amber-900/20 border border-amber-700/50 rounded-lg">
              <div className="text-amber-300 mb-1 text-sm">Richtwerte Spannungserhöhung (over_voltage)</div>
              <div className="text-slate-300 text-xs">{systemInfo.over_voltage_hint}</div>
            </div>
          )}
        </div>
      )}

      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Konfigurationsoptionen</h2>
          <div className="flex gap-2">
            <button
              onClick={loadConfig}
              disabled={loading}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg flex items-center gap-2 disabled:opacity-50"
            >
              <RefreshCw size={18} className={loading ? 'animate-spin' : ''} />
              Neu laden
            </button>
            <button
              onClick={saveConfig}
              disabled={saving || loading}
              className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg flex items-center gap-2 disabled:opacity-50"
            >
              <Save size={18} />
              {saving ? 'Speichere...' : 'Speichern'}
            </button>
            <button
              onClick={async () => {
                if (window.confirm('Möchten Sie den Raspberry Pi wirklich neu starten? Alle nicht gespeicherten Änderungen gehen verloren.')) {
                  await requireSudo(
                    {
                      title: 'System neu starten',
                      subtitle: 'Der Raspberry Pi wird neu gestartet. Bitte warten Sie, bis das System wieder hochgefahren ist.',
                      confirmText: 'Neustart',
                    },
                    async () => {
                      try {
                        const r = await fetchApi('/api/system/reboot', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ sudo_password: await getSudoPassword() }),
                        })
                        const d = await r.json()
                        if (d.status === 'success') {
                          toast.success('Neustart gestartet...')
                        } else {
                          toast.error(d.message || 'Neustart fehlgeschlagen')
                        }
                      } catch (e) {
                        toast.error('Fehler beim Neustart')
                      }
                    }
                  )
                }
              }}
              className="px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-lg flex items-center gap-2"
            >
              <Power size={18} />
              Neustart
            </button>
            <button
              onClick={async () => {
                if (window.confirm('ACHTUNG: Möchten Sie die Raspberry Pi Konfiguration wirklich auf Werkseinstellungen zurücksetzen? Alle Änderungen gehen verloren!')) {
                  if (window.confirm('Sind Sie sicher? Diese Aktion kann nicht rückgängig gemacht werden!')) {
                    await requireSudo(
                      {
                        title: 'Auf Werkseinstellungen zurücksetzen',
                        subtitle: 'Die config.txt wird auf Standardwerte zurückgesetzt. Ein Neustart ist erforderlich.',
                        confirmText: 'Zurücksetzen',
                      },
                    async () => {
                      try {
                        const r = await fetchApi('/api/raspberry-pi/config/reset', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ sudo_password: await getSudoPassword() }),
                        })
                        const d = await r.json()
                        if (d.status === 'success') {
                          toast.success('Konfiguration zurückgesetzt')
                          toast('Neustart erforderlich', { duration: 6000, icon: '⚠️' })
                          loadConfig()
                        } else {
                          toast.error(d.message || 'Zurücksetzen fehlgeschlagen')
                        }
                      } catch (e) {
                        toast.error('Fehler beim Zurücksetzen')
                      }
                    }
                    )
                  }
                }
              }}
              className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg flex items-center gap-2"
            >
              <RotateCcw size={18} />
              Reset
            </button>
          </div>
        </div>

        {loading ? (
          <div className="text-center py-8 text-slate-400">Lade Konfiguration...</div>
        ) : Object.keys(configCategories).length === 0 ? (
          <div className="text-center py-8 text-slate-400">Keine kompatiblen Optionen gefunden</div>
        ) : (
          <div className="space-y-6">
            {Object.entries(configCategories).map(([categoryKey, categoryData]) => (
              <motion.div
                key={categoryKey}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-6 bg-slate-800/40 rounded-lg border border-slate-700"
              >
                <h3 className="text-xl font-bold text-white mb-4 pb-2 border-b border-slate-700">
                  {categoryData.name}
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {categoryData.options.map(([key, option]) => (
                    <motion.div
                      key={key}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="p-4 bg-slate-700/30 rounded-lg border border-slate-600"
                    >
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold text-white text-sm">{option.name}</h4>
                            <button
                              onClick={() => showOptionInfo(key)}
                              className="p-1 text-sky-400 hover:text-sky-300 rounded"
                              title="Informationen anzeigen"
                            >
                              <Info size={14} />
                            </button>
                          </div>
                          <p className="text-xs text-slate-400 line-clamp-2 mb-2">{option.description}</p>
                        </div>
                      </div>
                      <div className="mt-2">{renderConfigValue(key, option)}</div>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>

      <div className="card bg-gradient-to-br from-yellow-900/30 to-yellow-900/10 border-yellow-500/50">
        <h3 className="text-lg font-bold text-yellow-300 mb-3">⚠️ Wichtige Hinweise</h3>
        <ul className="space-y-2 text-sm text-slate-300">
          <li>• Änderungen werden in /boot/firmware/config.txt gespeichert</li>
          <li>• Ein Neustart ist erforderlich, damit Änderungen wirksam werden</li>
          <li>• Falsche Konfigurationen können das System unbootbar machen</li>
          <li>• Ein Backup der config.txt wird automatisch erstellt</li>
          <li>• Bei Problemen: config.txt.backup wiederherstellen</li>
        </ul>
      </div>
    </div>
  )
}

export default RaspberryPiConfig
