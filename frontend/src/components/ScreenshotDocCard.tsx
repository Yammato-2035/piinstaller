import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { Camera } from 'lucide-react'
import toast from 'react-hot-toast'
import { setScreenshotMode } from '../api'

/** Seiten, die für Dokumentations-Screenshots erfasst werden (in dieser Reihenfolge). */
const SCREENSHOT_PAGES: { id: string; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'wizard', label: 'Assistent' },
  { id: 'presets', label: 'Voreinstellungen' },
  { id: 'security', label: 'Sicherheit' },
  { id: 'users', label: 'Benutzer' },
  { id: 'devenv', label: 'Dev-Umgebung' },
  { id: 'webserver', label: 'Webserver' },
  { id: 'mailserver', label: 'Mailserver' },
  { id: 'nas', label: 'NAS' },
  { id: 'homeautomation', label: 'Hausautomatisierung' },
  { id: 'musicbox', label: 'Musikbox' },
  { id: 'kino-streaming', label: 'Kino / Streaming' },
  { id: 'learning', label: 'Lerncomputer' },
  { id: 'monitoring', label: 'Monitoring' },
  { id: 'backup', label: 'Backup & Restore' },
  { id: 'control-center', label: 'Control Center' },
  { id: 'periphery-scan', label: 'Peripherie-Scan' },
  { id: 'raspberry-pi-config', label: 'Raspberry Pi Config' },
  { id: 'settings', label: 'Einstellungen' },
  { id: 'documentation', label: 'Dokumentation' },
]

interface ScreenshotDocCardProps {
  setCurrentPage?: (page: string) => void
}

export default function ScreenshotDocCard({ setCurrentPage }: ScreenshotDocCardProps) {
  const [running, setRunning] = useState(false)
  const [progress, setProgress] = useState('')

  const isTauri = typeof window !== 'undefined' && !!(window as any).__TAURI__

  const runScreenshots = async () => {
    if (!isTauri || !setCurrentPage) {
      toast.error('Nur in der Tauri-Desktop-App verfügbar.')
      return
    }

    const { invoke } = (window as any).__TAURI__.core
    const { getScreenshotableWindows, getWindowScreenshot } = await import('tauri-plugin-screenshots-api')

    setRunning(true)
    setScreenshotMode(true)

    try {
      const outputDir = await invoke<string>('get_screenshots_output_dir')
      const windows = await getScreenshotableWindows()
      const ourWindow = windows.find((w: { title?: string }) =>
        (w.title || '').includes('PI-Installer') || (w.title || '').includes('Raspberry')
      )
      const windowId = ourWindow?.id ?? windows[0]?.id

      if (!windowId) {
        toast.error('Kein Fenster für Screenshot gefunden.')
        setScreenshotMode(false)
        setRunning(false)
        return
      }

      const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

      for (let i = 0; i < SCREENSHOT_PAGES.length; i++) {
        const { id, label } = SCREENSHOT_PAGES[i]
        setProgress(`${i + 1}/${SCREENSHOT_PAGES.length}: ${label}`)
        setCurrentPage(id)
        await delay(1800)

        try {
          const sourcePath = await getWindowScreenshot(windowId)
          const filename = `screenshot-${id}.png`
          const targetPath = `${outputDir.replace(/\/$/, '')}/${filename}`
          await invoke('copy_screenshot_to', { source: sourcePath, target: targetPath })
        } catch (e) {
          console.warn(`Screenshot ${id} fehlgeschlagen:`, e)
        }
      }

      toast.success(`Screenshots gespeichert in:\n${outputDir}`)
    } catch (e: any) {
      toast.error(e?.message || 'Screenshot-Lauf fehlgeschlagen')
      console.error(e)
    } finally {
      setScreenshotMode(false)
      setRunning(false)
      setProgress('')
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="card"
    >
      <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
        <Camera className="text-sky-400" />
        Dokumentations-Screenshots
      </h3>
      <p className="text-sm text-slate-400 mb-4">
        Erstellt Screenshots aller Menüpunkte für die Dokumentation. Nutzt Platzhalterdaten (keine echten IPs, Benutzernamen oder Passwörter).
        Nur in der Tauri-Desktop-App verfügbar.
      </p>
      {!isTauri ? (
        <p className="text-amber-400 text-sm">Nur in der Tauri-Desktop-App verfügbar – im Browser nicht nutzbar.</p>
      ) : (
        <>
          {progress && (
            <p className="text-sky-300 text-sm mb-3 font-medium">{progress}</p>
          )}
          <button
            onClick={runScreenshots}
            disabled={running}
            className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg font-medium disabled:opacity-50 flex items-center gap-2"
          >
            <Camera size={18} />
            {running ? 'Erstelle Screenshots…' : 'Screenshots erstellen'}
          </button>
          <p className="text-xs text-slate-500 mt-3">
            Speicherort: Dokumente/PI-Installer/docs/screenshots/
          </p>
        </>
      )}
    </motion.div>
  )
}
