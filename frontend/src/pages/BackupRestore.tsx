import React, { useEffect, useRef, useState } from 'react'
import { Cloud, Database, Download, Upload, Trash2, Clock, HardDrive, Lock, Settings } from 'lucide-react'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
import { fetchApi } from '../api'
import SudoPasswordModal from '../components/SudoPasswordModal'

type BackupTab = 'backup' | 'settings' | 'restore'

const BackupRestore: React.FC = () => {
  const [activeTab, setActiveTab] = useState<BackupTab>('backup')
  const [backups, setBackups] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [backupType, setBackupType] = useState<'full' | 'incremental' | 'data'>('full')
  const [targets, setTargets] = useState<any[]>([])
  const [backupDirMode, setBackupDirMode] = useState<'default' | 'usb' | 'cloud' | 'custom'>('default')
  const [backupDir, setBackupDir] = useState('/mnt/backups')
  const [showCloudBackups, setShowCloudBackups] = useState(false)
  const [encryptionEnabled, setEncryptionEnabled] = useState(false)
  const [encryptionMethod, setEncryptionMethod] = useState<'gpg' | 'openssl'>('gpg')
  const [encryptionKey, setEncryptionKey] = useState('')
  const [selectedTarget, setSelectedTarget] = useState<string>('') // mountpoint
  const [selectedDevice, setSelectedDevice] = useState<string>('') // /dev/sdXn for unmounted USB
  const [targetCheck, setTargetCheck] = useState<any>(null)
  const [checkingTarget, setCheckingTarget] = useState(false)
  const [usbInfo, setUsbInfo] = useState<any>(null)
  const [showUsbDialog, setShowUsbDialog] = useState(false)
  const [usbLabel, setUsbLabel] = useState('PI-INSTALLER')
  const [usbDoFormat, setUsbDoFormat] = useState(false)
  const [usbConfirm, setUsbConfirm] = useState('')
  const [usbWorking, setUsbWorking] = useState(false)
  const [sudoModalOpen, setSudoModalOpen] = useState(false)
  const [sudoModalTitle, setSudoModalTitle] = useState('Sudo-Passwort erforderlich')
  const [sudoModalSubtitle, setSudoModalSubtitle] = useState('Für diese Aktion werden Administrator-Rechte benötigt.')
  const [sudoModalConfirmText, setSudoModalConfirmText] = useState('Bestätigen')
  const [pendingAction, setPendingAction] = useState<null | ((sudoPassword: string) => Promise<void>)>(null)
  const DEFAULT_BACKUP_DIR = '/mnt/backups'
  const LAST_DIR_KEY = 'pi_installer_last_backup_dir'
  const [verifying, setVerifying] = useState<Record<string, boolean>>({})
  const [backupSettings, setBackupSettings] = useState<any>(null)
  const [settingsLoading, setSettingsLoading] = useState(false)
  const [backupJob, setBackupJob] = useState<any>(null)
  const backupJobNotifiedRef = useRef<Record<string, boolean>>({})
  const [cloudBackups, setCloudBackups] = useState<any[]>([])
  const [cloudBackupsLoading, setCloudBackupsLoading] = useState(false)
  const [cloudRuleFilter, setCloudRuleFilter] = useState<string>('')
  const [cloudVerifying, setCloudVerifying] = useState<Record<string, boolean>>({})
  const [cloudVerified, setCloudVerified] = useState<Record<string, boolean>>({})

  useEffect(() => {
    loadTargets()
  }, [])

  useEffect(() => {
    loadBackupSettings()
  }, [])

  useEffect(() => {
    if (!backupJob?.job_id) return
    let cancelled = false
    let intervalId: number | null = null
    const tick = async () => {
      try {
        const r = await fetchApi(`/api/backup/jobs/${encodeURIComponent(backupJob.job_id)}`)
        const d = await r.json()
        if (cancelled) return
        if (d.status === 'success' && d.job) {
          const job = d.job
          setBackupJob(job)

          const terminal = job.status === 'success' || job.status === 'error' || job.status === 'cancelled'
          if (terminal) {
            if (!backupJobNotifiedRef.current[job.job_id]) {
              backupJobNotifiedRef.current[job.job_id] = true
              if (job.status === 'success') {
                toast.success('Backup fertig')
                if (job.warning) toast(String(job.warning), { icon: '⚠️', duration: 6000 })
                loadBackups()
                if (job.remote_file) {
                  void loadCloudBackups()
                }
              } else if (job.status === 'cancelled') {
                toast('Backup abgebrochen', { duration: 6000 })
              } else {
                toast.error(job.message || 'Backup fehlgeschlagen', { duration: 10000 })
              }
            }
            if (intervalId) window.clearInterval(intervalId)
            intervalId = null
          }
        }
      } catch {
        // ignore
      }
    }
    tick()
    intervalId = window.setInterval(() => {
      if (!cancelled) tick()
    }, 2000)
    return () => {
      cancelled = true
      if (intervalId) window.clearInterval(intervalId)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backupJob?.job_id])

  useEffect(() => {
    // beim Start: letztes Ziel wiederherstellen (wenn existiert)
    try {
      const last = localStorage.getItem(LAST_DIR_KEY)
      if (last && typeof last === 'string' && last.startsWith('/')) {
        setBackupDirMode(last === DEFAULT_BACKUP_DIR ? 'default' : 'custom')
        setBackupDir(last)
      }
    } catch {
      // ignore
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    loadBackups()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backupDir])

  useEffect(() => {
    checkTarget(backupDir)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backupDir])

  useEffect(() => {
    // letztes Ziel merken (damit "USB/letztes Ziel" schnell wieder erreichbar ist)
    try {
      if (backupDir && typeof backupDir === 'string') {
        localStorage.setItem(LAST_DIR_KEY, backupDir)
      }
    } catch {
      // ignore
    }
  }, [backupDir])

  useEffect(() => {
    // bei USB-Auswahl zusätzlich Device-Infos laden
    if (backupDirMode === 'usb' && (selectedTarget || selectedDevice)) {
      loadUsbInfo(selectedTarget, selectedDevice)
    } else {
      setUsbInfo(null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [backupDirMode, selectedTarget, selectedDevice])

  const loadTargets = async () => {
    try {
      const response = await fetchApi('/api/backup/targets')
      const data = await response.json()
      if (data.status === 'success') {
        setTargets(data.targets || [])
      }
    } catch (error) {
      console.error('Fehler beim Laden der Backup-Ziele:', error)
    } finally {
      // Backups initial laden (Standardziel)
      loadBackups()
    }
  }

  const loadBackups = async () => {
    try {
      const response = await fetchApi(`/api/backup/list?backup_dir=${encodeURIComponent(backupDir)}`)
      const data = await response.json()
      if (data.status === 'success') {
        setBackups(data.backups || [])
      }
    } catch (error) {
      console.error('Fehler beim Laden der Backups:', error)
    }
  }

  const loadBackupSettings = async () => {
    try {
      const r = await fetchApi('/api/backup/settings')
      const d = await r.json()
      if (d.status === 'success') setBackupSettings(d.settings)
    } catch {
      // ignore
    }
  }

  const saveBackupSettings = async () => {
    if (!backupSettings) return
    await requireSudo(
      { title: 'Backup-Einstellungen speichern', subtitle: 'Speichert Einstellungen + konfiguriert den Timer.', confirmText: 'Speichern' },
      async () => {
        setSettingsLoading(true)
        try {
          const r = await fetchApi('/api/backup/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ settings: backupSettings }),
          })
          const d = await r.json()
          if (d.status === 'success') {
            toast.success('Einstellungen gespeichert')
            setBackupSettings(d.settings)
          } else {
            toast.error(d.message || 'Speichern fehlgeschlagen')
          }
        } finally {
          setSettingsLoading(false)
        }
      }
    )
  }

  const runScheduleRuleNow = async (ruleId?: string) => {
    await requireSudo(
      { title: 'Scheduled Backup jetzt ausführen', subtitle: 'Führt den Backup-Runner sofort aus.', confirmText: 'Ausführen' },
      async () => {
        const r = await fetchApi('/api/backup/schedule/run-now', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(ruleId ? { rule_id: ruleId } : {}),
        })
        const d = await r.json()
        if (d.status === 'success') {
          toast.success('Scheduled Backup ausgeführt')
          if (d.stdout) toast.success(String(d.stdout).slice(0, 120), { duration: 6000 })
          loadBackups()
        } else {
          toast.error(String(d.stderr || d.stdout || d.message || 'Ausführung fehlgeschlagen').slice(0, 350), { duration: 12000 })
        }
      }
    )
  }

  // Cloud-Test wurde nach Settings verschoben

  const loadCloudBackups = async () => {
    setCloudBackupsLoading(true)
    try {
      const r = await fetchApi(`/api/backup/cloud/list${cloudRuleFilter ? `?rule_id=${encodeURIComponent(cloudRuleFilter)}` : ''}`)
      const d = await r.json()
      if (d.status === 'success') {
        const backups = Array.isArray(d.backups) ? d.backups : []
        // Konvertiere Cloud-Backups in das gleiche Format wie lokale Backups
        const formattedBackups = backups.map((b: any) => {
          const sizeBytes = b.size_bytes || 0
          const sizeMB = sizeBytes > 0 ? (sizeBytes / 1024 / 1024).toFixed(2) + ' MB' : 'Unbekannt'
          return {
            file: b.href || b.name,
            name: b.name,
            size: sizeMB,
            date: b.last_modified || 'Unbekannt',
            encrypted: b.encrypted || b.name?.endsWith('.gpg') || b.name?.endsWith('.enc'),
            location: 'Cloud',
          }
        })
        setCloudBackups(formattedBackups)
        if (backups.length === 0 && d.message) {
          toast(d.message, { duration: 4000, icon: 'ℹ️' })
        }
      } else {
        toast.error(d.message || 'Externe Backups konnten nicht geladen werden', { duration: 12000 })
        setCloudBackups([])
      }
    } catch (e) {
      toast.error('Externe Backups konnten nicht geladen werden (Backend nicht erreichbar)')
      setCloudBackups([])
    } finally {
      setCloudBackupsLoading(false)
    }
  }

  const verifyCloudBackup = async (name: string) => {
    if (!name) return
    setCloudVerifying((m) => ({ ...m, [name]: true }))
    try {
      const r = await fetchApi('/api/backup/cloud/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      })
      const d = await r.json()
      if (d.status === 'success' && d.ok) {
        setCloudVerified((m) => ({ ...m, [name]: true }))
        toast.success('Remote verifiziert')
      } else {
        setCloudVerified((m) => ({ ...m, [name]: false }))
        toast.error(d.message || `Remote nicht verifiziert (HTTP ${d.http_code ?? '—'})`, { duration: 12000 })
      }
    } catch {
      setCloudVerified((m) => ({ ...m, [name]: false }))
      toast.error('Remote Verifizierung fehlgeschlagen (Backend nicht erreichbar)')
    } finally {
      setCloudVerifying((m) => ({ ...m, [name]: false }))
    }
  }

  const checkTarget = async (dir: string) => {
    setCheckingTarget(true)
    try {
      const res = await fetchApi(`/api/backup/target-check?backup_dir=${encodeURIComponent(dir)}&create=1`)
      const data = await res.json()
      setTargetCheck(data)
    } catch (e) {
      setTargetCheck({ status: 'error', message: 'Backend nicht erreichbar' })
    } finally {
      setCheckingTarget(false)
    }
  }

  const loadUsbInfo = async (mountpoint: string, device: string) => {
    try {
      const qs = mountpoint
        ? `mountpoint=${encodeURIComponent(mountpoint)}`
        : `device=${encodeURIComponent(device)}`
      const res = await fetchApi(`/api/backup/usb/info?${qs}`)
      const data = await res.json()
      setUsbInfo(data)
    } catch (e) {
      setUsbInfo({ status: 'error', message: 'USB-Info konnte nicht geladen werden' })
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

  const requireSudo = async (opts: { title: string; subtitle?: string; confirmText?: string }, action: () => Promise<void>) => {
    // wenn Backend schon ein Passwort in der Session hat, direkt ausführen
    if (await hasSavedSudoPassword()) {
      await action()
      return
    }

    setSudoModalTitle(opts.title)
    setSudoModalSubtitle(opts.subtitle || 'Für diese Aktion werden Administrator-Rechte benötigt.')
    setSudoModalConfirmText(opts.confirmText || 'Bestätigen')
    setPendingAction(() => async (pwd: string) => {
      await storeSudoPassword(pwd)
      await action()
    })
    setSudoModalOpen(true)
  }

  const runUsbPrepare = async () => {
    if (!selectedTarget && !selectedDevice) {
      toast.error('Bitte zuerst einen USB-Stick auswählen')
      return
    }

    if (usbDoFormat) {
      // harte Sicherheitsabfrage
      if (usbConfirm.trim().toUpperCase() !== 'FORMAT') {
        toast.error('Bitte bestätigen Sie mit "FORMAT" (Datenverlust!)')
        return
      }
    }

    await requireSudo(
      { title: 'USB vorbereiten', subtitle: 'Formatieren/Umbenennen benötigt sudo.', confirmText: 'Weiter' },
      async () => {
        setUsbWorking(true)
        try {
          const res = await fetchApi('/api/backup/usb/prepare', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              mountpoint: selectedTarget,
              device: selectedDevice,
              format: usbDoFormat,
              label: usbLabel,
            }),
          })
          const data = await res.json()
          if (data.status === 'success') {
            toast.success('USB vorbereitet')
            if (Array.isArray(data.results)) {
              data.results.forEach((r: string) => toast.success(r, { duration: 3500 }))
            }

            await loadTargets()
            await loadUsbInfo(selectedTarget, selectedDevice)

            if (data.mounted_to) {
              const newDir = `${data.mounted_to}/pi-installer-backups`
              setBackupDirMode('custom')
              setBackupDir(newDir)
              toast.success(`Backup-Ziel gesetzt: ${newDir}`, { duration: 4000 })
            }
            setShowUsbDialog(false)
          } else {
            toast.error(data.message || 'USB vorbereiten fehlgeschlagen')
          }
        } finally {
          setUsbWorking(false)
        }
      }
    )
  }

  const runUsbEject = async () => {
    if (!selectedTarget && !selectedDevice) {
      toast.error('Bitte zuerst einen USB-Stick auswählen')
      return
    }

    if (!window.confirm('USB wirklich auswerfen? Danach können Sie den Stick gefahrlos entfernen.')) return

    await requireSudo(
      { title: 'USB auswerfen', subtitle: 'Unmount + sync (optional power-off).', confirmText: 'Auswerfen' },
      async () => {
        const res = await fetchApi('/api/backup/usb/eject', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            mountpoint: selectedTarget,
            device: selectedDevice,
          }),
        })
        const data = await res.json()
        if (data.status === 'success') {
          toast.success('USB ausgeworfen')
          if (Array.isArray(data.results)) {
            data.results.forEach((r: string) => toast.success(r, { duration: 3000 }))
          }
          await loadTargets()
          setSelectedTarget('')
          setSelectedDevice('')
          setUsbInfo(null)
        } else {
          toast.error(data.message || 'Auswerfen fehlgeschlagen')
          if (Array.isArray(data.still_mounted) && data.still_mounted.length > 0) {
            toast.error(`Noch gemountet: ${data.still_mounted.join(', ')}`, { duration: 8000 })
          }
        }
      }
    )
  }

  const mountSelectedUsb = async (device: string) => {
    if (!device) return
    await requireSudo(
      { title: 'USB mounten', subtitle: 'USB-Stick wird gemountet (nicht-destruktiv).', confirmText: 'Mounten' },
      async () => {
        try {
          const res = await fetchApi('/api/backup/usb/mount', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device }),
          })
          const data = await res.json()
          if (data.status === 'success') {
            await loadTargets()
            if (data.mounted_to) {
              const newDir = `${data.mounted_to}/pi-installer-backups`
              setBackupDirMode('usb')
              setBackupDir(newDir)
              setSelectedTarget(String(data.mounted_to))
              setSelectedDevice('')
              toast.success(`Gemountet: ${data.mounted_to}`, { duration: 4000 })
            } else {
              toast.success('USB ist gemountet', { duration: 4000 })
            }
          } else {
            toast.error(data.message || 'Mount fehlgeschlagen', { duration: 12000 })
          }
        } catch {
          toast.error('Mount fehlgeschlagen (Backend nicht erreichbar)')
        }
      }
    )
  }

  const onUsbSelectChange = async (v: string) => {
    if (v.startsWith('/dev/')) {
      setSelectedDevice(v)
      setSelectedTarget('')
      // ask before mounting (non-destructive, but needs sudo)
      const ok = window.confirm('Der USB-Stick ist nicht gemountet. Soll er jetzt gemountet werden?')
      if (ok) {
        toast('USB wird gemountet…', { duration: 2500 })
        await mountSelectedUsb(v)
      }
    } else {
      setSelectedTarget(v)
      setSelectedDevice('')
      if (v) setBackupDir(`${v}/pi-installer-backups`)
    }
  }

  const createBackup = async () => {
    const isCloudTarget = backupDirMode === 'cloud'
    if (isCloudTarget) {
      if (!backupSettings?.cloud?.enabled) {
        toast.error('Cloud-Upload ist deaktiviert. Bitte in Einstellungen → Cloud-Backup Einstellungen aktivieren.')
        return
      }
      // Prüfe Provider-spezifische Settings
      const provider = backupSettings?.cloud?.provider || 'seafile_webdav'
      if (provider.includes('webdav')) {
        if (!backupSettings?.cloud?.webdav_url || !backupSettings?.cloud?.username || !backupSettings?.cloud?.password) {
          toast.error('Cloud-Settings fehlen. Bitte in Einstellungen → Cloud-Backup Einstellungen konfigurieren.')
          return
        }
      } else if (provider === 's3' || provider === 's3_compatible') {
        if (!backupSettings?.cloud?.bucket || !backupSettings?.cloud?.access_key_id || !backupSettings?.cloud?.secret_access_key) {
          toast.error('S3-Settings fehlen. Bitte in Einstellungen → Cloud-Backup Einstellungen konfigurieren.')
          return
        }
      } else if (provider === 'google_cloud') {
        if (!backupSettings?.cloud?.bucket) {
          toast.error('GCS-Settings fehlen. Bitte in Einstellungen → Cloud-Backup Einstellungen konfigurieren.')
          return
        }
      } else if (provider === 'azure') {
        if (!backupSettings?.cloud?.account_name || !backupSettings?.cloud?.container || !backupSettings?.cloud?.account_key) {
          toast.error('Azure-Settings fehlen. Bitte in Einstellungen → Cloud-Backup Einstellungen konfigurieren.')
          return
        }
      }
    }

    const targetText = isCloudTarget ? 'Cloud (lokal wird nach erfolgreichem Upload gelöscht)' : `lokal in ${backupDir}`
    if (
      !window.confirm(
        `Möchten Sie wirklich ein ${
          backupType === 'full' ? 'vollständiges' : backupType === 'incremental' ? 'inkrementelles' : 'Daten-'
        } Backup erstellen?\n\nZiel: ${targetText}`
      )
    ) {
      return
    }

    await requireSudo(
      { title: 'Backup erstellen', subtitle: 'Backup benötigt sudo (tar/Dateisystemzugriff).', confirmText: 'Backup starten' },
      async () => {
        setLoading(true)
        try {
          const requestBody: any = {
            type: backupType,
            backup_dir: backupDir,
            target: isCloudTarget ? 'cloud_only' : (backupSettings?.cloud?.enabled ? 'local_and_cloud' : 'local'),
            async: true,
          }
          if (encryptionEnabled && encryptionMethod && encryptionKey) {
            requestBody.encryption_method = encryptionMethod
            requestBody.encryption_key = encryptionKey
          }
          
          const backupTypeText = backupType === 'full' ? 'vollständiges' : backupType === 'incremental' ? 'inkrementelles' : 'Daten-'
          const encryptionText = encryptionEnabled ? ` (verschlüsselt mit ${encryptionMethod.toUpperCase()})` : ''
          const targetText = isCloudTarget ? 'Cloud' : `lokal: ${backupDir}`
          
          toast(
            `Backup wird erstellt:\nTyp: ${backupTypeText} Backup${encryptionText}\nZiel: ${targetText}`,
            { 
              duration: 5000,
              icon: 'ℹ️'
            }
          )
          
          const response = await fetchApi('/api/backup/create', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody),
          })
          const data = await response.json()

          if (data.status === 'accepted') {
            toast.success('Backup gestartet…')
            // Setze Backup-Job sofort, damit die Anzeige startet
            const jobData = {
              job_id: data.job_id || String(Date.now()),
              status: 'queued',
              backup_file: data.backup_file || '',
              message: 'Backup wird erstellt…'
            }
            console.log('Setting backupJob:', jobData) // Debug
            setBackupJob(jobData)
            // Starte sofort Polling
            setTimeout(() => {
              const pollJob = async () => {
                try {
                  const r = await fetchApi(`/api/backup/jobs/${encodeURIComponent(data.job_id)}`)
                  const d = await r.json()
                  if (d.status === 'success' && d.job) {
                    console.log('Polling backupJob update:', d.job) // Debug
                    setBackupJob(d.job)
                    if (d.job.status === 'success' || d.job.status === 'error' || d.job.status === 'cancelled') {
                      // Zeige Ergebnis an
                      if (d.job.status === 'success') {
                        toast.success('Backup erfolgreich erstellt!')
                        if (d.job.warning) {
                          toast(d.job.warning, { icon: '⚠️', duration: 8000 })
                        }
                        // Prüfe ob Cloud-Upload erfolgreich war
                        const hasUpload = d.job.results?.some((r: string) => r.includes('uploaded:'))
                        if (isCloudTarget && hasUpload) {
                          toast.success('Backup erfolgreich in die Cloud hochgeladen!', { duration: 6000 })
                          loadCloudBackups() // Lade Cloud-Backups neu
                        } else if (isCloudTarget && !hasUpload) {
                          const uploadFailed = d.job.results?.some((r: string) => r.includes('upload failed'))
                          if (uploadFailed) {
                            toast.error('Cloud-Upload fehlgeschlagen!', { duration: 8000 })
                          }
                        }
                        loadBackups() // Lade lokale Backups neu
                      } else if (d.job.status === 'error') {
                        toast.error(d.job.message || 'Backup fehlgeschlagen', { duration: 10000 })
                        if (d.job.warning) {
                          toast.error(d.job.warning, { duration: 10000 })
                        }
                      }
                      return // Stop polling
                    }
                    setTimeout(pollJob, 2000) // Continue polling
                  }
                } catch (e) {
                  console.error('Polling error:', e) // Debug
                }
              }
              pollJob()
            }, 500)
          } else if (data.status === 'success') {
            // fallback (falls async nicht unterstützt)
            toast.success('Backup erstellt!')
            loadBackups()
          } else {
            toast.error(data.message || 'Fehler beim Erstellen des Backups')
            if (Array.isArray(data.results)) {
              data.results.forEach((r: string) => toast.error(r, { duration: 5000 }))
            }
          }
        } finally {
          setLoading(false)
        }
      }
    )
  }

  const cancelBackupJob = async () => {
    if (!backupJob?.job_id) return
    if (!window.confirm('Backup wirklich abbrechen?')) return
    try {
      const r = await fetchApi(`/api/backup/jobs/${encodeURIComponent(backupJob.job_id)}/cancel`, { method: 'POST' })
      const d = await r.json()
      if (d.status === 'success') {
        toast.success('Abbruch angefordert…')
        setBackupJob((j: any) => (j ? { ...j, status: 'cancel_requested' } : j))
      } else {
        toast.error(d.message || 'Abbruch fehlgeschlagen')
      }
    } catch {
      toast.error('Abbruch fehlgeschlagen (Backend nicht erreichbar)')
    }
  }

  const restoreBackup = async (backupFile: string) => {
    if (!window.confirm(`WARNUNG: Möchten Sie wirklich das Backup ${backupFile} wiederherstellen? Dies überschreibt alle aktuellen Daten!`)) {
      return
    }

    if (!window.confirm('Sind Sie SICHER? Diese Aktion kann nicht rückgängig gemacht werden!')) {
      return
    }

    await requireSudo(
      { title: 'Backup wiederherstellen', subtitle: 'Restore benötigt sudo. Achtung: überschreibt Dateien.', confirmText: 'Restore starten' },
      async () => {
        setLoading(true)
        try {
          const response = await fetchApi('/api/backup/restore', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              backup_file: backupFile,
            }),
          })
          const data = await response.json()

          if (data.status === 'success') {
            toast.success('Backup wiederhergestellt! System-Neustart empfohlen.')
            if (data.warning) toast(data.warning, { icon: '⚠️' })
          } else {
            toast.error(data.message || 'Fehler beim Wiederherstellen')
          }
        } finally {
          setLoading(false)
        }
      }
    )
  }

  const verifyBackup = async (backupFile: string, mode: 'gzip' | 'tar' | 'sha256' = 'gzip') => {
    await requireSudo(
      { title: 'Backup verifizieren', subtitle: 'Prüft die Integrität des Backups.', confirmText: 'Verifizieren' },
      async () => {
        setVerifying((m) => ({ ...m, [backupFile]: true }))
        try {
          const res = await fetchApi('/api/backup/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ backup_file: backupFile, mode }),
          })
          const data = await res.json()
          if (data.status === 'success') {
            toast.success(`Verifiziert (${data.mode}) in ${data.duration_ms}ms`)
            if (data.sha256) {
              toast.success(`SHA256: ${String(data.sha256).slice(0, 16)}…`, { duration: 6000 })
            }
          } else {
            toast.error(`Verifizierung fehlgeschlagen: ${data.message || data.stderr || 'Unbekannt'}`, { duration: 9000 })
          }
        } finally {
          setVerifying((m) => ({ ...m, [backupFile]: false }))
        }
      }
    )
  }

  const deleteBackup = async (backupFile: string) => {
    if (!window.confirm(`Backup wirklich löschen?\n\n${backupFile}`)) return
    await requireSudo(
      { title: 'Backup löschen', subtitle: 'Löscht die Backup-Datei (ggf. mit sudo).', confirmText: 'Löschen' },
      async () => {
        const res = await fetchApi('/api/backup/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ backup_file: backupFile }),
        })
        const data = await res.json()
        if (data.status === 'success') {
          toast.success('Backup gelöscht')
          loadBackups()
        } else {
          toast.error(data.message || data.stderr || 'Löschen fehlgeschlagen', { duration: 10000 })
        }
      }
    )
  }

  return (
    <div className="space-y-8 animate-fade-in page-transition">
      <SudoPasswordModal
        open={sudoModalOpen}
        title={sudoModalTitle}
        subtitle={sudoModalSubtitle}
        confirmText={sudoModalConfirmText}
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
      {/* USB Prepare Dialog */}
      {showUsbDialog && (
        <div className="fixed inset-0 z-50">
          <div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={() => !usbWorking && setShowUsbDialog(false)}
          />
          <div className="absolute inset-0 flex items-center justify-center p-4">
            <div
              className="card bg-slate-800/95 border border-slate-700 max-w-xl w-full shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-start justify-between gap-4 mb-4">
                <div>
                  <h2 className="text-2xl font-bold text-white">USB vorbereiten</h2>
                  <p className="text-sm text-slate-400">
                    Optional formatieren (löschen) und/oder umbenennen (Label).
                  </p>
                </div>
                <button
                  className="px-3 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg"
                  onClick={() => !usbWorking && setShowUsbDialog(false)}
                >
                  Schließen
                </button>
              </div>

              <div className="p-4 bg-yellow-900/20 border border-yellow-700/40 rounded-lg text-yellow-100 text-sm mb-4">
                <div className="font-semibold mb-1">Warnung</div>
                <div>
                  Wenn du „Formatieren“ aktivierst, werden <span className="font-semibold">alle Daten auf dem Stick unwiderruflich gelöscht</span>.
                  Prüfe unbedingt, dass du den richtigen Datenträger ausgewählt hast.
                </div>
              </div>

              <div className="space-y-4">
                <div className="p-3 bg-slate-900/40 border border-slate-700 rounded-lg text-sm text-slate-200">
                  <div className="font-semibold text-white mb-1">Ausgewählt</div>
                  <div className="text-xs text-slate-300 whitespace-pre-line">
                    Mountpoint: {selectedTarget || '—'}
                    {"\n"}Device: {usbInfo?.disk || '—'} • Partition: {usbInfo?.partition || '—'}
                    {"\n"}FS: {usbInfo?.fstype || '—'} • Label: {usbInfo?.label || '—'} • Größe: {usbInfo?.size || '—'}
                  </div>
                </div>

                <label className="flex items-center gap-3 p-3 bg-slate-900/40 border border-slate-700 rounded-lg">
                  <input
                    type="checkbox"
                    checked={usbDoFormat}
                    onChange={(e) => setUsbDoFormat(e.target.checked)}
                    className="w-5 h-5 accent-red-500"
                  />
                  <div className="text-sm">
                    <div className="font-semibold text-white">Stick löschen / formatieren (ext4)</div>
                    <div className="text-xs text-slate-400">Empfohlen wenn der Stick „read-only“ ist (z.B. ISO/Boot-Stick).</div>
                  </div>
                </label>

                <div>
                  <label className="block text-sm font-semibold text-white mb-2">Neuer Name (Label)</label>
                  <input
                    value={usbLabel}
                    onChange={(e) => setUsbLabel(e.target.value)}
                    placeholder="PI-INSTALLER"
                    className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-sky-600"
                  />
                  <div className="mt-1 text-xs text-slate-400">
                    Wird als Laufwerksname verwendet. (Erlaubt: Buchstaben/Zahlen/Leerzeichen/_/-)
                  </div>
                </div>

                {usbDoFormat && (
                  <div>
                    <label className="block text-sm font-semibold text-white mb-2">
                      Bestätigung (tippe <span className="text-red-300">FORMAT</span>)
                    </label>
                    <input
                      value={usbConfirm}
                      onChange={(e) => setUsbConfirm(e.target.value)}
                      placeholder="FORMAT"
                      className="w-full bg-slate-900/50 border border-red-700/60 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-red-500"
                    />
                  </div>
                )}
              </div>

              <div className="mt-6 flex gap-3">
                <button
                  className="flex-1 px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg"
                  disabled={usbWorking}
                  onClick={() => setShowUsbDialog(false)}
                >
                  Abbrechen
                </button>
                <button
                  className="flex-1 px-4 py-3 bg-red-600 hover:bg-red-500 text-white rounded-lg disabled:opacity-50"
                  disabled={usbWorking || (usbDoFormat && usbConfirm.trim().toUpperCase() !== 'FORMAT')}
                  onClick={runUsbPrepare}
                >
                  {usbWorking ? '⏳ Bitte warten…' : usbDoFormat ? 'Formatieren & Umbenennen' : 'Umbenennen / Mounten'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <div>
        <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
          <Database className="text-purple-500" />
          Backup & Restore
        </h1>
        <p className="text-slate-400">
          Erstellen und Wiederherstellen von System-Backups
        </p>
      </div>

      {/* Tabs */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card">
        <div className="flex gap-2 border-b border-slate-700 mb-6">
          <button
            onClick={() => setActiveTab('backup')}
            className={`px-4 py-2 font-medium transition-all relative flex items-center gap-2 ${
              activeTab === 'backup'
                ? 'text-sky-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Download size={18} />
            Backup erstellen
            {activeTab === 'backup' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400"
                initial={false}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            )}
          </button>
          <button
            onClick={() => setActiveTab('settings')}
            className={`px-4 py-2 font-medium transition-all relative flex items-center gap-2 ${
              activeTab === 'settings'
                ? 'text-sky-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Settings size={18} />
            Einstellungen
            {activeTab === 'settings' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400"
                initial={false}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            )}
          </button>
          <button
            onClick={() => setActiveTab('restore')}
            className={`px-4 py-2 font-medium transition-all relative flex items-center gap-2 ${
              activeTab === 'restore'
                ? 'text-sky-400'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <HardDrive size={18} />
            Vorhandene Backups
            {activeTab === 'restore' && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400"
                initial={false}
                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
              />
            )}
          </button>
        </div>
      </motion.div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        transition={{ duration: 0.2 }}
      >
      {activeTab === 'backup' && (
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Backup erstellen */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card"
          >
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <Download className="text-green-500" />
              Backup erstellen
            </h2>

            <div className="space-y-4">
              {/* Backup-Job Anzeige (Backup läuft) – nur im Tab Backup erstellen */}
              {backupJob && backupJob.job_id &&
               (backupJob.status === 'queued' ||
                backupJob.status === 'running' ||
                backupJob.status === 'cancel_requested' ||
                !backupJob.status ||
                backupJob.status === undefined) && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="p-4 bg-sky-900/20 border border-sky-700/40 rounded-lg text-sky-100"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                          className="w-5 h-5 border-2 border-sky-400 border-t-transparent rounded-full"
                        />
                        <div className="font-semibold">
                          {backupJob.status === 'cancel_requested' ? '⏳ Abbruch läuft…' : backupJob.message?.includes('Prüfe') ? '☁️ Prüfe Cloud…' : backupJob.message?.includes('Upload') ? '☁️ Upload läuft…' : '⏳ Backup läuft…'}
                        </div>
                      </div>
                      <div className="text-xs text-sky-100/80 mt-1">
                        {backupJob.backup_file ? `Datei: ${String(backupJob.backup_file).split('/').pop()}` : backupJob.job_id ? `Job-ID: ${backupJob.job_id}` : ''}
                      </div>
                      <div className="text-xs text-sky-100/80 mt-1">
                        Status: <span className="font-semibold">{backupJob.status || 'queued'}</span>
                        {typeof backupJob.bytes_current === 'number' ? ` • Größe: ${(backupJob.bytes_current / 1024 / 1024).toFixed(1)} MB` : ''}
                      </div>
                      {backupJob.message?.includes('Verschlüsselung') && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: [0.5, 1, 0.5] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                          className="mt-2 p-2 bg-purple-800/30 rounded border border-purple-600/40"
                        >
                          <div className="flex items-center gap-2 text-sm">
                            <Lock className="animate-pulse" size={16} />
                            <span>Verschlüsselung läuft…</span>
                          </div>
                        </motion.div>
                      )}
                      {(backupJob.message?.includes('Upload') || backupJob.message?.includes('Prüfe') || backupJob.results?.some((r: string) => String(r).includes('upload'))) && !backupJob.remote_file && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: [0.5, 1, 0.5] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                          className="mt-2 p-2 bg-sky-800/30 rounded border border-sky-600/40"
                        >
                          <div className="flex items-center gap-2 text-sm">
                            <Cloud className="animate-pulse" size={16} />
                            <span>
                              {backupJob.message?.includes('Prüfe') ? 'Prüfe in 1 Min, ob Datei in Cloud…' : 'Upload zu Cloud läuft…'}
                              {typeof backupJob.upload_progress_pct === 'number' && (
                                <span className="ml-2 font-semibold">{backupJob.upload_progress_pct} %</span>
                              )}
                            </span>
                          </div>
                          {typeof backupJob.upload_progress_pct === 'number' && (
                            <div className="mt-2 h-1.5 bg-sky-900/50 rounded-full overflow-hidden">
                              <motion.div
                                className="h-full bg-sky-400"
                                initial={{ width: 0 }}
                                animate={{ width: `${backupJob.upload_progress_pct}%` }}
                                transition={{ type: 'tween', duration: 0.3 }}
                              />
                            </div>
                          )}
                        </motion.div>
                      )}
                      {backupJob.remote_file && (
                        <motion.div
                          initial={{ opacity: 0, scale: 0.9 }}
                          animate={{ opacity: 1, scale: 1 }}
                          className="mt-2 p-2 bg-green-900/30 rounded border border-green-600/40"
                        >
                          <div className="text-sm text-green-300 flex items-center gap-2">
                            <span>✓</span>
                            <span>Upload erfolgreich: {String(backupJob.remote_file).split('/').pop()}</span>
                          </div>
                        </motion.div>
                      )}
                      {backupJob.warning && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="mt-2 p-2 bg-yellow-900/30 rounded border border-yellow-600/40"
                        >
                          <div className="text-sm text-yellow-300">⚠ {String(backupJob.warning)}</div>
                        </motion.div>
                      )}
                      {Array.isArray(backupJob.results) && backupJob.results.length > 0 && (
                        <div className="mt-2 space-y-1 text-xs">
                          {backupJob.results.map((r: string, idx: number) => (
                            <motion.div
                              key={idx}
                              initial={{ opacity: 0, x: -10 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: idx * 0.1 }}
                              className={String(r).includes('failed') ? 'text-red-300' : String(r).includes('uploaded') ? 'text-green-300' : 'text-sky-100/80'}
                            >
                              {String(r).includes('uploaded') && <Cloud size={12} className="inline mr-1" />}
                              {String(r)}
                            </motion.div>
                          ))}
                        </div>
                      )}
                    </div>
                    {(backupJob.status === 'queued' || backupJob.status === 'running') && (
                      <button
                        onClick={cancelBackupJob}
                        className="px-3 py-2 bg-red-600/25 hover:bg-red-600/35 border border-red-500/40 text-red-100 rounded-lg text-sm"
                      >
                        Abbrechen
                      </button>
                    )}
                  </div>
                </motion.div>
              )}
              <div>
                <label className="block text-white font-semibold mb-2">Ziel (Backup-Speicherort)</label>
                <div className="grid md:grid-cols-4 gap-3">
                  <button
                    onClick={() => {
                      setBackupDirMode('default')
                      setBackupDir(DEFAULT_BACKUP_DIR)
                    }}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      backupDirMode === 'default'
                        ? 'bg-sky-600/20 border-sky-500'
                        : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
                    }`}
                  >
                    <div className="font-bold text-white mb-1">Standard</div>
                    <div className="text-xs text-slate-400">/mnt/backups</div>
                  </button>

                  <button
                    onClick={() => {
                      setBackupDirMode('usb')
                      const mounted = (targets || []).find((t: any) => t.mountpoint && String(t.mountpoint).startsWith('/'))
                      const unmounted = (targets || []).find((t: any) => t.device && String(t.device).startsWith('/dev/'))
                      const mp = mounted?.mountpoint
                      const dev = unmounted?.device
                      if (mp) {
                        setSelectedTarget(mp)
                        setSelectedDevice('')
                        setBackupDir(`${mp}/pi-installer-backups`)
                      } else if (dev) {
                        setSelectedDevice(dev)
                        setSelectedTarget('')
                      } else {
                        setSelectedTarget('')
                        setSelectedDevice('')
                        setBackupDir(DEFAULT_BACKUP_DIR)
                      }
                    }}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      backupDirMode === 'usb'
                        ? 'bg-sky-600/20 border-sky-500'
                        : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
                    }`}
                  >
                    <div className="font-bold text-white mb-1">USB / Datenträger</div>
                    <div className="text-xs text-slate-400">Mountpoint auswählen</div>
                  </button>

                  <button
                    onClick={() => {
                      setBackupDirMode('cloud')
                      // local staging dir stays as-is; default to standard if unset
                      if (!backupDir || typeof backupDir !== 'string') setBackupDir(DEFAULT_BACKUP_DIR)
                      toast('Cloud-Ziel gewählt: Backup wird hochgeladen und lokal gelöscht (nach Verifizierung).', { duration: 4500 })
                    }}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      backupDirMode === 'cloud'
                        ? 'bg-sky-600/20 border-sky-500'
                        : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
                    }`}
                  >
                    <div className="font-bold text-white mb-1 flex items-center gap-2">
                      <Cloud size={18} className="text-sky-300" />
                      Cloud
                    </div>
                    <div className="text-xs text-slate-400">WebDAV Upload (Cloud-only)</div>
                  </button>

                  <button
                    onClick={() => setBackupDirMode('custom')}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      backupDirMode === 'custom'
                        ? 'bg-sky-600/20 border-sky-500'
                        : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
                    }`}
                  >
                    <div className="font-bold text-white mb-1">Eigener Pfad</div>
                    <div className="text-xs text-slate-400">z.B. /media/pi/USB</div>
                  </button>
                </div>

                {backupDirMode === 'cloud' && (
                  <div className="mt-3 p-3 bg-sky-900/20 border border-sky-700/40 rounded-lg text-sky-100 text-sm">
                    <div className="font-semibold mb-1">Cloud-Backup</div>
                    <div className="text-xs text-sky-100/80">
                      Upload erfolgt über WebDAV (Backup-Einstellungen → Cloud). Die lokale Datei wird nach erfolgreichem Upload & Verifizierung gelöscht.
                    </div>
                    {!backupSettings?.cloud?.enabled && (
                      <div className="mt-2 text-xs text-yellow-200">Hinweis: Cloud-Upload ist aktuell deaktiviert. Bitte unten bei Backup-Einstellungen aktivieren.</div>
                    )}
                  </div>
                )}

                {backupDirMode === 'usb' && (
                  <div className="mt-3">
                    <label className="block text-sm text-slate-300 mb-2">Datenträger / Mountpoint</label>
                    {(targets || []).length === 0 && (
                      <div className="mb-3 p-3 bg-yellow-900/20 border border-yellow-700/40 rounded-lg text-yellow-100 text-sm">
                        <div className="font-semibold mb-1">Kein Datenträger erkannt</div>
                        <div className="text-xs text-yellow-100/80">
                          Aktuell meldet das System keinen USB-Stick. Falls du gerade „Auswerfen“ genutzt hast: Stick kurz abziehen und wieder anstecken,
                          dann auf „Neu scannen“ klicken.
                        </div>
                        <button
                          type="button"
                          onClick={() => loadTargets()}
                          className="mt-3 px-3 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg border border-slate-600 transition-all text-sm"
                        >
                          Neu scannen
                        </button>
                      </div>
                    )}
                    <select
                      value={selectedTarget || selectedDevice}
                      onChange={(e) => {
                        const v = e.target.value
                        void onUsbSelectChange(v)
                      }}
                      className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-sky-600"
                    >
                      <option value="">(Kein Datenträger erkannt)</option>
                      {(targets || []).map((t: any, idx: number) => (
                        <option key={idx} value={t.mountpoint || t.device || ''}>
                          {t.mountpoint ? t.mountpoint : `${t.device} (nicht gemountet)`}
                          {t.label ? ` (${t.label})` : ''} {t.size ? `- ${t.size}` : ''} {t.tran ? `- ${t.tran}` : ''} {t.model ? `- ${t.model}` : ''}
                        </option>
                      ))}
                    </select>
                    <p className="mt-2 text-xs text-slate-400">
                      {selectedDevice && !selectedTarget ? (
                        <span className="inline-flex items-center gap-2 flex-wrap">
                          <span>
                            Stick ist nicht gemountet.
                            <span className="text-slate-200 font-semibold"> USB vorbereiten…</span> (Format/Label) oder
                          </span>
                          <button
                            type="button"
                            onClick={() => void mountSelectedUsb(selectedDevice)}
                            className="px-2 py-1 bg-slate-700/60 hover:bg-slate-700 text-white rounded-md border border-slate-600 transition-all text-xs"
                          >
                            jetzt mounten
                          </button>
                        </span>
                      ) : (
                        <>Backup wird in <span className="text-slate-200 font-semibold">{backupDir}</span> erstellt.</>
                      )}
                    </p>

                    {/* USB-Hinweis + Aktion */}
                    {(selectedTarget || selectedDevice) && (
                      <div className="mt-3 p-3 bg-slate-900/40 border border-slate-700 rounded-lg">
                        <div className="flex items-start justify-between gap-3">
                          <div className="text-sm text-slate-300">
                            <div className="font-semibold text-white">USB Status</div>
                            {usbInfo?.status === 'success' ? (
                              <div className="text-xs text-slate-400 mt-1 whitespace-pre-line">
                                Device: {usbInfo.disk} • Partition: {usbInfo.partition}
                                {"\n"}FS: {usbInfo.fstype || '—'} • Label: {usbInfo.label || '—'} • Größe: {usbInfo.size || '—'}
                                {"\n"}USB: {usbInfo.is_usb ? 'ja' : 'nein'} • Removable: {usbInfo.is_removable ? 'ja' : 'nein'}
                              </div>
                            ) : (
                              <div className="text-xs text-red-300 mt-1">{usbInfo?.message || 'USB-Info nicht verfügbar'}</div>
                            )}
                          </div>
                          <div className="flex flex-col gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                setUsbDoFormat(false)
                                setUsbConfirm('')
                                setUsbLabel('PI-INSTALLER')
                                setShowUsbDialog(true)
                              }}
                              className="px-3 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-200 rounded-lg border border-red-700/40 transition-all text-sm"
                            >
                              USB vorbereiten…
                            </button>
                            <button
                              type="button"
                              onClick={runUsbEject}
                              className="px-3 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg border border-slate-600 transition-all text-sm"
                            >
                              Auswerfen
                            </button>
                          </div>
                        </div>
                        {!checkingTarget && targetCheck?.status === 'success' && targetCheck?.write_test?.success === false && (
                          <div className="mt-2 text-xs text-yellow-200">
                            Hinweis: Schreibtest ist fehlgeschlagen. Der Stick ist evtl. schreibgeschützt oder im falschen Dateisystem (z.B. ISO). „USB vorbereiten…“ kann das beheben (Datenverlust).
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {backupDirMode === 'custom' && (
                  <div className="mt-3">
                    <label className="block text-sm text-slate-300 mb-2">Backup-Verzeichnis (absoluter Pfad)</label>
                    <input
                      value={backupDir}
                      onChange={(e) => setBackupDir(e.target.value)}
                      placeholder="/media/…/pi-installer-backups"
                      className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-sky-600"
                    />
                    <p className="mt-2 text-xs text-slate-400">
                      Hinweis: Erlaubte Root-Pfade sind typischerweise <span className="text-slate-200">/mnt</span>, <span className="text-slate-200">/media</span>, <span className="text-slate-200">/run/media</span> oder <span className="text-slate-200">/home</span>.
                    </p>
                  </div>
                )}

                {/* Ziel-Status (Speicherplatz + Schreibtest) */}
                <div className="mt-4 p-4 bg-slate-900/40 border border-slate-700 rounded-lg">
                  <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <div className="text-sm font-semibold text-white">Ziel-Status</div>
                      <div className="text-xs text-slate-400 truncate">{backupDir}</div>
                    </div>
                    <div className="text-xs text-slate-300">
                      {checkingTarget ? '⏳ Prüfe…' : ' '}
                    </div>
                  </div>

                  {!checkingTarget && targetCheck?.status === 'success' && (
                    <div className="mt-3 grid sm:grid-cols-3 gap-3 text-sm">
                      <div className="p-3 bg-slate-800/40 border border-slate-700 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Freier Speicher</div>
                        <div className="font-semibold text-white">
                          {targetCheck.fs?.free_human ?? '—'}
                          <span className="text-slate-400 font-normal">
                            {targetCheck.fs?.total_human ? ` / ${targetCheck.fs.total_human}` : ''}
                          </span>
                        </div>
                        {typeof targetCheck.fs?.used_percent === 'number' && (
                          <div className="text-xs text-slate-400">{targetCheck.fs.used_percent}% belegt</div>
                        )}
                      </div>
                      <div className="p-3 bg-slate-800/40 border border-slate-700 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Verzeichnis</div>
                        <div className={`font-semibold ${targetCheck.exists && targetCheck.is_dir ? 'text-green-300' : 'text-yellow-300'}`}>
                          {targetCheck.exists ? (targetCheck.is_dir ? 'OK' : 'Kein Ordner') : 'Nicht vorhanden'}
                        </div>
                        {targetCheck.created && <div className="text-xs text-slate-400">Wurde erstellt</div>}
                      </div>
                      <div className="p-3 bg-slate-800/40 border border-slate-700 rounded-lg">
                        <div className="text-xs text-slate-400 mb-1">Schreibtest</div>
                        <div className={`font-semibold ${targetCheck.write_test?.success ? 'text-green-300' : 'text-red-300'}`}>
                          {targetCheck.write_test?.success ? 'OK' : 'Fehler'}
                        </div>
                        <div className="text-xs text-slate-400">
                          {targetCheck.write_test?.message ?? '—'}
                        </div>
                        {!targetCheck.write_test?.success && Array.isArray(targetCheck.write_test?.hints) && targetCheck.write_test.hints.length > 0 && (
                          <div className="mt-2 text-xs text-yellow-200/90 whitespace-pre-line">
                            {targetCheck.write_test.hints.join('\n')}
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {!checkingTarget && targetCheck?.status === 'error' && (
                    <div className="mt-3 text-sm text-red-300">
                      {targetCheck.message || 'Ziel konnte nicht geprüft werden'}
                    </div>
                  )}
                </div>
              </div>

              <div>
                <label className="block text-white font-semibold mb-2">Backup-Typ</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { 
                      id: 'full', 
                      label: 'Vollständig', 
                      desc: 'Gesamtes System',
                      hint: 'Komplettes System-Backup inkl. Betriebssystem, installierte Pakete und alle Dateien. Empfohlen für erste Sicherung oder nach größeren Änderungen. Größte Dateigröße, aber vollständige Wiederherstellung möglich.'
                    },
                    { 
                      id: 'incremental', 
                      label: 'Inkrementell', 
                      desc: 'Nur Änderungen',
                      hint: 'Nur Änderungen seit dem letzten Voll-Backup werden gesichert. Schneller und kleiner als Voll-Backup, benötigt aber das letzte Voll-Backup zur Wiederherstellung. Ideal für regelmäßige Backups.'
                    },
                    { 
                      id: 'data', 
                      label: 'Daten', 
                      desc: 'Nur Daten',
                      hint: 'Nur Benutzerdaten werden gesichert (/home, /var/www, /opt). Schnellste Option, aber kein Betriebssystem-Backup. Ideal wenn nur Daten gesichert werden sollen.'
                    },
                  ].map((type) => (
                    <button
                      key={type.id}
                      onClick={() => setBackupType(type.id as any)}
                      className={`p-4 rounded-lg border-2 transition-all relative group text-left ${
                        backupType === type.id
                          ? 'bg-sky-600/20 border-sky-500'
                          : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
                      }`}
                    >
                      <div className="font-bold text-white mb-1">{type.label}</div>
                      <div className="text-xs text-slate-400">{type.desc}</div>
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-slate-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 w-72">
                        {type.hint}
                        <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-900"></div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Verschlüsselung */}
              <div className="p-4 bg-slate-900/40 border border-slate-700 rounded-lg">
                <label className="flex items-center gap-3 mb-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={encryptionEnabled}
                    onChange={(e) => setEncryptionEnabled(e.target.checked)}
                    className="w-5 h-5 accent-purple-500"
                  />
                  <div>
                    <div className="font-semibold text-white">Verschlüsselung aktivieren</div>
                    <div className="text-xs text-slate-400">Backup wird verschlüsselt gespeichert</div>
                  </div>
                </label>
                {encryptionEnabled && (
                  <div className="space-y-3 mt-3">
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Verschlüsselungsmethode</div>
                      <select
                        value={encryptionMethod}
                        onChange={(e) => setEncryptionMethod(e.target.value as 'gpg' | 'openssl')}
                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      >
                        <option value="gpg">GPG (AES-256)</option>
                        <option value="openssl">OpenSSL (AES-256-CBC)</option>
                      </select>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">
                        Verschlüsselungsschlüssel {encryptionMethod === 'openssl' && '(erforderlich)'}
                      </div>
                      <input
                        type="password"
                        value={encryptionKey}
                        onChange={(e) => setEncryptionKey(e.target.value)}
                        placeholder={encryptionMethod === 'gpg' ? 'Optional (leer = ohne Passphrase)' : 'Passwort eingeben'}
                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      />
                      <div className="text-xs text-slate-500 mt-1">
                        {encryptionMethod === 'gpg'
                          ? 'GPG: Ohne Schlüssel wird nur komprimiert'
                          : 'OpenSSL: Schlüssel ist erforderlich'}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <button
                onClick={createBackup}
                disabled={loading || (encryptionEnabled && encryptionMethod === 'openssl' && !encryptionKey)}
                className="btn-primary w-full"
              >
                {loading ? '⏳ Erstelle Backup...' : '💾 Backup erstellen'}
              </button>
            </div>
          </motion.div>
        </div>
        <div className="space-y-4">
          <div className="card bg-gradient-to-br from-yellow-900/30 to-yellow-900/10 border-yellow-500/50">
            <h3 className="text-lg font-bold text-yellow-300 mb-3">⚠️ Wichtige Hinweise</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>• Standard-Ziel ist /mnt/backups (oder ein ausgewählter Mountpoint)</li>
              <li>• Restore überschreibt aktuelle Daten</li>
              <li>• System-Neustart nach Restore empfohlen</li>
              <li>• Regelmäßige Backups sind wichtig!</li>
            </ul>
          </div>
        </div>
      </div>
      )}

      {activeTab === 'restore' && (
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Backup-Liste */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card"
          >
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <HardDrive className="text-blue-500" />
              Verfügbare Backups
            </h2>

            {/* Schnellwechsel Ziel & Filter */}
            <div className="mb-4 p-4 bg-slate-900/40 border border-slate-700 rounded-lg space-y-3">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <div className="text-sm font-semibold text-white">Schnellwechsel</div>
                  <div className="text-xs text-slate-400 truncate">
                    Aktuelles Ziel: <span className="text-slate-200 font-semibold">{backupDir}</span>
                  </div>
                </div>
                <div className="flex gap-2 flex-wrap justify-end">
                  <button
                    onClick={() => {
                      setBackupDirMode('default')
                      setBackupDir(DEFAULT_BACKUP_DIR)
                    }}
                    className={`px-3 py-2 rounded-lg border text-sm transition-all ${
                      backupDir === DEFAULT_BACKUP_DIR
                        ? 'bg-sky-600/20 border-sky-500 text-white'
                        : 'bg-slate-800/40 border-slate-700 text-slate-200 hover:border-slate-500'
                    }`}
                  >
                    Standard
                  </button>
                  <button
                    onClick={() => {
                      // heuristisch: wenn wir schon im USB-Pfad sind, bleib; sonst springe zum letzten Ziel
                      let last = ''
                      try {
                        last = localStorage.getItem(LAST_DIR_KEY) || ''
                      } catch {
                        last = ''
                      }
                      const candidate =
                        backupDir.startsWith('/mnt/pi-installer-usb/')
                          ? backupDir
                          : (last && last !== DEFAULT_BACKUP_DIR ? last : backupDir)
                      if (candidate && candidate.startsWith('/')) {
                        setBackupDirMode(candidate === DEFAULT_BACKUP_DIR ? 'default' : 'custom')
                        setBackupDir(candidate)
                      }
                    }}
                    className={`px-3 py-2 rounded-lg border text-sm transition-all ${
                      backupDir.startsWith('/mnt/pi-installer-usb/')
                        ? 'bg-sky-600/20 border-sky-500 text-white'
                        : 'bg-slate-800/40 border-slate-700 text-slate-200 hover:border-slate-500'
                    }`}
                  >
                    USB / letztes Ziel
                  </button>
                  <button
                    onClick={() => loadBackups()}
                    className="px-3 py-2 rounded-lg border text-sm transition-all bg-slate-800/40 border-slate-700 text-slate-200 hover:border-slate-500"
                  >
                    Aktualisieren
                  </button>
                </div>
              </div>
              {/* Filter */}
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Filter:</span>
                <select
                  value={showCloudBackups ? 'cloud' : backupDir}
                  onChange={(e) => {
                    if (e.target.value === 'cloud') {
                      setShowCloudBackups(true)
                      loadCloudBackups()
                    } else {
                      setShowCloudBackups(false)
                      setBackupDir(e.target.value)
                      setBackupDirMode(e.target.value === DEFAULT_BACKUP_DIR ? 'default' : 'custom')
                      loadBackups()
                    }
                  }}
                  className="flex-1 bg-slate-800/50 border border-slate-600 rounded-lg px-3 py-1.5 text-white text-sm"
                >
                  <option value={DEFAULT_BACKUP_DIR}>Lokal: {DEFAULT_BACKUP_DIR}</option>
                  {backupDir !== DEFAULT_BACKUP_DIR && !showCloudBackups && <option value={backupDir}>Aktuell: {backupDir}</option>}
                  <option value="cloud">Cloud-Backups</option>
                </select>
              </div>
            </div>

            {showCloudBackups ? (
              cloudBackupsLoading ? (
                <div className="text-center py-8 text-slate-400">
                  <Clock size={48} className="mx-auto mb-4 opacity-50 animate-spin" />
                  <p>Lade Cloud-Backups…</p>
                </div>
              ) : cloudBackups.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <Clock size={48} className="mx-auto mb-4 opacity-50" />
                  <p>Keine Cloud-Backups gefunden</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {cloudBackups.map((backup: any, index: number) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="p-4 bg-slate-700/30 rounded-lg border border-slate-600 flex items-center justify-between"
                    >
                      <div className="flex-1">
                        <div className="font-semibold text-white mb-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span>{backup.file?.split('/').pop() || backup.name || 'Unbekannt'}</span>
                            <span className="text-xs px-2 py-1 rounded-full bg-sky-600/25 border border-sky-400/40 text-sky-200">
                              Cloud
                            </span>
                            {(backup.encrypted === true || String(backup.file || backup.name || '').endsWith('.gpg') || String(backup.file || backup.name || '').endsWith('.enc') || String(backup.file || backup.name || '').includes('.tar.gz.gpg') || String(backup.file || backup.name || '').includes('.tar.gz.enc')) && (
                              <span className="text-xs px-2 py-1 rounded-full bg-purple-600/30 border border-purple-400/40 text-purple-200 flex items-center gap-1">
                                <Lock size={12} />
                                Verschlüsselt
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-slate-400">
                          {backup.size && <span>📦 {backup.size}</span>}
                          {backup.date && <span>📅 {backup.date}</span>}
                          <span className="text-xs">📍 Cloud</span>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )
            ) : backups.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <Clock size={48} className="mx-auto mb-4 opacity-50" />
                <p>Keine Backups gefunden</p>
                <p className="text-sm mt-2">Tipp: prüfen Sie das Ziel-Verzeichnis oben im Schnellwechsel</p>
              </div>
            ) : (
              <div className="space-y-3">
                {backups.map((backup, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="p-4 bg-slate-700/30 rounded-lg border border-slate-600 flex items-center justify-between"
                  >
                    <div className="flex-1">
                      <div className="font-semibold text-white mb-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span>{backup.file.split('/').pop()}</span>
                          {String(backup.file).includes('pi-backup-inc-') && (
                            <span className="text-xs px-2 py-1 rounded-full bg-purple-600/30 border border-purple-400/40 text-purple-200">
                              Inkrementell
                            </span>
                          )}
                          {String(backup.file).includes('pi-backup-full-') && (
                            <span className="text-xs px-2 py-1 rounded-full bg-sky-600/25 border border-sky-400/40 text-sky-200">
                              Vollständig
                            </span>
                          )}
                          {String(backup.file).includes('pi-backup-data-') && (
                            <span className="text-xs px-2 py-1 rounded-full bg-emerald-600/25 border border-emerald-400/40 text-emerald-200">
                              Daten
                            </span>
                          )}
                          {(backup.encrypted === true || String(backup.file).endsWith('.gpg') || String(backup.file).endsWith('.enc') || String(backup.file).includes('.tar.gz.gpg') || String(backup.file).includes('.tar.gz.enc')) && (
                            <span className="text-xs px-2 py-1 rounded-full bg-purple-600/30 border border-purple-400/40 text-purple-200 flex items-center gap-1">
                              <Lock size={12} />
                              Verschlüsselt
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-slate-400">
                        <span>📦 {backup.size}</span>
                        <span>📅 {backup.date}</span>
                        {backup.location && <span className="text-xs">📍 {backup.location}</span>}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => deleteBackup(backup.file)}
                        className="px-3 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/40 text-red-100 rounded-lg transition-all flex items-center gap-2 text-sm"
                      >
                        <Trash2 size={18} />
                        Löschen
                      </button>
                      <button
                        onClick={() => verifyBackup(backup.file, 'gzip')}
                        disabled={!!verifying[backup.file]}
                        className="px-3 py-2 bg-slate-700/60 hover:bg-slate-700 text-white rounded-lg transition-all text-sm disabled:opacity-50"
                      >
                        {verifying[backup.file] ? '⏳ Prüfe…' : 'Verifizieren'}
                      </button>
                      <button
                        onClick={() => restoreBackup(backup.file)}
                        className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all flex items-center gap-2"
                      >
                        <Upload size={18} />
                        Wiederherstellen
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        </div>
        <div className="space-y-4">
          <div className="card bg-gradient-to-br from-yellow-900/30 to-yellow-900/10 border-yellow-500/50">
            <h3 className="text-lg font-bold text-yellow-300 mb-3">⚠️ Wichtige Hinweise</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>• Standard-Ziel ist /mnt/backups (oder ein ausgewählter Mountpoint)</li>
              <li>• Restore überschreibt aktuelle Daten</li>
              <li>• System-Neustart nach Restore empfohlen</li>
              <li>• Regelmäßige Backups sind wichtig!</li>
            </ul>
          </div>
        </div>
      </div>
      )}

      {activeTab === 'settings' && (
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card"
          >
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <Settings className="text-purple-500" />
              Backup-Einstellungen & Zeitsteuerung
            </h2>
            <div className="space-y-4">
              <div className="card bg-gradient-to-br from-sky-900/25 to-sky-900/10 border-sky-500/30">
                <h3 className="text-lg font-bold text-sky-300 mb-3">⚙️ Backup-Einstellungen</h3>
              {!backupSettings ? (
                <div className="text-sm text-slate-300">
                  <button className="px-3 py-2 bg-slate-700/50 hover:bg-slate-700 rounded-lg" onClick={loadBackupSettings}>
                    Einstellungen laden
                  </button>
                </div>
              ) : (
                <div className="space-y-4 text-sm text-slate-200">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Standard: Backups behalten</div>
                    <input
                      type="number"
                      min={1}
                      max={100}
                      value={backupSettings.retention?.keep_last ?? 5}
                      onChange={(e) =>
                        setBackupSettings((s: any) => ({ ...s, retention: { ...(s.retention || {}), keep_last: Number(e.target.value) } }))
                      }
                      className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-3 py-2 text-white"
                    />
                    <div className="mt-1 text-xs text-slate-400">Kann pro Regel überschrieben werden.</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Regeln</div>
                    <button
                      type="button"
                      onClick={() =>
                        setBackupSettings((s: any) => ({
                          ...s,
                          schedules: Array.isArray(s.schedules)
                            ? s.schedules.concat([
                                {
                                  id: `rule-${Date.now()}`,
                                  enabled: true,
                                  name: 'Neue Regel',
                                  type: 'incremental',
                                  target: 'cloud_only',
                                  keep_last: s.retention?.keep_last ?? 5,
                                  days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                                  time: '02:00',
                                  dataset: 'personal_default',
                                  incremental: false,
                                },
                              ])
                            : [
                                {
                                  id: `rule-${Date.now()}`,
                                  enabled: true,
                                  name: 'Neue Regel',
                                  type: 'incremental',
                                  target: 'cloud_only',
                                  keep_last: s.retention?.keep_last ?? 5,
                                  days: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                                  time: '02:00',
                                  dataset: 'personal_default',
                                  incremental: false,
                                },
                              ],
                        }))
                      }
                      className="w-full px-3 py-2 bg-slate-700/60 hover:bg-slate-700 text-white rounded-lg"
                    >
                      + Regel hinzufügen
                    </button>
                  </div>
                </div>

                <div className="p-3 bg-slate-900/40 border border-slate-700 rounded-lg">
                  <div className="font-semibold text-white mb-2">Zeitplan-Regeln</div>
                  {Array.isArray(backupSettings.schedules) && backupSettings.schedules.length > 0 ? (
                    <div className="space-y-3">
                      {backupSettings.schedules.map((rule: any, idx: number) => (
                        <div key={rule.id || idx} className="p-3 bg-slate-950/40 border border-slate-800 rounded-lg">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0 flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <input
                                  type="checkbox"
                                  className="w-5 h-5 accent-sky-500"
                                  checked={!!rule.enabled}
                                  onChange={(e) =>
                                    setBackupSettings((s: any) => ({
                                      ...s,
                                      schedules: (s.schedules || []).map((r: any) => (r === rule ? { ...r, enabled: e.target.checked } : r)),
                                    }))
                                  }
                                />
                                <input
                                  value={rule.name ?? ''}
                                  onChange={(e) =>
                                    setBackupSettings((s: any) => ({
                                      ...s,
                                      schedules: (s.schedules || []).map((r: any) => (r === rule ? { ...r, name: e.target.value } : r)),
                                    }))
                                  }
                                  className="flex-1 bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm"
                                  placeholder="Name"
                                />
                              </div>

                              <div className="grid grid-cols-2 gap-2">
                                <div>
                                  <div className="text-xs text-slate-400 mb-1">Typ</div>
                                  <select
                                    value={rule.type ?? 'incremental'}
                                    onChange={(e) =>
                                      setBackupSettings((s: any) => ({
                                        ...s,
                                        schedules: (s.schedules || []).map((r: any) => (r === rule ? { ...r, type: e.target.value } : r)),
                                      }))
                                    }
                                    className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm"
                                  >
                                    <option value="full">Full</option>
                                    <option value="incremental">Inkrementell</option>
                                    <option value="data">Daten (Home/WWW/Opt)</option>
                                    <option value="personal">Persönliche Daten (/home/*)</option>
                                  </select>
                                </div>
                                <div>
                                  <div className="text-xs text-slate-400 mb-1">Ziel</div>
                                  <select
                                    value={rule.target ?? 'cloud_only'}
                                    onChange={(e) =>
                                      setBackupSettings((s: any) => ({
                                        ...s,
                                        schedules: (s.schedules || []).map((r: any) => (r === rule ? { ...r, target: e.target.value } : r)),
                                      }))
                                    }
                                    className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm"
                                  >
                                    <option value="cloud_only">Cloud (lokal löschen)</option>
                                    <option value="local_and_cloud">Lokal + Cloud</option>
                                    <option value="local">Nur lokal</option>
                                  </select>
                                </div>
                                <div>
                                  <div className="text-xs text-slate-400 mb-1">Tage</div>
                                  <div className="flex flex-wrap gap-2">
                                    {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((d) => (
                                      <label key={d} className="text-xs text-slate-200 flex items-center gap-1">
                                        <input
                                          type="checkbox"
                                          className="accent-sky-500"
                                          checked={Array.isArray(rule.days) ? rule.days.includes(d) : false}
                                          onChange={(e) => {
                                            const next = Array.isArray(rule.days) ? [...rule.days] : []
                                            if (e.target.checked) {
                                              if (!next.includes(d)) next.push(d)
                                            } else {
                                              const i = next.indexOf(d)
                                              if (i >= 0) next.splice(i, 1)
                                            }
                                            setBackupSettings((s: any) => ({
                                              ...s,
                                              schedules: (s.schedules || []).map((r: any) => (r === rule ? { ...r, days: next } : r)),
                                            }))
                                          }}
                                        />
                                        {d}
                                      </label>
                                    ))}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-xs text-slate-400 mb-1">Uhrzeit</div>
                                  <input
                                    value={rule.time ?? '02:00'}
                                    onChange={(e) =>
                                      setBackupSettings((s: any) => ({
                                        ...s,
                                        schedules: (s.schedules || []).map((r: any) => (r === rule ? { ...r, time: e.target.value } : r)),
                                      }))
                                    }
                                    className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm"
                                    placeholder="02:00"
                                  />
                                </div>
                                <div>
                                  <div className="text-xs text-slate-400 mb-1">Behalten</div>
                                  <input
                                    type="number"
                                    min={1}
                                    max={100}
                                    value={rule.keep_last ?? backupSettings.retention?.keep_last ?? 5}
                                    onChange={(e) =>
                                      setBackupSettings((s: any) => ({
                                        ...s,
                                        schedules: (s.schedules || []).map((r: any) => (r === rule ? { ...r, keep_last: Number(e.target.value) } : r)),
                                      }))
                                    }
                                    className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm"
                                  />
                                </div>
                                {rule.type === 'personal' && (
                                  <div className="col-span-2">
                                    <div className="text-xs text-slate-400 mb-1">Persönliche Ordner (für alle /home/*)</div>
                                    <div className="flex flex-wrap gap-2">
                                      {['Downloads', 'Documents', 'Pictures', 'Images', 'Videos', 'Desktop'].map((f) => (
                                        <label key={f} className="text-xs text-slate-200 flex items-center gap-1">
                                          <input
                                            type="checkbox"
                                            className="accent-sky-500"
                                            checked={Array.isArray(backupSettings.datasets?.personal_default?.folders) ? backupSettings.datasets.personal_default.folders.includes(f) : false}
                                            onChange={(e) => {
                                              const cur = Array.isArray(backupSettings.datasets?.personal_default?.folders)
                                                ? [...backupSettings.datasets.personal_default.folders]
                                                : []
                                              if (e.target.checked) {
                                                if (!cur.includes(f)) cur.push(f)
                                              } else {
                                                const i = cur.indexOf(f)
                                                if (i >= 0) cur.splice(i, 1)
                                              }
                                              setBackupSettings((s: any) => ({
                                                ...s,
                                                datasets: { ...(s.datasets || {}), personal_default: { ...(s.datasets?.personal_default || {}), folders: cur } },
                                                schedules: (s.schedules || []).map((r: any) =>
                                                  r === rule ? { ...r, dataset: 'personal_default' } : r
                                                ),
                                              }))
                                            }}
                                          />
                                          {f}
                                        </label>
                                      ))}
                                    </div>
                                    <label className="mt-2 flex items-center gap-2 text-xs text-slate-200">
                                      <input
                                        type="checkbox"
                                        className="accent-sky-500"
                                        checked={!!rule.incremental}
                                        onChange={(e) =>
                                          setBackupSettings((s: any) => ({
                                            ...s,
                                            schedules: (s.schedules || []).map((r: any) => (r === rule ? { ...r, incremental: e.target.checked } : r)),
                                          }))
                                        }
                                      />
                                      Inkrementell (auf Basis des letzten Personal-Full dieser Regel)
                                    </label>
                                  </div>
                                )}
                              </div>
                            </div>
                            <div className="flex flex-col gap-2">
                              <button
                                type="button"
                                onClick={() => void runScheduleRuleNow(String(rule.id))}
                                className="px-3 py-2 bg-slate-700/60 hover:bg-slate-700 text-white rounded-lg text-sm"
                              >
                                Jetzt ausführen
                              </button>
                              <button
                                type="button"
                                onClick={() =>
                                  setBackupSettings((s: any) => ({
                                    ...s,
                                    schedules: (s.schedules || []).filter((r: any) => r !== rule),
                                  }))
                                }
                                className="px-3 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/40 text-red-100 rounded-lg text-sm"
                              >
                                Entfernen
                              </button>
                              <div className="text-xs text-slate-400">
                                Timer: {backupSettings._timer_status?.[rule.id]?.enabled || '—'} / {backupSettings._timer_status?.[rule.id]?.active || '—'}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-slate-400">Keine Regeln vorhanden.</div>
                  )}
                </div>

                <div className="p-3 bg-slate-900/40 border border-slate-700 rounded-lg">
                  <div className="font-semibold text-white mb-2">Cloud-Backups</div>
                  <div className="text-xs text-slate-400 mb-3">
                    Cloud-Konfiguration unter{' '}
                    <span className="text-sky-400 font-semibold">Einstellungen → Cloud-Backup Einstellungen</span>
                  </div>
                  {backupSettings.cloud?.enabled ? (
                    <div className="space-y-2">
                      <div>
                        <div className="text-xs text-slate-400 mb-1">Cloud-Anbieter auswählen</div>
                        <select
                          value={backupSettings.cloud?.provider || 'seafile_webdav'}
                          onChange={async (e) => {
                            const newProvider = e.target.value
                            const updated = {
                              ...backupSettings,
                              cloud: { ...backupSettings.cloud, provider: newProvider }
                            }
                            setBackupSettings(updated)
                            // Speichere sofort
                            try {
                              const r = await fetchApi('/api/backup/settings', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ settings: updated }),
                              })
                              const d = await r.json()
                              if (d.status === 'success') {
                                toast.success('Cloud-Anbieter gespeichert')
                                setBackupSettings(d.settings)
                              }
                            } catch {
                              toast.error('Fehler beim Speichern')
                            }
                          }}
                          className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
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
                      {Array.isArray(backupSettings.schedules) && backupSettings.schedules.length > 0 && (
                        <div className="p-2 bg-slate-950/30 border border-slate-800 rounded-lg">
                          <div className="text-xs text-slate-400 mb-1">Filter externe Backups nach Regel</div>
                          <select
                            value={cloudRuleFilter}
                            onChange={(e) => setCloudRuleFilter(e.target.value)}
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm"
                          >
                            <option value="">(Alle)</option>
                            {backupSettings.schedules.map((r: any, idx: number) => (
                              <option key={r.id || idx} value={String(r.id || '')}>
                                {r.name ? `${r.name} (${String(r.id || '')})` : String(r.id || '')}
                              </option>
                            ))}
                          </select>
                        </div>
                      )}
                      <button
                        onClick={loadCloudBackups}
                        disabled={cloudBackupsLoading}
                        className="w-full px-3 py-2 bg-slate-700/60 hover:bg-slate-700 text-white rounded-lg disabled:opacity-50"
                      >
                        {cloudBackupsLoading ? '⏳ Lade externe Backups…' : 'Externe Backups anzeigen'}
                      </button>

                      {cloudBackups.length > 0 && (
                        <div className="mt-2 p-2 bg-slate-950/40 border border-slate-800 rounded-lg">
                          <div className="text-xs text-slate-400 mb-2">Externe Backups</div>
                          <div className="space-y-1 max-h-44 overflow-auto">
                            {cloudBackups.map((b: any, idx: number) => (
                              <div key={idx} className="text-xs text-slate-200 flex items-center justify-between gap-2">
                                <span className="truncate">{b.name || b.href || '—'}</span>
                                <div className="flex items-center gap-2">
                                  {b.name && (
                                    <button
                                      type="button"
                                      onClick={() => void verifyCloudBackup(String(b.name))}
                                      disabled={!!cloudVerifying[String(b.name)]}
                                      className="px-2 py-1 bg-slate-800/50 hover:bg-slate-800 border border-slate-700 rounded-md text-xs text-white disabled:opacity-50"
                                    >
                                      {cloudVerifying[String(b.name)] ? '⏳' : cloudVerified[String(b.name)] === true ? '✓' : 'Verifizieren'}
                                    </button>
                                  )}
                                  {typeof b.size_bytes === 'number' && (
                                    <span className="text-slate-400 whitespace-nowrap">{(b.size_bytes / 1024 / 1024).toFixed(1)} MB</span>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-xs text-yellow-300">
                      Cloud-Upload ist deaktiviert. Aktiviere es in den Einstellungen.
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={saveBackupSettings}
                    disabled={settingsLoading}
                    className="w-full px-3 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg disabled:opacity-50"
                  >
                    {settingsLoading ? '⏳ Übernehme…' : 'Einstellungen übernehmen'}
                  </button>
                </div>
              </div>
            )}
            </div>
          </div>
        </motion.div>
        </div>
        <div className="space-y-4">
          <div className="card bg-gradient-to-br from-yellow-900/30 to-yellow-900/10 border-yellow-500/50">
            <h3 className="text-lg font-bold text-yellow-300 mb-3">⚠️ Hinweise Backup & Zeitsteuerung</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>• Standard-Ziel ist /mnt/backups (oder ein ausgewählter Mountpoint)</li>
              <li>• Restore überschreibt aktuelle Daten</li>
              <li>• System-Neustart nach Restore empfohlen</li>
              <li>• Regelmäßige Backups sind wichtig!</li>
            </ul>
          </div>
        </div>
      </div>
      )}
      </motion.div>
    </div>
  )
}

export default BackupRestore
