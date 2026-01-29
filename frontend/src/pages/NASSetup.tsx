import React, { useState, useEffect } from 'react'
import { HardDrive, Server, Folder, Users } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'

const NASSetup: React.FC = () => {
  const [config, setConfig] = useState({
    nas_type: 'samba',
    enable_samba: false,
    enable_nfs: false,
    enable_ftp: false,
    share_name: 'pi-share',
    share_path: '/mnt/nas',
    enable_guest: false,
    enable_encryption: true,
  })

  const [loading, setLoading] = useState(false)
  const [nasStatus, setNasStatus] = useState<any>(null)

  useEffect(() => {
    loadNasStatus()
  }, [])

  const loadNasStatus = async () => {
    try {
      const response = await fetchApi('/api/nas/status')
      const data = await response.json()
      setNasStatus(data)
    } catch (error) {
      console.error('Fehler beim Laden des NAS-Status:', error)
    }
  }

  const nasTypes = [
    { id: 'samba', label: '📁 Samba/CIFS', desc: 'Windows-kompatibel, einfach zu nutzen' },
    { id: 'nfs', label: '🔗 NFS', desc: 'Linux/Unix Netzwerk-Dateisystem' },
    { id: 'ftp', label: '📤 FTP/SFTP', desc: 'Dateiübertragung über Internet' },
  ]

  const applyConfig = async () => {
    const sudoPassword = prompt('Sudo-Passwort eingeben:')
    if (!sudoPassword) {
      toast.error('Sudo-Passwort erforderlich')
      return
    }

    setLoading(true)
    try {
      const response = await fetchApi('/api/nas/configure', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...config,
          sudo_password: sudoPassword,
        }),
      })
      const data = await response.json()

      if (data.status === 'success') {
        toast.success('NAS konfiguriert!')
        await loadNasStatus()
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
          <HardDrive className="text-purple-500" />
          NAS (Network Attached Storage)
        </h1>
        <p className="text-slate-400">Richten Sie einen Netzwerk-Speicher für Dateifreigabe ein</p>
      </div>

      {/* Status */}
      {nasStatus && (
        <div className="card">
          <h2 className="text-2xl font-bold text-white mb-4">Status</h2>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="p-4 bg-slate-800/50 rounded">
              <div className="flex items-center justify-between">
                <span className="text-slate-300">Samba</span>
                {nasStatus.samba?.installed ? (
                  <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">✓ Installiert</span>
                ) : (
                  <span className="px-2 py-1 bg-red-900/50 text-white rounded text-xs">Nicht installiert</span>
                )}
              </div>
            </div>
            <div className="p-4 bg-slate-800/50 rounded">
              <div className="flex items-center justify-between">
                <span className="text-slate-300">NFS</span>
                {nasStatus.nfs?.installed ? (
                  <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">✓ Installiert</span>
                ) : (
                  <span className="px-2 py-1 bg-red-900/50 text-white rounded text-xs">Nicht installiert</span>
                )}
              </div>
            </div>
            <div className="p-4 bg-slate-800/50 rounded">
              <div className="flex items-center justify-between">
                <span className="text-slate-300">FTP</span>
                {nasStatus.ftp?.installed ? (
                  <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">✓ Installiert</span>
                ) : (
                  <span className="px-2 py-1 bg-red-900/50 text-white rounded text-xs">Nicht installiert</span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* NAS Type Selection */}
      <div className="card">
        <h2 className="text-2xl font-bold text-white mb-4">NAS-Typ auswählen</h2>
        <div className="grid md:grid-cols-3 gap-4">
          {nasTypes.map((type) => (
            <div
              key={type.id}
              onClick={() => setConfig({ ...config, nas_type: type.id })}
              className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                config.nas_type === type.id
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

      {/* Configuration */}
      <div className="card">
        <h2 className="text-2xl font-bold text-white mb-4">Konfiguration</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-slate-300 mb-2">Freigabe-Name</label>
            <input
              type="text"
              value={config.share_name}
              onChange={(e) => setConfig({ ...config, share_name: e.target.value })}
              className="w-full px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700"
              placeholder="pi-share"
            />
          </div>
          <div>
            <label className="block text-slate-300 mb-2">Freigabe-Pfad</label>
            <input
              type="text"
              value={config.share_path}
              onChange={(e) => setConfig({ ...config, share_path: e.target.value })}
              className="w-full px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700"
              placeholder="/mnt/nas"
            />
          </div>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={config.enable_guest}
              onChange={(e) => setConfig({ ...config, enable_guest: e.target.checked })}
              className="w-5 h-5 accent-sky-600"
            />
            <label className="text-slate-300">Gast-Zugriff erlauben</label>
          </div>
          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={config.enable_encryption}
              onChange={(e) => setConfig({ ...config, enable_encryption: e.target.checked })}
              className="w-5 h-5 accent-sky-600"
            />
            <label className="text-slate-300">Verschlüsselung aktivieren</label>
          </div>
        </div>
      </div>

      {/* Apply Button */}
      <div className="flex justify-end">
        <button
          onClick={applyConfig}
          disabled={loading}
          className="px-6 py-3 bg-sky-600 hover:bg-sky-700 text-white rounded-lg font-semibold transition-colors disabled:opacity-50"
        >
          {loading ? 'Konfigurieren...' : 'Konfiguration anwenden'}
        </button>
      </div>
    </div>
  )
}

export default NASSetup
