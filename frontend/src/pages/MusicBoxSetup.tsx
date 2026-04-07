import React, { useState, useEffect, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Music, Radio, Headphones } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'
import SudoPasswordModal from '../components/SudoPasswordModal'
import { usePlatform } from '../context/PlatformContext'
import type { ExperienceLevel } from '../components/Sidebar'
import { PandaCompanion, PandaRail, PandaHelperStrip, type PandaStatus } from '../components/companions'

interface MusicBoxSetupProps {
  experienceLevel?: ExperienceLevel
}

const MusicBoxSetup: React.FC<MusicBoxSetupProps> = ({ experienceLevel = 'beginner' }) => {
  const { t } = useTranslation()
  const { pageSubtitleLabel } = usePlatform()
  const [config, setConfig] = useState({
    music_type: 'mopidy',
    enable_mopidy: false,
    enable_volumio: false,
    enable_plex: false,
    enable_airplay: false,
    enable_spotify: false,
    enable_internetradio: false,
    enable_streaming: false,
  })

  const [loading, setLoading] = useState(false)
  const [sudoModalOpen, setSudoModalOpen] = useState(false)
  const [installMixerSudoOpen, setInstallMixerSudoOpen] = useState(false)
  const [loadingMixerInstall, setLoadingMixerInstall] = useState(false)
  const [mixerInstallError, setMixerInstallError] = useState<{ message?: string; copyable_command?: string } | null>(null)
  const [musicStatus, setMusicStatus] = useState<any>(null)
  const [diagnoseData, setDiagnoseData] = useState<any>(null)
  const [loadingDiagnose, setLoadingDiagnose] = useState(false)

  useEffect(() => {
    loadMusicStatus()
  }, [])

  const musicCompanionStatus = useMemo((): PandaStatus => {
    if (diagnoseData?.error) return 'warning'
    const st = musicStatus?.[config.music_type]
    if (st?.running) return 'success'
    if (st?.installed) return 'warning'
    return 'info'
  }, [musicStatus, config.music_type, diagnoseData?.error])

  const loadDiagnose = async () => {
    setLoadingDiagnose(true)
    setDiagnoseData(null)
    try {
      const response = await fetchApi('/api/musicbox/mopidy-diagnose')
      const data = await response.json()
      setDiagnoseData(data)
    } catch (e) {
      setDiagnoseData({ error: String(e) })
    } finally {
      setLoadingDiagnose(false)
    }
  }

  const loadMusicStatus = async () => {
    try {
      const response = await fetchApi('/api/musicbox/status')
      const data = await response.json()
      setMusicStatus(data)
    } catch (error) {
      console.error('Fehler beim Laden des MusicBox-Status:', error)
    }
  }

  const installMixerPackages = async (sudoPassword?: string) => {
    setLoadingMixerInstall(true)
    setMixerInstallError(null)
    try {
      const response = await fetchApi('/api/system/install-mixer-packages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(sudoPassword != null ? { sudo_password: sudoPassword } : {}),
      })
      const data = await response.json()
      if (data.status === 'success') {
        setInstallMixerSudoOpen(false)
        setMixerInstallError(null)
        toast.success(data.message)
      } else {
        if (data.requires_sudo_password) setInstallMixerSudoOpen(true)
        else {
          toast.error(data.message || t('musicbox.toast.installFailed'))
          if (data.copyable_command) setMixerInstallError({ message: data.message, copyable_command: data.copyable_command })
        }
      }
    } catch (e) {
      toast.error(t('musicbox.toast.installFailed'))
      setMixerInstallError({
        message: t('musicbox.toast.installFailed'),
        copyable_command: 'sudo apt-get update && sudo apt-get install -y pavucontrol qpwgraph',
      })
    } finally {
      setLoadingMixerInstall(false)
    }
  }

  const musicTypes = [
    { id: 'mopidy', label: '🎵 Mopidy', desc: 'Modularer Music Server (Internetradio, lokale Dateien, Erweiterungen)', port: 6680, docsLink: 'https://docs.mopidy.com/', paid: false },
    { id: 'volumio', label: '📻 Volumio', desc: 'Audiophile Music Player (Radio, Streaming, Plugins)', port: 3000, docsLink: 'https://volumio.org/get-started/', paid: 'optional' },
    { id: 'plex', label: '🎬 Plex Media Server', desc: 'Media Server & Streaming (Plex Pass optional)', port: 32400, docsLink: 'https://support.plex.tv/', paid: 'optional' },
  ]

  const runApplyConfig = async (sudoPassword: string) => {
    setLoading(true)
    try {
      const response = await fetchApi('/api/musicbox/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...config,
          sudo_password: sudoPassword,
        }),
      })
      const data = await response.json()

      if (data.status === 'success') {
        setSudoModalOpen(false)
        toast.success(t('musicbox.toast.configured'))
        if (data.results && data.results.length > 0) {
          data.results.forEach((result: string) => toast.success(result, { duration: 3000 }))
        }
        await loadMusicStatus()
      } else {
        if (data.requires_sudo_password) {
          setSudoModalOpen(true)
        } else {
          toast.error(data.message || t('musicbox.toast.configError'))
        }
      }
    } catch (error) {
      toast.error(t('musicbox.toast.configError'))
    } finally {
      setLoading(false)
    }
  }

  const applyConfig = async () => {
    setLoading(true)
    try {
      const response = await fetchApi('/api/musicbox/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      })
      const data = await response.json()

      if (data.status === 'success') {
        toast.success(t('musicbox.toast.configured'))
        if (data.results && data.results.length > 0) {
          data.results.forEach((result: string) => toast.success(result, { duration: 3000 }))
        }
        await loadMusicStatus()
      } else {
        if (data.requires_sudo_password) {
          setSudoModalOpen(true)
        } else {
          toast.error(data.message || t('musicbox.toast.configError'))
        }
      }
    } catch (error) {
      toast.error(t('musicbox.toast.configError'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <Music className="text-purple-500" />
            {t('musicbox.page.title')}
          </h1>
        </div>
        <p className="text-slate-400">{t('musicbox.page.subtitle', { pageSubtitleLabel })}</p>
      </div>

      <PandaHelperStrip experienceLevel={experienceLevel} variant="base">
        {t('musicbox.panda.strip')}
      </PandaHelperStrip>
      <PandaRail>
        <PandaCompanion
          type="tutorial"
          size="sm"
          surface="dark"
          frame={false}
          showTrafficLight
          trafficLightPosition="bottom-right"
          status={musicCompanionStatus}
          title={t('musicbox.panda.companionTitle')}
          subtitle={t('musicbox.panda.companionSubtitle')}
        />
      </PandaRail>

      {/* Info: Music-Server & Bezahldienste */}
      <div className="card-info">
        <h3 className="text-base font-semibold mb-2">ℹ️ Music-Server & Bezahldienste</h3>
        <p className="text-sm mb-2">
          <strong>Mopidy / Volumio</strong> sind kostenlos und unterstützen lokale Dateien, Internetradio und Erweiterungen (z. B. Spotify Connect, Tidal, <strong>Apple Music</strong>, <strong>Amazon Music</strong>). Einige Dienste erfordern ein Abo.
        </p>
        <p className="text-sm mb-2">
          <strong>Apple Music:</strong> per AirPlay von iPhone/iPad/Mac („AirPlay Support“ aktivieren). <strong>Amazon Music:</strong> über Volumio-Plugin oder im Browser (music.amazon.com). <strong>Plex</strong> ist grundsätzlich kostenlos; Plex Pass optional.
        </p>
        <p className="text-sm">
          Spotify, Tidal, Deezer usw. benötigen jeweils ein eigenes Konto/Abo und werden in der Web-Oberfläche des Music-Servers verbunden.
        </p>
      </div>

      {/* Info: Ausgabequelle & Mixer */}
      <div className="card-info">
        <h3 className="text-base font-semibold mb-2">🔊 Ausgabequelle & Mixer</h3>
        <p className="text-sm mb-3">
          <strong>Ausgabequelle wählen:</strong> Unter Linux steuern PulseAudio bzw. PipeWire die Wiedergabe. Headset, Lautsprecher oder HDMI in den <strong>System-Sound-Einstellungen</strong> oder mit <code className="opacity-90 px-1 rounded">pavucontrol</code> (Mixer).
        </p>
        <p className="text-sm mb-2">
          <strong>Mopidy-Weboberfläche:</strong> Ohne Webclient-Erweiterung zeigt Port 6680 nur zwei Texte („Mopidy“, „Web clients“). Mit „Installation starten“ wird automatisch <strong>Iris</strong> installiert; danach unter <code className="opacity-90 px-1 rounded">http://localhost:6680/iris</code> die volle Oberfläche nutzen.
        </p>
        <p className="text-sm mb-2 opacity-90">
          <strong>Iris läuft nicht?</strong> Mopidy läuft als User „mopidy“. Einmal „Installation starten“ erneut ausführen – dabei wird Iris ggf. für diesen User nachinstalliert. Oder manuell im Terminal (auf dem Rechner, auf dem Mopidy läuft):
        </p>
        <pre className="p-3 bg-slate-800 rounded text-xs overflow-x-auto text-slate-200 mb-3 select-all">
sudo -u mopidy python3 -m pip install --user --break-system-packages Mopidy-Iris
sudo systemctl restart mopidy
        </pre>
        <div className="flex flex-wrap gap-3 mb-3">
          <a href="http://localhost:6680/iris" target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-sm font-medium">
            🎵 Mopidy Iris (Port 6680/iris)
          </a>
          <a href="http://localhost:6680" target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium">
            Mopidy Startseite (6680)
          </a>
          <a href="http://localhost:3000" target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-sm font-medium">
            📻 Volumio (Port 3000)
          </a>
          <a href="http://localhost:32400/web" target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-sm font-medium">
            🎬 Plex Web (Port 32400)
          </a>
          <a href="http://localhost:6680" target="_blank" rel="noopener noreferrer" className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium">
            📡 Internetradio (Mopidy)
          </a>
        </div>
        <p className="text-sm mb-3">
          <strong>Mixer:</strong> <code className="opacity-90 px-1 rounded">pavucontrol</code> (PulseAudio) oder <code className="opacity-90 px-1 rounded">qpwgraph</code> (PipeWire) für Kanäle und Lautstärke. <strong>Dolby Atmos:</strong> herstellerspezifisch (z. B. Dolby Access).
        </p>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={async () => {
              try {
                const r = await fetchApi('/api/system/run-mixer', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ app: 'pavucontrol' }),
                })
                const d = await r.json()
                if (d.status === 'success') toast.success(d.message)
                else toast.error(d.message || 'Fehler')
              } catch (e) {
                toast.error('Mixer konnte nicht gestartet werden')
              }
            }}
            className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-sm font-medium"
          >
            Mixer öffnen (pavucontrol)
          </button>
          <button
            type="button"
            onClick={async () => {
              try {
                const r = await fetchApi('/api/system/run-mixer', {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ app: 'qpwgraph' }),
                })
                const d = await r.json()
                if (d.status === 'success') toast.success(d.message)
                else toast.error(d.message || 'Fehler')
              } catch (e) {
                toast.error('Mixer konnte nicht gestartet werden')
              }
            }}
            className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium"
          >
            Mixer öffnen (qpwgraph)
          </button>
          <button
            type="button"
            onClick={() => installMixerPackages()}
            disabled={loadingMixerInstall}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium disabled:opacity-50"
          >
            {loadingMixerInstall ? 'Installiere…' : 'Mixer-Programme installieren (pavucontrol & qpwgraph)'}
          </button>
        </div>
        {mixerInstallError?.copyable_command && (
          <div className="mt-3 p-3 bg-slate-800/60 rounded-lg border border-amber-600/40">
            <p className="text-amber-200 text-xs mb-2">{t('musicbox.mixer.manualHint')}</p>
            <div className="flex flex-wrap items-center gap-2">
              <code className="flex-1 min-w-0 bg-slate-800 px-2 py-1 rounded text-slate-200 font-mono text-xs break-all">{mixerInstallError.copyable_command}</code>
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(mixerInstallError!.copyable_command!)
                  toast.success(t('musicbox.mixer.copied'))
                }}
                className="px-2 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-xs shrink-0"
              >
                {t('musicbox.mixer.copy')}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Iris-Diagnose (warum läuft Iris nicht?) */}
      <div className="card">
        <h2 className="text-2xl font-bold text-white mb-2">{t('musicbox.diagnose.title')}</h2>
        <p className="text-slate-400 text-sm mb-3">{t('musicbox.diagnose.intro')}</p>
        <button
          type="button"
          onClick={loadDiagnose}
          disabled={loadingDiagnose}
          className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white rounded-lg text-sm font-medium disabled:opacity-50"
        >
          {loadingDiagnose ? t('musicbox.diagnose.running') : t('musicbox.diagnose.run')}
        </button>
        {diagnoseData && (
          <div className="mt-4 space-y-3 text-sm">
            {diagnoseData.error && (
              <p className="text-red-400">{diagnoseData.error}</p>
            )}
            <div className="grid gap-2">
              <p>
                <span className="text-slate-500">{t('musicbox.diagnose.irisCurrentUser')}</span>{' '}
                {diagnoseData.iris_import_current_user ? t('musicbox.yes') : t('musicbox.no')}
              </p>
              {diagnoseData.iris_visible_to_mopidy !== undefined && (
                <p>
                  <span className="text-slate-500">{t('musicbox.diagnose.irisMopidyUser')}</span>{' '}
                  {diagnoseData.iris_visible_to_mopidy ? t('musicbox.yes') : t('musicbox.diagnose.irisMopidyNoDetail')}
                </p>
              )}
              {!diagnoseData.sudo_used && (
                <p className="text-amber-400">{t('musicbox.diagnose.sudoHint')}</p>
              )}
            </div>
            {diagnoseData.iris_config_snippet && (
              <div>
                <p className="text-slate-500 mb-1">{t('musicbox.diagnose.configSnip')}</p>
                <pre className="p-2 bg-slate-800 rounded text-xs overflow-x-auto whitespace-pre-wrap break-words">{diagnoseData.iris_config_snippet}</pre>
              </div>
            )}
            {diagnoseData.mopidy_deps && (
              <div>
                <p className="text-slate-500 mb-1">{t('musicbox.diagnose.deps')}</p>
                <pre className="p-2 bg-slate-800 rounded text-xs overflow-x-auto whitespace-pre-wrap break-words max-h-40 overflow-y-auto">{diagnoseData.mopidy_deps}</pre>
              </div>
            )}
            {diagnoseData.mopidy_extensions_output && (
              <div>
                <p className="text-slate-500 mb-1">{t('musicbox.diagnose.extensions')}</p>
                <pre className="p-2 bg-slate-800 rounded text-xs overflow-x-auto whitespace-pre-wrap break-words max-h-48 overflow-y-auto">{diagnoseData.mopidy_extensions_output}</pre>
              </div>
            )}
            {diagnoseData.mopidy_log_tail && (
              <div>
                <p className="text-slate-500 mb-1">{t('musicbox.diagnose.logTail')}</p>
                <pre className="p-2 bg-slate-800 rounded text-xs overflow-x-auto whitespace-pre-wrap break-words max-h-64 overflow-y-auto">{diagnoseData.mopidy_log_tail}</pre>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Status */}
      {musicStatus && (
        <div className="card">
          <h2 className="text-2xl font-bold text-white mb-4">{t('musicbox.status.title')}</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {musicTypes.map((type) => {
              const status = musicStatus[type.id]
              return (
                <div key={type.id} className="p-4 bg-slate-800/50 rounded">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-300 font-semibold">{type.label}</span>
                    {status?.installed ? (
                      <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">{t('musicbox.status.installed')}</span>
                    ) : (
                      <span className="px-2 py-1 bg-red-900/50 text-white rounded text-xs">{t('musicbox.status.notInstalled')}</span>
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
                        {t('musicbox.openPort', { port: type.port })}
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
                        {t('musicbox.docs')}
                      </a>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Music Type Selection */}
      <div className="card">
        <h2 className="text-2xl font-bold text-white mb-4">{t('musicbox.serverSelect.title')}</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {musicTypes.map((type) => (
            <div
              key={type.id}
              onClick={() => setConfig({ ...config, music_type: type.id })}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                config.music_type === type.id
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

      {/* Info: Bezahldienste & Zugangsdaten */}
      <div className="card-info">
        <h2 className="text-xl font-bold mb-2">Bezahldienste & Zugangsdaten</h2>
        <p className="text-sm mb-4">
          Zugangsdaten speichern, damit Mopidy/Volumio sie nutzen können (z. B. Spotify Connect, Tidal). Gespeichert werden nur Hinweise „Zugangsdaten hinterlegt“; die eigentlichen Daten legst du in den jeweiligen Programmen oder über deren Web-Oberfläche an.
        </p>
        <ul className="text-sm space-y-2 mb-4 list-disc list-inside">
          <li><strong>Spotify</strong> – Abo nötig; in Mopidy/Volumio: Spotify Connect aktivieren und anmelden</li>
          <li><strong>Apple Music</strong> – Abo nötig; von iPhone/iPad/Mac per <strong>AirPlay</strong> auf die Musikbox streamen (unten „AirPlay Support“ aktivieren)</li>
          <li><strong>Amazon Music</strong> – Abo optional; über Volumio-Plugin (Volumio-Weboberfläche) oder im Browser (music.amazon.com)</li>
          <li><strong>Tidal</strong> – Abo nötig; Erweiterung in Mopidy/Volumio konfigurieren</li>
          <li><strong>Deezer</strong> – Abo optional; Plugin in Volumio/Mopidy</li>
          <li><strong>Plex Pass</strong> – optional; Plex Media Server mit Konto verknüpfen</li>
        </ul>
        <div className="card-hint mt-3">
          <p className="text-sm">
            <strong>Hinweis:</strong> Zugangsdaten für Spotify/Tidal etc. werden in der Regel in der Oberfläche des Music-Servers (Mopidy Web, Volumio) eingegeben und dort gespeichert. Nach der Installation die jeweilige Web-Oberfläche öffnen (Buttons oben) und dort den gewünschten Dienst verbinden.
          </p>
        </div>
      </div>

      {/* Hinweis: AirPlay-Ziel = verbundener Rechner (Pi oder Linux-PC/Laptop) */}
      <div className="card-hint">
        <h3 className="text-base font-semibold mb-2">🔊 AirPlay: Auf welchem Rechner?</h3>
        <p className="text-sm mb-2">
          AirPlay (Shairport-sync) wird <strong>auf dem Rechner installiert, mit dem Sie verbunden sind</strong> – ob Raspberry Pi, Linux-Laptop oder -PC. Dieser Rechner erscheint dann auf dem iPhone bzw. bei Apple-Geräten als AirPlay-Ziel.
        </p>
        <p className="text-sm">
          Das Programm ist nicht Pi-spezifisch: Wenn Sie z. B. auf einem ASUS-Laptop mit Linux verbunden sind, wird AirPlay dort installiert und der Laptop wird zur Musikbox bzw. zum AirPlay-Ziel. Wenn Sie mit einem Pi verbunden sind, wird der Pi zum Ziel. So können Sie an jedem Linux-Rechner, auf dem die App läuft, AirPlay nutzen.
        </p>
      </div>

      {/* Additional Options */}
      <div className="card">
        <h2 className="text-2xl font-bold text-white mb-4">Zusätzliche Features</h2>
        <div className="space-y-3">
          <label className="flex items-center gap-3 p-4 bg-slate-700/30 rounded-lg cursor-pointer">
            <input
              type="checkbox"
              checked={config.enable_internetradio}
              onChange={(e) => setConfig({ ...config, enable_internetradio: e.target.checked })}
              className="w-5 h-5 accent-sky-600"
            />
            <span className="text-slate-300">Internetradio</span>
            <span className="text-slate-500 text-sm">(z. B. Mopidy-Internetradio, Volumio Radio)</span>
          </label>
          <label className="flex items-center gap-3 p-4 bg-slate-700/30 rounded-lg cursor-pointer">
            <input
              type="checkbox"
              checked={config.enable_streaming}
              onChange={(e) => setConfig({ ...config, enable_streaming: e.target.checked })}
              className="w-5 h-5 accent-sky-600"
            />
            <span className="text-slate-300">Streaming-Dienste</span>
            <span className="text-slate-500 text-sm">(Spotify, Apple Music, Amazon Music, Tidal etc. – Abo erforderlich)</span>
          </label>
          <label className="flex items-center gap-3 p-4 bg-slate-700/30 rounded-lg cursor-pointer">
            <input
              type="checkbox"
              checked={config.enable_airplay}
              onChange={(e) => setConfig({ ...config, enable_airplay: e.target.checked })}
              className="w-5 h-5 accent-sky-600"
            />
            <span className="text-slate-300">AirPlay Support</span>
            <span className="text-slate-500 text-sm">(Shairport-sync – installiert auf dem Rechner, mit dem Sie verbunden sind)</span>
          </label>
          <label className="flex items-center gap-3 p-4 bg-slate-700/30 rounded-lg cursor-pointer">
            <input
              type="checkbox"
              checked={config.enable_spotify}
              onChange={(e) => setConfig({ ...config, enable_spotify: e.target.checked })}
              className="w-5 h-5 accent-sky-600"
            />
            <span className="text-slate-300">Spotify Connect</span>
          </label>
        </div>
      </div>

      {/* Apply Button */}
      <div className="flex justify-end">
        <button
          onClick={applyConfig}
          disabled={loading}
          className="px-6 py-3 bg-sky-600 hover:bg-sky-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
        >
          {loading ? t('musicbox.install.running') : t('musicbox.install.start')}
        </button>
      </div>

      <SudoPasswordModal
        open={sudoModalOpen}
        title={t('musicbox.sudo.installTitle')}
        subtitle={t('musicbox.sudo.installSubtitle')}
        confirmText={t('musicbox.sudo.installConfirm')}
        onCancel={() => setSudoModalOpen(false)}
        onConfirm={runApplyConfig}
      />
      <SudoPasswordModal
        open={installMixerSudoOpen}
        title={t('musicbox.sudo.mixerTitle')}
        subtitle={t('musicbox.sudo.mixerSubtitle')}
        confirmText={t('musicbox.sudo.mixerConfirm')}
        onCancel={() => setInstallMixerSudoOpen(false)}
        onConfirm={(pwd) => installMixerPackages(pwd)}
      />
    </div>
  )
}

export default MusicBoxSetup
