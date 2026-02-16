import React, { useEffect, useState } from 'react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
import { Upload, RefreshCw, Copy, Terminal, Package } from 'lucide-react'
import { fetchApi } from '../api'

interface SelfUpdateStatus {
  source_path: string
  source_version: string
  installed_path: string | null
  installed_version: string | null
  update_available: boolean
  is_running_from_opt: boolean
  can_run_deploy: boolean
  deploy_script: string
}

const PiInstallerUpdate: React.FC = () => {
  const [status, setStatus] = useState<SelfUpdateStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [installing, setInstalling] = useState(false)
  const [commandToRun, setCommandToRun] = useState<string | null>(null)

  const loadStatus = async () => {
    setLoading(true)
    try {
      const res = await fetchApi('/api/self-update/status')
      if (res.ok) {
        const data = await res.json()
        if (data.status === 'success') setStatus(data)
      }
    } catch {
      toast.error('Status konnte nicht geladen werden')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadStatus()
  }, [])

  const handleInstall = async () => {
    if (!status?.can_run_deploy) return
    setInstalling(true)
    setCommandToRun(null)
    try {
      const res = await fetchApi('/api/self-update/install', { method: 'POST' })
      const data = await res.json()
      if (data.status === 'success') {
        toast.success(data.message || 'Installation abgeschlossen')
        loadStatus()
      } else {
        if (data.command_to_run) setCommandToRun(data.command_to_run)
        toast.error(data.message || 'Installation fehlgeschlagen')
      }
    } catch (e) {
      toast.error('Installation fehlgeschlagen')
    } finally {
      setInstalling(false)
    }
  }

  const copyCommand = () => {
    if (!commandToRun) return
    navigator.clipboard.writeText(commandToRun).then(
      () => toast.success('Befehl in Zwischenablage kopiert'),
      () => toast.error('Kopieren fehlgeschlagen')
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[200px]">
        <RefreshCw className="w-8 h-8 text-sky-500 animate-spin" />
      </div>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-2xl"
    >
      <div className="flex items-center gap-3 mb-6">
        <div className="w-12 h-12 rounded-xl bg-sky-100 dark:bg-sky-900/40 flex items-center justify-center">
          <Package className="w-6 h-6 text-sky-600 dark:text-sky-400" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-slate-800 dark:text-white">PI-Installer aktualisieren</h1>
          <p className="text-slate-600 dark:text-slate-400 text-sm">
            Aktuelle Entwicklung auf /opt installieren – Service-User pi-installer, Berechtigungen gesetzt
          </p>
        </div>
      </div>

      {status && (
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 p-4">
            <h2 className="font-semibold text-slate-800 dark:text-white mb-3">Status</h2>
            <dl className="grid gap-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500 dark:text-slate-400">Quelle (läuft gerade)</dt>
                <dd className="font-mono text-slate-700 dark:text-slate-300 truncate max-w-[60%]" title={status.source_path}>
                  {status.source_path}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500 dark:text-slate-400">Version (Quelle)</dt>
                <dd className="font-mono text-slate-700 dark:text-slate-300">{status.source_version}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500 dark:text-slate-400">Installation unter /opt</dt>
                <dd className="font-mono text-slate-700 dark:text-slate-300">
                  {status.installed_path ?? '– nicht installiert'}
                </dd>
              </div>
              {status.installed_version != null && (
                <div className="flex justify-between gap-4">
                  <dt className="text-slate-500 dark:text-slate-400">Version (/opt)</dt>
                  <dd className="font-mono text-slate-700 dark:text-slate-300">{status.installed_version}</dd>
                </div>
              )}
            </dl>
            {status.is_running_from_opt && (
              <p className="mt-3 text-amber-600 dark:text-amber-400 text-sm">
                Sie nutzen bereits die Installation unter /opt. Für Updates aus einem anderen Verzeichnis dort starten.
              </p>
            )}
          </div>

          {!status.is_running_from_opt && status.can_run_deploy && (
            <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800/50 p-4">
              <h2 className="font-semibold text-slate-800 dark:text-white mb-2">Auf /opt installieren oder aktualisieren</h2>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                Kopiert das aktuelle Quellverzeichnis nach /opt/pi-installer, setzt den Service-User pi-installer und startet den Dienst neu.
              </p>
              <button
                type="button"
                onClick={handleInstall}
                disabled={installing}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-700 text-white font-medium disabled:opacity-50"
              >
                {installing ? (
                  <RefreshCw className="w-4 h-4 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4" />
                )}
                {installing ? 'Installation läuft…' : status.update_available ? 'Jetzt aktualisieren' : 'Jetzt nach /opt installieren'}
              </button>
            </div>
          )}

          {commandToRun && (
            <div className="rounded-xl border border-amber-200 dark:border-amber-800 bg-amber-50 dark:bg-amber-900/20 p-4">
              <h3 className="font-semibold text-amber-800 dark:text-amber-200 flex items-center gap-2 mb-2">
                <Terminal className="w-4 h-4" />
                Befehl im Terminal ausführen
              </h3>
              <p className="text-sm text-amber-700 dark:text-amber-300 mb-2">
                Der Deploy konnte nicht automatisch ausgeführt werden (z. B. sudo-Passwort). Führen Sie den Befehl lokal aus:
              </p>
              <pre className="text-sm bg-slate-800 text-slate-100 p-3 rounded-lg overflow-x-auto break-all">
                {commandToRun}
              </pre>
              <button
                type="button"
                onClick={copyCommand}
                className="mt-2 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 text-white text-sm"
              >
                <Copy className="w-3.5 h-3.5" />
                Kopieren
              </button>
            </div>
          )}

          {!status.can_run_deploy && !status.is_running_from_opt && (
            <p className="text-slate-600 dark:text-slate-400 text-sm">
              Das Deploy-Skript (scripts/deploy-to-opt.sh) wurde im Quellverzeichnis nicht gefunden.
            </p>
          )}
        </div>
      )}
    </motion.div>
  )
}

export default PiInstallerUpdate
