import React, { useState } from 'react'
import { Tv, Film, ExternalLink, Volume2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'
import SudoPasswordModal from '../components/SudoPasswordModal'
import { usePlatform } from '../context/PlatformContext'

const STREAMING_SERVICES = [
  { id: 'amazon', name: 'Amazon Prime Video', url: 'https://www.primevideo.com', color: 'from-blue-600 to-blue-800' },
  { id: 'netflix', name: 'Netflix', url: 'https://www.netflix.com', color: 'from-red-600 to-red-800' },
  { id: 'disney', name: 'Disney+', url: 'https://www.disneyplus.com', color: 'from-indigo-600 to-blue-800' },
  { id: 'sky', name: 'Sky', url: 'https://www.sky.de', color: 'from-slate-600 to-slate-800' },
  { id: 'paramount', name: 'Paramount+', url: 'https://www.paramountplus.com', color: 'from-blue-700 to-slate-800' },
  { id: 'ard', name: 'ARD Mediathek', url: 'https://www.ardmediathek.de', color: 'from-red-700 to-red-900' },
  { id: 'zdf', name: 'ZDF Mediathek', url: 'https://www.zdf.de', color: 'from-amber-600 to-amber-800' },
]

const OUTPUT_OPTIONS = [
  { id: 'tv', label: 'TV', desc: 'Fernseher (HDMI)' },
  { id: 'beamer', label: 'Beamer', desc: 'Projektor' },
  { id: 'monitor1', label: 'Monitor 1', desc: 'Hauptbildschirm' },
  { id: 'monitor2', label: 'Monitor 2', desc: 'Zweitbildschirm' },
  { id: 'surround', label: 'Surround / DTS / Dolby Digital', desc: 'Mehrkanal-Audio' },
]

const KinoStreaming: React.FC = () => {
  const { pageSubtitleLabel } = usePlatform()
  const [selectedOutput, setSelectedOutput] = useState<string>('tv')
  const [installMixerSudoOpen, setInstallMixerSudoOpen] = useState(false)
  const [loadingMixerInstall, setLoadingMixerInstall] = useState(false)
  const [mixerInstallError, setMixerInstallError] = useState<{ message?: string; copyable_command?: string } | null>(null)

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
          toast.error(data.message || 'Installation fehlgeschlagen')
          if (data.copyable_command) setMixerInstallError({ message: data.message, copyable_command: data.copyable_command })
        }
      }
    } catch (e) {
      toast.error('Installation fehlgeschlagen')
      setMixerInstallError({ message: 'Installation fehlgeschlagen', copyable_command: 'sudo apt-get update && sudo apt-get install -y pavucontrol qpwgraph' })
    } finally {
      setLoadingMixerInstall(false)
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <Film className="text-amber-500" />
            Kino / Streaming
          </h1>
        </div>
        <p className="text-slate-400">Kino / Streaming – {pageSubtitleLabel}</p>
      </div>

      {/* Info: Video- & Soundausgabe */}
      <div className="card-info">
        <h2 className="text-xl font-bold mb-2 flex items-center gap-2">
          <Tv size={22} />
          Video- & Soundausgabe
        </h2>
        <p className="text-sm mb-4">
          Wähle die Ausgabemöglichkeit für Bild (TV, Beamer, Monitor) und Ton (Surround, DTS, Dolby Digital). Die Umschaltung erfolgt in der Regel über die Systemeinstellungen (Display, Sound) oder über den Player.
        </p>
        <div className="flex flex-wrap gap-3">
          {OUTPUT_OPTIONS.map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => setSelectedOutput(opt.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedOutput === opt.id
                  ? 'bg-sky-600 text-white'
                  : 'bg-black/10 dark:bg-white/10 hover:opacity-80'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
        <p className="text-xs mt-2 opacity-90">
          Ausgewählt: <strong>{OUTPUT_OPTIONS.find((o) => o.id === selectedOutput)?.label}</strong> – {OUTPUT_OPTIONS.find((o) => o.id === selectedOutput)?.desc}
        </p>
      </div>

      {/* Info: Bezahldienste & Player starten */}
      <div className="card-info">
        <h2 className="text-xl font-bold mb-2">Streaming-Dienste & Player</h2>
        <p className="text-sm mb-4">
          Dienste im Browser öffnen oder Player starten. Zugangsdaten (Amazon, Netflix, Sky, Disney+ etc.) werden im jeweiligen Dienst bzw. in der jeweiligen App verwaltet.
        </p>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {STREAMING_SERVICES.map((s) => (
            <a
              key={s.id}
              href={s.url}
              target="_blank"
              rel="noopener noreferrer"
              className={`p-4 rounded-lg border border-slate-600 bg-gradient-to-br ${s.color} text-white hover:opacity-90 transition-opacity flex items-center justify-between gap-2`}
            >
              <span className="font-semibold">{s.name}</span>
              <ExternalLink size={18} />
            </a>
          ))}
        </div>
        <div className="card-hint mt-4">
          <p className="text-sm">
            <strong>Zugangsdaten:</strong> Bei Bezahldiensten (Prime, Netflix, Sky, Disney+, Paramount+) meldest du dich auf der jeweiligen Webseite oder in der App an. Eine zentrale Speicherung der Zugangsdaten in dieser Oberfläche ist aus Sicherheitsgründen nicht vorgesehen; nutze die Anmeldung direkt im Dienst oder einen Passwort-Manager.
          </p>
        </div>
      </div>

      {/* Mixer – Lautstärke & Ausgabegerät */}
      <div className="card-info">
        <h3 className="text-base font-semibold mb-2 flex items-center gap-2">
          <Volume2 size={18} />
          Mixer – Lautstärke & Ausgabegerät
        </h3>
        <p className="text-sm mb-3">
          Ton und Lautstärke für Kino/Streaming steuerst du über PulseAudio (<code className="opacity-90 px-1 rounded">pavucontrol</code>) oder PipeWire (<code className="opacity-90 px-1 rounded">qpwgraph</code>). Dort kannst du das Ausgabegerät (z. B. HDMI, AV-Receiver) und die Kanäle einstellen.
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
            <p className="text-amber-200 text-xs mb-2">Installation fehlgeschlagen. Manuell im Terminal ausführen:</p>
            <div className="flex flex-wrap items-center gap-2">
              <code className="flex-1 min-w-0 bg-slate-800 px-2 py-1 rounded text-slate-200 font-mono text-xs break-all">{mixerInstallError.copyable_command}</code>
              <button
                type="button"
                onClick={() => {
                  navigator.clipboard.writeText(mixerInstallError!.copyable_command!)
                  toast.success('Befehl kopiert')
                }}
                className="px-2 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-xs shrink-0"
              >
                Kopieren
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Hinweis: Surround, DTS, Dolby Digital */}
      <div className="card-hint">
        <h3 className="text-base font-semibold mb-2 flex items-center gap-2">
          <Volume2 size={18} />
          Surround, DTS, Dolby Digital
        </h3>
        <p className="text-sm">
          Mehrkanal-Audio (Surround, DTS, Dolby Digital/Atmos) wird über die System-Sound-Einstellungen (PulseAudio/PipeWire) und die Auswahl des passenden Ausgabegeräts gesteuert. Stelle in den Einstellungen das gewünschte Gerät (z. B. HDMI für AV-Receiver) als Ausgabe ein.
        </p>
      </div>

      <SudoPasswordModal
        open={installMixerSudoOpen}
        title="Sudo-Passwort für Mixer-Installation"
        subtitle="pavucontrol und qpwgraph werden per apt installiert. Dafür werden Administrator-Rechte benötigt."
        confirmText="Installieren"
        onCancel={() => setInstallMixerSudoOpen(false)}
        onConfirm={(pwd) => installMixerPackages(pwd)}
      />
    </div>
  )
}

export default KinoStreaming
