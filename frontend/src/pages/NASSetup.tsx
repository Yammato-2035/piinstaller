import React, { useState, useEffect } from 'react'
import { HardDrive, Server, Folder, Users, Search, Trash2, FileWarning } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'
import { usePlatform } from '../context/PlatformContext'
import SudoPasswordModal from '../components/SudoPasswordModal'

const NASSetup: React.FC = () => {
  const { pageSubtitleLabel } = usePlatform()
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
  const [duplicateScanPath, setDuplicateScanPath] = useState(config.share_path)
  const [duplicateBackupPath, setDuplicateBackupPath] = useState(config.share_path + '/duplicate_backup')
  const [excludeSystemCache, setExcludeSystemCache] = useState(true)
  const [duplicateResult, setDuplicateResult] = useState<{ groups: { files: string[]; count: number }[]; total_duplicates: number; total_groups: number } | null>(null)
  const [loadingDuplicates, setLoadingDuplicates] = useState(false)
  const [duplicateSudoOpen, setDuplicateSudoOpen] = useState(false)
  const [pendingDuplicateAction, setPendingDuplicateAction] = useState<'install' | 'move' | null>(null)

  useEffect(() => {
    loadNasStatus()
  }, [])

  const loadNasStatus = async () => {
    try {
      const response = await fetchApi('/api/nas/status')
      const data = await response.json()
      setNasStatus(data)
      if (data.suggested_scan_path) {
        setDuplicateScanPath(prev => (prev === '/mnt/nas' ? data.suggested_scan_path : prev))
        setDuplicateBackupPath(prev => (prev === '/mnt/nas/duplicate_backup' ? data.suggested_scan_path + '/duplicate_backup' : prev))
      }
    } catch (error) {
      console.error('Fehler beim Laden des NAS-Status:', error)
    }
  }

  const nasTypes = [
    { id: 'samba', label: '📁 Samba/CIFS', desc: 'Windows-kompatibel, einfach zu nutzen' },
    { id: 'nfs', label: '🔗 NFS', desc: 'Linux/Unix Netzwerk-Dateisystem' },
    { id: 'ftp', label: '📤 FTP/SFTP', desc: 'Dateiübertragung über Internet' },
  ]

  const runDuplicateInstall = async (sudoPassword: string) => {
    setLoadingDuplicates(true)
    try {
      const r = await fetchApi('/api/nas/duplicates/install', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sudo_password: sudoPassword }),
      })
      const d = await r.json()
        if (d.status === 'success') {
        toast.success(d.message || 'Duplikat-Finder installiert')
        await loadNasStatus()
      } else {
        toast.error(d.message || 'Installation fehlgeschlagen')
      }
    } catch (e) {
      toast.error('Fehler bei der Installation')
    } finally {
      setLoadingDuplicates(false)
      setDuplicateSudoOpen(false)
      setPendingDuplicateAction(null)
    }
  }

  const runDuplicateScan = async () => {
    setLoadingDuplicates(true)
    setDuplicateResult(null)
    try {
      const r = await fetchApi('/api/nas/duplicates/scan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: duplicateScanPath || config.share_path,
          exclude_system_cache: excludeSystemCache,
        }),
      })
      const d = await r.json()
      if (d.status === 'success') {
        setDuplicateResult(d)
        if (d.total_groups === 0) toast.success('Keine Duplikate gefunden')
        else toast.success(`${d.total_duplicates} Duplikate in ${d.total_groups} Gruppen gefunden`)
      } else {
        if (d.requires_install) {
          setPendingDuplicateAction('install')
          setDuplicateSudoOpen(true)
        }
        toast.error(d.message || 'Scan fehlgeschlagen')
      }
    } catch (e) {
      toast.error('Fehler beim Scan')
    } finally {
      setLoadingDuplicates(false)
    }
  }

  const runMoveToBackup = async (sudoPassword: string) => {
    if (!duplicateResult?.groups?.length) return
    setLoadingDuplicates(true)
    try {
      const r = await fetchApi('/api/nas/duplicates/move-to-backup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          groups: duplicateResult.groups,
          backup_path: duplicateBackupPath || config.share_path + '/duplicate_backup',
          sudo_password: sudoPassword,
        }),
      })
      const d = await r.json()
      if (d.status === 'success') {
        toast.success(d.message)
        setDuplicateResult(null)
        await runDuplicateScan()
      } else {
        toast.error(d.message || 'Verschieben fehlgeschlagen')
      }
    } catch (e) {
      toast.error('Fehler beim Verschieben')
    } finally {
      setLoadingDuplicates(false)
      setDuplicateSudoOpen(false)
      setPendingDuplicateAction(null)
    }
  }

  const handleDuplicateSudoConfirm = async (password: string) => {
    if (pendingDuplicateAction === 'install') await runDuplicateInstall(password)
    else if (pendingDuplicateAction === 'move') await runMoveToBackup(password)
  }

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
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <HardDrive className="text-purple-500" />
            NAS (Network Attached Storage)
          </h1>
        </div>
        <p className="text-slate-400">NAS – {pageSubtitleLabel}</p>
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

      {/* Duplikate & Aufräumen */}
      <div className="card">
        <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
          <FileWarning className="text-amber-500" />
          Duplikate & Aufräumen
        </h2>
        <p className="text-slate-400 text-sm mb-4">
          Findet doppelte Dateien auf dem NAS und kann sie in einen Backup-Ordner verschieben (statt zu löschen).
        </p>
        {nasStatus && (
          <div className="flex items-center gap-2 mb-4">
            <span className="text-slate-300">Duplikat-Finder (fdupes/jdupes):</span>
            {nasStatus.fdupes?.installed ? (
              <span className="px-2 py-1 bg-green-900/50 text-green-300 rounded text-xs">✓ Installiert</span>
            ) : (
              <span className="px-2 py-1 bg-amber-900/50 text-amber-300 rounded text-xs">Nicht installiert</span>
            )}
            {!nasStatus.fdupes?.installed && (
              <button
                onClick={() => { setPendingDuplicateAction('install'); setDuplicateSudoOpen(true) }}
                disabled={loadingDuplicates}
                className="px-3 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-sm disabled:opacity-50"
              >
                Installieren
              </button>
            )}
          </div>
        )}
        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-slate-300 mb-1 text-sm">Scan-Pfad</label>
            <input
              type="text"
              value={duplicateScanPath}
              onChange={(e) => setDuplicateScanPath(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700 text-sm"
              placeholder="/mnt/nas"
            />
          </div>
          <div>
            <label className="block text-slate-300 mb-1 text-sm">Backup-Pfad (für Verschieben)</label>
            <input
              type="text"
              value={duplicateBackupPath}
              onChange={(e) => setDuplicateBackupPath(e.target.value)}
              className="w-full px-4 py-2 bg-slate-800 text-white rounded-lg border border-slate-700 text-sm"
              placeholder="/mnt/nas/duplicate_backup"
            />
          </div>
        </div>
        <div className="flex items-center gap-2 mb-4">
          <input
            type="checkbox"
            id="exclude-system-cache"
            checked={excludeSystemCache}
            onChange={(e) => setExcludeSystemCache(e.target.checked)}
            className="w-4 h-4 accent-sky-600"
          />
          <label htmlFor="exclude-system-cache" className="text-slate-400 text-sm">
            System-/Cache-Verzeichnisse ausschließen (.cache, mesa_shader, __pycache__, node_modules, .git)
          </label>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            onClick={runDuplicateScan}
            disabled={loadingDuplicates || !nasStatus?.fdupes?.installed}
            className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center gap-2"
          >
            <Search size={16} /> {loadingDuplicates ? 'Scanne...' : 'Scan starten'}
          </button>
          {duplicateResult && duplicateResult.total_groups > 0 && (
            <button
              onClick={() => { setPendingDuplicateAction('move'); setDuplicateSudoOpen(true) }}
              disabled={loadingDuplicates}
              className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg text-sm font-medium disabled:opacity-50 flex items-center gap-2"
            >
              <Trash2 size={16} /> In Backup verschieben
            </button>
          )}
        </div>
        {duplicateResult && duplicateResult.groups && duplicateResult.groups.length > 0 && (
          <div className="mt-4 p-3 bg-slate-800/50 rounded-lg max-h-64 overflow-y-auto">
            <p className="text-slate-400 text-sm mb-2">
              {duplicateResult.total_duplicates} Duplikate in {duplicateResult.total_groups} Gruppen. Pro Gruppe bleibt die erste Datei, der Rest wird ins Backup verschoben.
            </p>
            <ul className="space-y-3 text-xs">
              {duplicateResult.groups.slice(0, 15).map((g: { files: string[] }, i: number) => (
                <li key={i} className="border-l-2 border-slate-600 pl-2">
                  {g.files.map((f: string, j: number) => (
                    <div key={j} className="text-slate-300 font-mono truncate" title={f}>
                      {j === 0 ? '✓ ' : '  '}{f}
                    </div>
                  ))}
                </li>
              ))}
              {duplicateResult.groups.length > 15 && (
                <li className="text-slate-500">… und {duplicateResult.groups.length - 15} weitere Gruppen</li>
              )}
            </ul>
          </div>
        )}
      </div>

      <SudoPasswordModal
        open={duplicateSudoOpen}
        title="Sudo-Passwort"
        subtitle={pendingDuplicateAction === 'install' ? 'Für die Installation von fdupes.' : 'Zum Verschieben der Duplikate ins Backup.'}
        confirmText="Bestätigen"
        onCancel={() => { setDuplicateSudoOpen(false); setPendingDuplicateAction(null) }}
        onConfirm={handleDuplicateSudoConfirm}
      />

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
