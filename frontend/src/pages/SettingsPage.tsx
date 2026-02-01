import React, { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
import { Cloud, RefreshCw, CheckCircle, XCircle, Settings } from 'lucide-react'
import { fetchApi } from '../api'
import SudoPasswordModal from '../components/SudoPasswordModal'
import { usePlatform } from '../context/PlatformContext'

type GeneralSubTab = 'init' | 'network' | 'basic'

interface SettingsPageProps {
  setCurrentPage?: (page: string) => void
}

const SettingsPage: React.FC<SettingsPageProps> = ({ setCurrentPage }) => {
  const { isRaspberryPi } = usePlatform()
  const [activeTab, setActiveTab] = useState<'general' | 'cloud' | 'logs'>('general')
  const [generalSubTab, setGeneralSubTab] = useState<GeneralSubTab>('init')
  const [initStatus, setInitStatus] = useState<any>(null)
  const [settings, setSettings] = useState<any>(null)
  const [logs, setLogs] = useState<string>('')
  const [logPath, setLogPath] = useState<string | null>(null)
  const [loadingLogs, setLoadingLogs] = useState(false)
  const [saving, setSaving] = useState(false)
  const [backupSettings, setBackupSettings] = useState<any>(null)
  const [cloudQuota, setCloudQuota] = useState<any>(null)
  const [loadingQuota, setLoadingQuota] = useState(false)
  const [testingCloud, setTestingCloud] = useState(false)
  const [sudoModalOpen, setSudoModalOpen] = useState(false)
  const [pendingAction, setPendingAction] = useState<null | ((sudoPassword: string) => Promise<void>)>(null)
  const [networkInfo, setNetworkInfo] = useState<{
    status?: 'success' | 'error'
    message?: string
    ips?: string[]
    hostname?: string
    frontend_port?: number
    backend_port?: number
  } | null>(null)
  const [loadingNetwork, setLoadingNetwork] = useState(false)

  const loadAll = async () => {
    try {
      const [a, b, c] = await Promise.all([
        fetchApi('/api/init/status'),
        fetchApi('/api/settings'),
        fetchApi('/api/backup/settings'),
      ])
      const ia = await a.json()
      const sb = await b.json()
      const bc = await c.json()
      if (ia?.status === 'success') setInitStatus(ia)
      if (sb?.status === 'success') setSettings(sb.settings)
      if (bc?.status === 'success') setBackupSettings(bc.settings)
    } catch {
      // ignore
    }
  }

  const loadNetworkInfo = async () => {
    setLoadingNetwork(true)
    setNetworkInfo(null)
    try {
      const r = await fetchApi('/api/system/network')
      const d = await r.json()
      if (d?.status === 'success') {
        setNetworkInfo({
          status: 'success',
          ips: d.ips ?? [],
          hostname: d.hostname,
          frontend_port: d.frontend_port ?? 3001,
          backend_port: d.backend_port ?? 8000,
        })
      } else {
        setNetworkInfo({
          status: 'error',
          message: d?.message ?? 'Netzwerk-Info konnte nicht geladen werden.',
        })
      }
    } catch (e) {
      setNetworkInfo({
        status: 'error',
        message: 'Backend nicht erreichbar.',
      })
    } finally {
      setLoadingNetwork(false)
    }
  }

  const loadCloudQuota = async () => {
    if (!backupSettings?.cloud?.enabled) {
      setCloudQuota(null)
      return
    }
    setLoadingQuota(true)
    try {
      const r = await fetchApi('/api/backup/cloud/quota')
      const d = await r.json()
      if (d.status === 'success') {
        setCloudQuota(d.quota)
      }
    } catch {
      // ignore
    } finally {
      setLoadingQuota(false)
    }
  }

  useEffect(() => {
    loadAll()
  }, [])

  useEffect(() => {
    if (activeTab === 'general' && generalSubTab === 'network') loadNetworkInfo()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab, generalSubTab])

  useEffect(() => {
    if (activeTab !== 'logs') return
    let cancelled = false
    fetchApi('/api/logs/path')
      .then((r) => r.json())
      .then((d) => { if (!cancelled && d?.status === 'success' && d?.path) setLogPath(d.path) })
      .catch(() => {})
    return () => { cancelled = true }
  }, [activeTab])

  useEffect(() => {
    if (backupSettings?.cloud?.enabled) {
      loadCloudQuota()
    } else {
      setCloudQuota(null)
    }
  }, [backupSettings?.cloud?.enabled])

  const loadLogs = async () => {
    setLoadingLogs(true)
    try {
      const [pathRes, tailRes] = await Promise.all([
        fetchApi('/api/logs/path'),
        fetchApi('/api/logs/tail?lines=250'),
      ])
      const pathData = await pathRes.json()
      const tailData = await tailRes.json()
      if (pathData?.status === 'success' && pathData?.path) {
        setLogPath(pathData.path)
      }
      if (tailData.status === 'success') {
        setLogs(String(tailData.content || ''))
      } else {
        toast.error(tailData.message || 'Logs konnten nicht geladen werden')
      }
    } catch {
      toast.error('Logs konnten nicht geladen werden (Backend nicht erreichbar)')
    } finally {
      setLoadingLogs(false)
    }
  }

  const save = async () => {
    if (!settings) return
    return saveWith(settings)
  }

  const saveWith = async (s: typeof settings) => {
    if (!s) return
    setSaving(true)
    try {
      const r = await fetchApi('/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ settings: s }),
      })
      const d = await r.json()
      if (d.status === 'success') {
        toast.success('Einstellungen gespeichert')
        setSettings(d.settings)
      } else {
        toast.error(d.message || 'Speichern fehlgeschlagen')
      }
    } catch {
      toast.error('Speichern fehlgeschlagen (Backend nicht erreichbar)')
    } finally {
      setSaving(false)
    }
  }

  const saveBackupSettings = async () => {
    if (!backupSettings) return
    await requireSudo(
      {
        title: 'Cloud-Einstellungen speichern',
        subtitle: 'Speichert Cloud-Konfiguration für Backups.',
        confirmText: 'Speichern',
      },
      async () => {
        try {
          const r = await fetchApi('/api/backup/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ settings: backupSettings }),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success('Cloud-Einstellungen gespeichert')
            setBackupSettings(d.settings)
            if (d.settings.cloud?.enabled) {
              await loadCloudQuota()
            }
          } else {
            toast.error(d.message || 'Speichern fehlgeschlagen')
          }
        } catch {
          toast.error('Speichern fehlgeschlagen')
        }
      }
    )
  }

  const testCloud = async () => {
    if (!backupSettings?.cloud?.webdav_url || !backupSettings?.cloud?.username || !backupSettings?.cloud?.password) {
      toast.error('Bitte WebDAV URL + Username + Passwort ausfüllen')
      return
    }
    setTestingCloud(true)
    try {
      const r = await fetchApi('/api/backup/cloud/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          webdav_url: backupSettings.cloud.webdav_url,
          username: backupSettings.cloud.username,
          password: backupSettings.cloud.password,
        }),
      })
      const d = await r.json()
      if (d.status === 'success' && d.ok) {
        toast.success(`Cloud-Verbindung OK (HTTP ${d.http_code})`)
        await loadCloudQuota()
      } else {
        toast.error(d.message || `Cloud-Test fehlgeschlagen (HTTP ${d.http_code ?? '—'})`, { duration: 12000 })
      }
    } catch {
      toast.error('Cloud-Test fehlgeschlagen (Backend nicht erreichbar)')
    } finally {
      setTestingCloud(false)
    }
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
    action: (pwd?: string) => Promise<void>
  ) => {
    if (await hasSavedSudoPassword()) {
      await action()
      return
    }

    setSudoModalOpen(true)
    setPendingAction(() => async (pwd: string) => {
      await storeSudoPassword(pwd)
      await action(pwd)
    })
  }

  const [rebooting, setRebooting] = useState(false)
  const triggerReboot = async () => {
    if (!window.confirm('Möchten Sie das System wirklich neu starten? Bitte speichern Sie zuvor alle Änderungen.')) return
    await requireSudo(
      {
        title: 'System neu starten',
        subtitle: 'Das System wird neu gestartet. Die Anwendung ist danach kurz nicht erreichbar.',
        confirmText: 'Neustart',
      },
      async (pwd?: string) => {
        setRebooting(true)
        try {
          const body: Record<string, string> = {}
          if (pwd) body.sudo_password = pwd
          const r = await fetchApi('/api/system/reboot', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success('Neustart gestartet…')
          } else {
            toast.error(d.message || 'Neustart fehlgeschlagen')
          }
        } catch {
          toast.error('Neustart fehlgeschlagen (Backend nicht erreichbar)')
        } finally {
          setRebooting(false)
        }
      }
    )
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

      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <Settings className="text-sky-500" />
            Einstellungen
          </h1>
        </div>
        <p className="text-slate-400">Hier kannst du grundlegende Einstellungen verwalten und den Initialisierungsstatus prüfen.</p>
      </div>

      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card">
        {/* Hauptmenü */}
        <div className="flex flex-wrap gap-2 border-b border-slate-700 pb-3 mb-3">
          <button
            onClick={() => setActiveTab('general')}
            className={`px-4 py-2 font-medium transition-all relative ${
              activeTab === 'general'
                ? 'text-sky-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Allgemein
            {activeTab === 'general' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400"
                initial={false}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            )}
          </button>
          <button
            onClick={() => setActiveTab('cloud')}
            className={`px-4 py-2 font-medium transition-all relative ${
              activeTab === 'cloud'
                ? 'text-sky-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Cloud-Backup
            {activeTab === 'cloud' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400"
                initial={false}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            )}
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={`px-4 py-2 font-medium transition-all relative ${
              activeTab === 'logs'
                ? 'text-sky-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Logs
            {activeTab === 'logs' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400"
                initial={false}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            )}
          </button>
        </div>
        {/* Submenü Allgemein (nur bei aktivem Tab) */}
        {activeTab === 'general' && (
          <div className="flex flex-wrap gap-2 border-b border-slate-700 pb-3 mb-3">
            <button
              onClick={() => setGeneralSubTab('init')}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                generalSubTab === 'init'
                  ? 'bg-sky-600 text-white'
                  : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              Initialisierung
            </button>
            <button
              onClick={() => setGeneralSubTab('network')}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                generalSubTab === 'network'
                  ? 'bg-sky-600 text-white'
                  : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              Frontend-Netzwerk-Zugriff
            </button>
            <button
              onClick={() => setGeneralSubTab('basic')}
              className={`px-3 py-1.5 rounded text-sm font-medium transition-colors ${
                generalSubTab === 'basic'
                  ? 'bg-sky-600 text-white'
                  : 'bg-slate-700/60 text-slate-300 hover:bg-slate-700 hover:text-white'
              }`}
            >
              Grundlegende Einstellungen
            </button>
          </div>
        )}
      </motion.div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        transition={{ duration: 0.2 }}
      >
        {activeTab === 'general' && (
          <div className="min-h-[280px]">
            {generalSubTab === 'init' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="card">
          <h3 className="text-lg font-bold text-white mb-3">Initialisierung</h3>
          {!initStatus ? (
            <div className="text-sm text-slate-400">Lade…</div>
          ) : (
            <div className="space-y-2 text-sm text-slate-200">
              <div>
                <span className="text-slate-400">Device-ID:</span> <span className="font-semibold">{initStatus.device_id}</span>
              </div>
              <div>
                <span className="text-slate-400">Config:</span> <span className="font-mono text-xs">{initStatus.config_path}</span>
              </div>
              <div>
                <span className="text-slate-400">Erster Start:</span>{' '}
                <span className={initStatus.first_run ? 'text-yellow-300 font-semibold' : 'text-green-300 font-semibold'}>
                  {initStatus.first_run ? 'ja' : 'nein'}
                </span>
              </div>
              <div>
                <span className="text-slate-400">Device Match:</span>{' '}
                <span className={initStatus.matched_device ? 'text-green-300 font-semibold' : 'text-yellow-300 font-semibold'}>
                  {initStatus.matched_device ? 'ja' : 'nein'}
                </span>
              </div>
              <button onClick={loadAll} className="mt-2 px-3 py-2 bg-slate-700/60 hover:bg-slate-700 text-white rounded-lg">
                Neu laden
              </button>
            </div>
          )}
        </motion.div>
            )}

            {generalSubTab === 'network' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="card">
          <h3 className="text-lg font-bold text-white mb-3">Frontend-Netzwerk-Zugriff</h3>
          {settings && (
            <div className="space-y-3 p-3 bg-slate-800/50 rounded-lg border border-slate-600 mb-4">
              <div className="flex flex-wrap items-center gap-3 gap-y-2">
                <label className="flex items-center gap-2 cursor-pointer shrink-0">
                  <input
                    type="checkbox"
                    checked={!!settings?.network?.remote_access_disabled}
                    onChange={(e) => {
                      const checked = e.target.checked
                      const next = { ...settings, network: { ...(settings?.network || {}), remote_access_disabled: checked } }
                      setSettings(next)
                      saveWith(next)
                    }}
                    disabled={saving}
                    className="w-5 h-5 shrink-0 accent-amber-500"
                  />
                  <span className="text-white whitespace-nowrap">Remote Zugriff deaktivieren</span>
                  {saving && <span className="text-sm text-slate-400">…</span>}
                </label>
                <button
                  type="button"
                  onClick={triggerReboot}
                  disabled={rebooting}
                  className="ml-auto px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg font-medium text-sm shrink-0 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {rebooting ? '…' : 'Neustart'}
                </button>
              </div>
              <p className="text-xs text-slate-500">
                Wirkt erst nach Neustart (start.sh). Nur Neustart – ändert kein Boot-Ziel (Desktop/Kommandozeile).{' '}
                {isRaspberryPi && setCurrentPage ? (
                  <>Boot-Ziel z. B. in der{' '}
                    <button
                      type="button"
                      onClick={() => setCurrentPage('raspberry-pi-config')}
                      className="text-sky-400 hover:text-sky-300 hover:underline focus:outline-none focus:ring-1 focus:ring-sky-400 rounded"
                    >
                      Raspberry Pi Config
                    </button>
                    {' '}oder per </>
                ) : isRaspberryPi && !setCurrentPage ? (
                  <>Boot-Ziel z. B. in der <span className="text-slate-400">Raspberry Pi Config</span> oder per </>
                ) : null}
                <code className="text-slate-400">systemctl set-default</code> einstellen.
              </p>
            </div>
          )}
          {loadingNetwork ? (
            <div className="text-sm text-slate-400">Lade…</div>
          ) : networkInfo?.status === 'error' ? (
            <div className="space-y-3 text-sm">
              <div className="p-3 bg-red-900/20 rounded-lg border border-red-800/50 text-red-200">
                {networkInfo.message ?? 'Netzwerk-Info konnte nicht geladen werden.'}
              </div>
              <button
                onClick={loadNetworkInfo}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg"
              >
                Erneut laden
              </button>
            </div>
          ) : !networkInfo ? (
            <div className="text-sm text-slate-400">Lade…</div>
          ) : (
            <div className="space-y-3 text-sm">
              <div className="p-3 bg-slate-800/50 rounded-lg border border-slate-600">
                <div className="text-xs text-slate-400 mb-2">Frontend erreichbar von jedem Rechner im Netzwerk:</div>
                {networkInfo?.ips && networkInfo.ips.length > 0 ? (
                  <div className="space-y-1">
                    {networkInfo.ips.map((ip, idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        <code className="px-2 py-1 bg-slate-900/70 rounded text-sky-300 font-mono text-xs">
                          http://{ip}:{networkInfo.frontend_port ?? 3001}
                        </code>
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(`http://${ip}:${networkInfo.frontend_port ?? 3001}`)
                            toast.success('URL in Zwischenablage kopiert')
                          }}
                          className="text-xs text-slate-400 hover:text-sky-400"
                        >
                          Kopieren
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-slate-400">
                    Keine IP-Adressen gefunden. Prüfen Sie, ob der Rechner per LAN/WLAN verbunden ist.
                    <span className="block mt-1 text-amber-400/90">0.0.0.0 ist keine erreichbare Adresse.</span>
                  </div>
                )}
                {networkInfo?.hostname && networkInfo.hostname !== 'unknown' && (
                  <div className="mt-2 text-xs text-slate-500">
                    Hostname: <span className="text-slate-300">{networkInfo.hostname}</span>
                  </div>
                )}
                <div className="mt-3 text-xs text-slate-500">
                  <div>Backend API: Port {networkInfo?.backend_port ?? 8000}</div>
                  <div className="mt-1">
                    Auf anderen Geräten im Heimnetz die angezeigte Adresse (z. B. http://192.168.1.x:3001) im Browser öffnen.
                    <span className="block mt-1 text-amber-400/90">Nicht 0.0.0.0 verwenden – das ist keine erreichbare Adresse.</span>
                    {settings?.network?.remote_access_disabled && (
                      <span className="block mt-1 text-amber-400/90">Remote-Zugriff ist deaktiviert – von anderen Geräten nicht erreichbar.</span>
                    )}
                  </div>
                </div>
              </div>
              <button
                onClick={loadNetworkInfo}
                className="text-xs text-slate-400 hover:text-sky-400"
              >
                Aktualisieren
              </button>

              <div className="mt-4 p-3 bg-amber-900/20 rounded-lg border border-amber-700/50">
                <div className="text-sm font-semibold text-amber-200 mb-2">Firewall & Erreichbarkeit</div>
                <p className="text-xs text-slate-300 mb-2">
                  Wenn Sie weder die Website (Port 80) noch das Frontend (Port 3001) von anderen Geräten erreichen, blockiert oft die Firewall (UFW) die Ports.
                </p>
                <p className="text-xs text-slate-400 mb-2">Auf dem Pi im Terminal ausführen:</p>
                <code className="block text-xs text-sky-300 font-mono bg-slate-900/70 p-2 rounded mb-2 overflow-x-auto">
                  sudo ufw allow 3001/tcp<br />
                  sudo ufw allow 8000/tcp<br />
                  sudo ufw allow 80/tcp
                </code>
                <p className="text-xs text-slate-400">
                  Oder: <code className="text-sky-300">sudo ./scripts/open-firewall-pi-installer.sh</code> im Projektordner.
                </p>
                <p className="text-xs text-slate-400 mt-2">
                  Prüfen: <code className="text-sky-300">ss -tlnp | grep -E &apos;3001|8000&apos;</code> sollte <code className="text-sky-300">0.0.0.0</code> anzeigen.
                </p>
              </div>
            </div>
          )}
        </motion.div>
            )}

            {generalSubTab === 'basic' && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="card">
          <h3 className="text-lg font-bold text-white mb-3">Grundlegende Einstellungen</h3>
          {!settings ? (
            <div className="text-sm text-slate-400">Lade…</div>
          ) : (
            <div className="space-y-4 text-sm">
              <div>
                <div className="text-xs text-slate-400 mb-1">Sprache</div>
                <select
                  value={settings.ui?.language ?? 'de'}
                  onChange={(e) => setSettings((s: any) => ({ ...s, ui: { ...(s.ui || {}), language: e.target.value } }))}
                  className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="de">Deutsch</option>
                  <option value="en">English</option>
                </select>
              </div>

              <div>
                <div className="text-xs text-slate-400 mb-1">Standard Backup-Ziel</div>
                <input
                  value={settings.backup?.default_dir ?? '/mnt/backups'}
                  onChange={(e) => setSettings((s: any) => ({ ...s, backup: { ...(s.backup || {}), default_dir: e.target.value } }))}
                  className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  placeholder="/mnt/backups"
                />
                <div className="text-xs text-slate-500 mt-1">Muss unter /mnt, /media, /run/media oder /home liegen.</div>
              </div>

              <div>
                <div className="text-xs text-slate-400 mb-1">Logging Level</div>
                <select
                  value={settings.logging?.level ?? 'INFO'}
                  onChange={(e) => setSettings((s: any) => ({ ...s, logging: { ...(s.logging || {}), level: e.target.value } }))}
                  className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                >
                  <option value="DEBUG">DEBUG</option>
                  <option value="INFO">INFO</option>
                  <option value="WARNING">WARNING</option>
                  <option value="ERROR">ERROR</option>
                </select>
              </div>

              <div>
                <div className="text-xs text-slate-400 mb-1">Log-Aufbewahrungsdauer (Tage)</div>
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={settings.logging?.retention_days ?? 30}
                  onChange={(e) => setSettings((s: any) => ({ ...s, logging: { ...(s.logging || {}), retention_days: parseInt(e.target.value) || 30 } }))}
                  className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                  placeholder="30"
                />
                <div className="text-xs text-slate-500 mt-1">
                  Logs werden nach dieser Anzahl von Tagen automatisch gelöscht (Standard: 30 Tage)
                </div>
              </div>

              <button
                onClick={save}
                disabled={saving}
                className="w-full px-3 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg disabled:opacity-50"
              >
                {saving ? '⏳ Speichere…' : 'Speichern'}
              </button>
            </div>
          )}
        </motion.div>
            )}
          </div>
        )}

        {activeTab === 'cloud' && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Cloud className="text-sky-400" />
            Cloud-Backup Einstellungen
          </h3>
          <button
            onClick={loadCloudQuota}
            disabled={loadingQuota || !backupSettings?.cloud?.enabled}
            className="px-3 py-2 bg-slate-700/60 hover:bg-slate-700 text-white rounded-lg text-sm disabled:opacity-50 flex items-center gap-2"
          >
            <RefreshCw size={16} className={loadingQuota ? 'animate-spin' : ''} />
            Quota aktualisieren
          </button>
        </div>

        {!backupSettings ? (
          <div className="text-sm text-slate-400">Lade Cloud-Einstellungen…</div>
        ) : (
          <div className="space-y-4">
            {/* Provider-Auswahl */}
            <div>
              <div className="text-xs text-slate-400 mb-2">Cloud-Anbieter</div>
              <select
                value={backupSettings.cloud?.provider || 'seafile_webdav'}
                onChange={(e) =>
                  setBackupSettings((s: any) => ({
                    ...s,
                    cloud: { ...(s.cloud || {}), provider: e.target.value },
                  }))
                }
                className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
              >
                <option value="seafile_webdav">WebDAV (Seafile)</option>
                <option value="webdav">WebDAV (Allgemein)</option>
                <option value="nextcloud_webdav">WebDAV (Nextcloud)</option>
                <option value="s3">Amazon S3</option>
                <option value="s3_compatible">S3-kompatibel (MinIO, etc.)</option>
                <option value="google_cloud">Google Cloud Storage</option>
                <option value="azure">Azure Blob Storage</option>
              </select>
            </div>

            {/* Aktivierung */}
            <label className="flex items-center gap-3 p-3 bg-slate-900/40 border border-slate-700 rounded-lg cursor-pointer">
              <input
                type="checkbox"
                checked={!!backupSettings.cloud?.enabled}
                onChange={(e) =>
                  setBackupSettings((s: any) => ({
                    ...s,
                    cloud: { ...(s.cloud || {}), enabled: e.target.checked },
                  }))
                }
                className="w-5 h-5 accent-sky-500"
              />
              <div>
                <div className="font-semibold text-white">Cloud-Upload aktivieren</div>
                <div className="text-xs text-slate-400">Backups werden automatisch in die Cloud hochgeladen</div>
              </div>
            </label>

            {/* WebDAV Einstellungen */}
            {backupSettings.cloud?.provider?.includes('webdav') && (
              <div className="space-y-3 p-4 bg-slate-900/40 border border-slate-700 rounded-lg">
                <div>
                  <div className="text-xs text-slate-400 mb-1">WebDAV URL</div>
                  <input
                    value={backupSettings.cloud?.webdav_url ?? ''}
                    onChange={(e) =>
                      setBackupSettings((s: any) => ({
                        ...s,
                        cloud: { ...(s.cloud || {}), webdav_url: e.target.value },
                      }))
                    }
                    className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    placeholder="https://.../seafdav/MeineBibliothek/Backups"
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Benutzername</div>
                    <input
                      value={backupSettings.cloud?.username ?? ''}
                      onChange={(e) =>
                        setBackupSettings((s: any) => ({
                          ...s,
                          cloud: { ...(s.cloud || {}), username: e.target.value },
                        }))
                      }
                      className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      placeholder="Benutzername"
                    />
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Passwort/Token</div>
                    <input
                      type="password"
                      value={backupSettings.cloud?.password ?? ''}
                      onChange={(e) =>
                        setBackupSettings((s: any) => ({
                          ...s,
                          cloud: { ...(s.cloud || {}), password: e.target.value },
                        }))
                      }
                      className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      placeholder="Passwort/Token"
                    />
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400 mb-1">Remote Unterordner (optional)</div>
                  <input
                    value={backupSettings.cloud?.remote_path ?? ''}
                    onChange={(e) =>
                      setBackupSettings((s: any) => ({
                        ...s,
                        cloud: { ...(s.cloud || {}), remote_path: e.target.value },
                      }))
                    }
                    className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    placeholder="Backups"
                  />
                </div>
              </div>
            )}

            {/* S3 Einstellungen */}
            {backupSettings.cloud?.provider === 's3' || backupSettings.cloud?.provider === 's3_compatible' ? (
              <div className="space-y-3 p-4 bg-slate-900/40 border border-slate-700 rounded-lg">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Bucket</div>
                    <input
                      value={backupSettings.cloud?.bucket ?? ''}
                      onChange={(e) =>
                        setBackupSettings((s: any) => ({
                          ...s,
                          cloud: { ...(s.cloud || {}), bucket: e.target.value },
                        }))
                      }
                      className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      placeholder="my-backup-bucket"
                    />
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Region</div>
                    <input
                      value={backupSettings.cloud?.region ?? 'us-east-1'}
                      onChange={(e) =>
                        setBackupSettings((s: any) => ({
                          ...s,
                          cloud: { ...(s.cloud || {}), region: e.target.value },
                        }))
                      }
                      className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      placeholder="us-east-1"
                    />
                  </div>
                </div>
                {backupSettings.cloud?.provider === 's3_compatible' && (
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Endpoint URL (für S3-kompatibel)</div>
                    <input
                      value={backupSettings.cloud?.endpoint_url ?? ''}
                      onChange={(e) =>
                        setBackupSettings((s: any) => ({
                          ...s,
                          cloud: { ...(s.cloud || {}), endpoint_url: e.target.value },
                        }))
                      }
                      className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      placeholder="https://minio.example.com"
                    />
                  </div>
                )}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Access Key ID</div>
                    <input
                      type="password"
                      value={backupSettings.cloud?.access_key_id ?? ''}
                      onChange={(e) =>
                        setBackupSettings((s: any) => ({
                          ...s,
                          cloud: { ...(s.cloud || {}), access_key_id: e.target.value },
                        }))
                      }
                      className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      placeholder="Access Key"
                    />
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Secret Access Key</div>
                    <input
                      type="password"
                      value={backupSettings.cloud?.secret_access_key ?? ''}
                      onChange={(e) =>
                        setBackupSettings((s: any) => ({
                          ...s,
                          cloud: { ...(s.cloud || {}), secret_access_key: e.target.value },
                        }))
                      }
                      className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      placeholder="Secret Key"
                    />
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400 mb-1">Key Prefix (optional)</div>
                  <input
                    value={backupSettings.cloud?.key_prefix ?? ''}
                    onChange={(e) =>
                      setBackupSettings((s: any) => ({
                        ...s,
                        cloud: { ...(s.cloud || {}), key_prefix: e.target.value },
                      }))
                    }
                    className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    placeholder="backups/"
                  />
                </div>
              </div>
            ) : null}

            {/* Google Cloud Storage */}
            {backupSettings.cloud?.provider === 'google_cloud' && (
              <div className="space-y-3 p-4 bg-slate-900/40 border border-slate-700 rounded-lg">
                <div>
                  <div className="text-xs text-slate-400 mb-1">Bucket</div>
                  <input
                    value={backupSettings.cloud?.bucket ?? ''}
                    onChange={(e) =>
                      setBackupSettings((s: any) => ({
                        ...s,
                        cloud: { ...(s.cloud || {}), bucket: e.target.value },
                      }))
                    }
                    className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    placeholder="my-backup-bucket"
                  />
                </div>
                <div>
                  <div className="text-xs text-slate-400 mb-1">Service Account JSON Datei (Pfad)</div>
                  <input
                    value={backupSettings.cloud?.service_account_file ?? ''}
                    onChange={(e) =>
                      setBackupSettings((s: any) => ({
                        ...s,
                        cloud: { ...(s.cloud || {}), service_account_file: e.target.value },
                      }))
                    }
                    className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    placeholder="/path/to/service-account.json"
                  />
                </div>
                <div>
                  <div className="text-xs text-slate-400 mb-1">Key Prefix (optional)</div>
                  <input
                    value={backupSettings.cloud?.key_prefix ?? ''}
                    onChange={(e) =>
                      setBackupSettings((s: any) => ({
                        ...s,
                        cloud: { ...(s.cloud || {}), key_prefix: e.target.value },
                      }))
                    }
                    className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    placeholder="backups/"
                  />
                </div>
              </div>
            )}

            {/* Azure Blob Storage */}
            {backupSettings.cloud?.provider === 'azure' && (
              <div className="space-y-3 p-4 bg-slate-900/40 border border-slate-700 rounded-lg">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Account Name</div>
                    <input
                      value={backupSettings.cloud?.account_name ?? ''}
                      onChange={(e) =>
                        setBackupSettings((s: any) => ({
                          ...s,
                          cloud: { ...(s.cloud || {}), account_name: e.target.value },
                        }))
                      }
                      className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      placeholder="storageaccount"
                    />
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Container</div>
                    <input
                      value={backupSettings.cloud?.container ?? ''}
                      onChange={(e) =>
                        setBackupSettings((s: any) => ({
                          ...s,
                          cloud: { ...(s.cloud || {}), container: e.target.value },
                        }))
                      }
                      className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      placeholder="backups"
                    />
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-400 mb-1">Account Key</div>
                  <input
                    type="password"
                    value={backupSettings.cloud?.account_key ?? ''}
                    onChange={(e) =>
                      setBackupSettings((s: any) => ({
                        ...s,
                        cloud: { ...(s.cloud || {}), account_key: e.target.value },
                      }))
                    }
                    className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    placeholder="Account Key"
                  />
                </div>
                <div>
                  <div className="text-xs text-slate-400 mb-1">Key Prefix (optional)</div>
                  <input
                    value={backupSettings.cloud?.key_prefix ?? ''}
                    onChange={(e) =>
                      setBackupSettings((s: any) => ({
                        ...s,
                        cloud: { ...(s.cloud || {}), key_prefix: e.target.value },
                      }))
                    }
                    className="w-full bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    placeholder="backups/"
                  />
                </div>
              </div>
            )}

            {/* Quota-Anzeige */}
            {backupSettings.cloud?.enabled && cloudQuota && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-4 bg-sky-900/20 border border-sky-700/40 rounded-lg"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-semibold text-white">Speicherplatz</div>
                  {cloudQuota.used_percent !== null && (
                    <div className={`text-sm font-semibold ${cloudQuota.used_percent > 90 ? 'text-red-300' : cloudQuota.used_percent > 75 ? 'text-yellow-300' : 'text-green-300'}`}>
                      {cloudQuota.used_percent}% belegt
                    </div>
                  )}
                </div>
                {cloudQuota.used_percent !== null && (
                  <div className="mb-2 h-2 bg-slate-700 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${cloudQuota.used_percent}%` }}
                      transition={{ duration: 0.5 }}
                      className={`h-full ${
                        cloudQuota.used_percent > 90 ? 'bg-red-500' : cloudQuota.used_percent > 75 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                    />
                  </div>
                )}
                <div className="grid grid-cols-3 gap-3 text-xs">
                  {cloudQuota.used_human && (
                    <div>
                      <div className="text-slate-400">Verwendet</div>
                      <div className="text-white font-semibold">{cloudQuota.used_human}</div>
                    </div>
                  )}
                  {cloudQuota.available_human && (
                    <div>
                      <div className="text-slate-400">Verfügbar</div>
                      <div className="text-green-300 font-semibold">{cloudQuota.available_human}</div>
                    </div>
                  )}
                  {cloudQuota.total_human && (
                    <div>
                      <div className="text-slate-400">Gesamt</div>
                      <div className="text-white font-semibold">{cloudQuota.total_human}</div>
                    </div>
                  )}
                </div>
              </motion.div>
            )}

            {/* Buttons */}
            <div className="flex gap-3">
              <button
                onClick={testCloud}
                disabled={testingCloud || !backupSettings.cloud?.enabled}
                className="flex-1 px-4 py-2 bg-slate-700/60 hover:bg-slate-700 text-white rounded-lg disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {testingCloud ? (
                  <>
                    <RefreshCw size={16} className="animate-spin" />
                    Teste…
                  </>
                ) : (
                  <>
                    <CheckCircle size={16} />
                    Verbindung testen
                  </>
                )}
              </button>
              <button
                onClick={saveBackupSettings}
                className="flex-1 px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg"
              >
                Speichern
              </button>
            </div>
          </div>
        )}
      </motion.div>
        )}

        {activeTab === 'logs' && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card">
            <div className="flex items-center justify-between gap-3 mb-3">
              <h3 className="text-lg font-bold text-white">Logs</h3>
              <button onClick={loadLogs} className="px-3 py-2 bg-slate-700/60 hover:bg-slate-700 text-white rounded-lg">
                {loadingLogs ? '⏳ Lade…' : 'Logs laden'}
              </button>
            </div>
            {logPath && (
              <p className="mb-2 text-sm text-slate-400">
                Log-Datei: <code className="bg-slate-800 px-1.5 py-0.5 rounded">{logPath}</code>
                {' '}(<code className="text-slate-500">tail -f &#39;{logPath}&#39;</code> im Terminal)
              </p>
            )}
            <pre className="bg-slate-950/50 border border-slate-700 rounded-lg p-3 text-xs text-slate-200 overflow-auto max-h-96 whitespace-pre-wrap">
              {logs || '—'}
            </pre>
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}

export default SettingsPage
