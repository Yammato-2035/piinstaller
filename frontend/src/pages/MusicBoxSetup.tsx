import React, { useState, useEffect } from 'react'
import { Music, Radio, Headphones } from 'lucide-react'
import toast from 'react-hot-toast'

const MusicBoxSetup: React.FC = () => {
  const [config, setConfig] = useState({
    music_type: 'mopidy',
    enable_mopidy: false,
    enable_volumio: false,
    enable_plex: false,
    enable_airplay: false,
    enable_spotify: false,
  })

  const [loading, setLoading] = useState(false)
  const [musicStatus, setMusicStatus] = useState<any>(null)

  useEffect(() => {
    loadMusicStatus()
  }, [])

  const loadMusicStatus = async () => {
    try {
      const response = await fetch('/api/musicbox/status')
      const data = await response.json()
      setMusicStatus(data)
    } catch (error) {
      console.error('Fehler beim Laden des MusicBox-Status:', error)
    }
  }

  const musicTypes = [
    { id: 'mopidy', label: '🎵 Mopidy', desc: 'Modularer Music Server', port: 6680, docsLink: 'https://docs.mopidy.com/' },
    { id: 'volumio', label: '📻 Volumio', desc: 'Audiophile Music Player', port: 3000, docsLink: 'https://volumio.org/get-started/' },
    { id: 'plex', label: '🎬 Plex Media Server', desc: 'Media Server & Streaming', port: 32400, docsLink: 'https://support.plex.tv/' },
  ]

  const applyConfig = async () => {
    const sudoPassword = prompt('Sudo-Passwort eingeben:')
    if (!sudoPassword) {
      toast.error('Sudo-Passwort erforderlich')
      return
    }

    setLoading(true)
    try {
      const response = await fetch('/api/musicbox/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...config,
          sudo_password: sudoPassword,
        }),
      })
      const data = await response.json()

      if (data.status === 'success') {
        toast.success('Musikbox konfiguriert!')
        await loadMusicStatus()
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
          <Music className="text-purple-500" />
          Musikbox
        </h1>
        <p className="text-slate-400">Richten Sie einen Music Server ein</p>
      </div>

      {/* Status */}
      {musicStatus && (
        <div className="card">
          <h2 className="text-2xl font-bold text-white mb-4">Status</h2>
          <div className="grid md:grid-cols-3 gap-4">
            {musicTypes.map((type) => {
              const status = musicStatus[type.id]
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

      {/* Music Type Selection */}
      <div className="card">
        <h2 className="text-2xl font-bold text-white mb-4">Music Server auswählen</h2>
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

      {/* Additional Options */}
      <div className="card">
        <h2 className="text-2xl font-bold text-white mb-4">Zusätzliche Features</h2>
        <div className="space-y-3">
          <label className="flex items-center gap-3 p-4 bg-slate-700/30 rounded-lg cursor-pointer">
            <input
              type="checkbox"
              checked={config.enable_airplay}
              onChange={(e) => setConfig({ ...config, enable_airplay: e.target.checked })}
              className="w-5 h-5 accent-sky-600"
            />
            <span className="text-slate-300">AirPlay Support</span>
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
          {loading ? 'Installieren...' : 'Installation starten'}
        </button>
      </div>
    </div>
  )
}

export default MusicBoxSetup
