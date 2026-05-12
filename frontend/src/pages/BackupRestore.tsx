import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Cloud, Database, Download, Upload, Trash2, Clock, HardDrive, Lock, Settings, CheckSquare, Square, Copy, Usb, FolderOpen, ClipboardCheck } from 'lucide-react'
import AppIcon from '../components/AppIcon'
import toast from 'react-hot-toast'
import { motion } from 'framer-motion'
import { fetchApi } from '../api'
import { postDiagnosisInterpret } from '../api/diagnosisApi'
import { postDiagnosticsAnalyze } from '../api/diagnosticsApi'
import DiagnosisPanel from '../components/DiagnosisPanel'
import DiagnosticsAssistantPanel from '../components/DiagnosticsAssistantPanel'
import { PandaCompanion, PandaRail, PandaHelperStrip, type PandaStatus } from '../components/companions'
import PageHeader from '../components/layout/PageHeader'
import type { ExperienceLevel } from '../components/Sidebar'
import BeginnerGuidanceMarker from '../beginner/BeginnerGuidanceMarker'
import { TrafficLightBadge } from '../components/trafficLight/TrafficLightBadge'
import { deriveBackupSafetyTrafficLight } from '../trafficLight/trafficLightModel'
import SudoPasswordModal from '../components/SudoPasswordModal'
import type { DiagnosisRecord } from '../types/diagnosis'
import type { DiagnosticsAnalyzeResponse, DiagnosticsUserLevel } from '../types/diagnostics'
import { usePlatform } from '../context/PlatformContext'
import type { TFunction } from 'i18next'

type BackupTab = 'backup' | 'settings' | 'restore' | 'clone'

interface BackupRestoreProps {
  experienceLevel?: ExperienceLevel
}

/** Trägt nur einen i18n-Code (kein Backend-Freitext). */
class BackupI18nError extends Error {
  readonly code: string
  constructor(code: string) {
    super(code)
    this.name = 'BackupI18nError'
    this.code = code
  }
}

/** API-Vertrag Phase 2A: `backup.*` mit Punkten oder Legacy-Kurzcodes ohne Punkte. */
function pickStructuredCode(payload: unknown): string | null {
  if (!payload || typeof payload !== 'object') return null
  const o = payload as Record<string, unknown>
  for (const k of ['message_code', 'error_code', 'code']) {
    const v = o[k]
    if (typeof v === 'string' && v.trim()) {
      const raw = v.trim()
      const withoutMsgPrefix = raw.replace(/^backup\.messages\./i, '')
      if (/^backup\.[a-z0-9_.]+$/i.test(withoutMsgPrefix)) return withoutMsgPrefix
      if (/^[a-z][a-z0-9_]*$/i.test(withoutMsgPrefix)) return withoutMsgPrefix
    }
  }
  return null
}

/** `backup.success` → i18n-Suffix `success` (Key `backup.messages.success`). */
function backupApiCodeToI18nSuffix(code: string): string {
  const c = code.trim()
  if (c.startsWith('backup.')) return c.slice('backup.'.length).replace(/\./g, '_')
  return c.replace(/^backup\.messages\./i, '')
}

/** LEGACY_TRANSITION: Nur wenn das Backend noch kein `code` liefert (z. B. ältere Cloud-Listen). */
function inferBackupMessageCode(rawMessage: unknown, status?: unknown, ctx?: string): string {
  const s = String(rawMessage ?? '').trim()
  const st = String(status ?? '').toLowerCase()
  const lower = s.toLowerCase()

  if (ctx === 'clone_terminal') {
    if (st === 'success') return 'clone_success'
    if (st === 'cancelled') return 'clone_cancelled'
    if (st === 'error') return 'clone_failed'
  }
  if (ctx === 'clone_running') {
    if (st === 'cancel_requested') return 'clone_cancel_pending'
    return 'clone_running_detail'
  }

  if (!s) {
    if (st === 'error') return 'generic_error'
    if (st === 'success') return 'generic_success'
    return 'unknown'
  }

  if (s.includes('Job nicht gefunden') || lower.includes('job not found')) return 'job_not_found'
  if (s.includes('Job ist bereits abgeschlossen') || lower.includes('job already')) return 'job_already_done'
  if (s.includes('Einstellungen gespeichert') || lower.includes('settings saved')) return 'settings_saved'
  if (s.includes('Konnte Settings nicht speichern') || lower.includes('could not save settings')) return 'settings_save_failed'
  if (s.includes('Ungültiger Backup-Pfad')) return 'invalid_backup_path'
  if (s.includes('Sudo-Passwort gespeichert') || lower.includes('sudo password saved')) return 'sudo_saved'
  if (s.includes('Sudo-Passwort falsch') || lower.includes('sudo password wrong') || lower.includes('wrong password')) return 'sudo_wrong'
  if (s.includes('Sudo-Test hat zu lange') || lower.includes('sudo test') && lower.includes('long')) return 'sudo_test_timeout'
  if (s.includes('Passwort erforderlich') && ctx === 'sudo') return 'sudo_password_required'
  if (s.includes('Backup erstellt') || (lower.includes('backup') && lower.includes('created'))) return 'backup_created'
  if (s.includes('Backup fehlgeschlagen') || (lower.includes('backup') && lower.includes('failed'))) return 'backup_failed'
  if (s.includes('Backup abgebrochen') || (lower.includes('backup') && lower.includes('cancelled'))) return 'backup_cancelled'
  if (s.includes('Abbruch angefordert') || lower.includes('cancellation requested')) return 'cancel_requested'
  if (s.includes('Prüfe in 1 Min') || (lower.includes('check') && lower.includes('cloud'))) return 'cloud_check_pending'
  if (lower.includes('upload failed') || s.includes('Upload fehlgeschlagen')) return 'upload_failed'
  if (s.includes('Klon erfolgreich') || (lower.includes('clone') && lower.includes('success'))) return 'clone_success'
  if (s.includes('Klon fehlgeschlagen') || (lower.includes('clone') && lower.includes('fail'))) return 'clone_failed'
  if (s.includes('Klon abgebrochen') || (lower.includes('clone') && lower.includes('cancel'))) return 'clone_cancelled'
  if (s.includes('Klon läuft') || (lower.includes('clone') && lower.includes('running'))) return 'clone_running_detail'
  if (lower.includes('test restore') || s.includes('Test-Restore')) return 'restore_preview_status'
  if (lower.includes('verify') || lower.includes('verifizierung')) return 'verify_failed_generic'
  if (lower.includes('löschung fehlgeschlagen') || lower.includes('delete failed')) return 'delete_failed'
  if (lower.includes('no space') || s.includes('Speicherplatz')) return 'backup_no_space'
  if (lower.includes('unbekannter backup-typ') || lower.includes('unknown backup type')) return 'unknown_backup_type'

  return 'unknown'
}

/** UI-Phase primär aus `job.code`, sonst Übergang über Statuszeile (nicht als Nutzertext). */
function inferBackupJobUiPhase(job: {
  code?: unknown
  message?: unknown
  results?: unknown[]
} | null): 'check_cloud' | 'upload' | 'encrypt' | 'running' {
  const jc = String(job?.code ?? '').trim()
  if (jc === 'backup.job.encrypting') return 'encrypt'
  if (jc === 'backup.cloud_check_pending') return 'check_cloud'
  if (jc === 'backup.job.uploading') return 'upload'
  if (
    jc === 'backup.cloud_credentials_missing' ||
    jc === 'backup.cloud_upload_skipped' ||
    jc === 'backup.cloud_upload_file_missing'
  ) {
    return 'upload'
  }
  const m = String(job?.message ?? '').toLowerCase()
  const results = job?.results
  const hasUploadLine =
    Array.isArray(results) && results.some((x) => String(x).toLowerCase().includes('upload'))
  if (m.includes('verschlüsselung') || m.includes('encryption')) return 'encrypt'
  if (m.includes('prüfe') || (m.includes('check') && m.includes('cloud'))) return 'check_cloud'
  if (m.includes('upload') || hasUploadLine) return 'upload'
  return 'running'
}

function resolveApiFeedbackCode(payload: unknown, ctx?: string): string {
  const fromPayload = pickStructuredCode(payload)
  if (fromPayload) return fromPayload
  if (payload && typeof payload === 'object') {
    const o = payload as Record<string, unknown>
    const nestedJob = o.job
    if (nestedJob && typeof nestedJob === 'object') {
      const fromJob = pickStructuredCode(nestedJob)
      if (fromJob) return fromJob
    }
    if (ctx === 'cloud_verify' && o.status !== 'success' && typeof o.http_code === 'number') return 'cloud_verify_http'
  }
  if (payload && typeof payload === 'object') {
    const o = payload as Record<string, unknown>
    return inferBackupMessageCode(o.message, o.status, ctx)
  }
  return 'unknown'
}

function backupMsgParams(payload: unknown): Record<string, string | number> {
  const p: Record<string, string | number> = {}
  if (!payload || typeof payload !== 'object') return p
  const o = payload as Record<string, unknown>
  if (typeof o.http_code === 'number') p.code = o.http_code
  return p
}

function backupMsg(tFn: TFunction, code: string, params?: Record<string, string | number>): string {
  const suffix = backupApiCodeToI18nSuffix(code)
  const key = `backup.messages.${suffix}`
  const translated = params && Object.keys(params).length ? tFn(key, { ...params } as Record<string, unknown>) : tFn(key)
  return translated === key ? tFn('backup.messages.unknown') : translated
}

function toastFromApi(
  toastFn: typeof toast,
  tFn: TFunction,
  kind: 'success' | 'error' | 'info',
  payload: unknown,
  ctx?: string,
  opts?: { duration?: number; icon?: string },
) {
  const code = resolveApiFeedbackCode(payload, ctx)
  const params = backupMsgParams(payload)
  const msg = backupMsg(tFn, code, params)
  if (kind === 'success') toastFn.success(msg, opts as Record<string, unknown>)
  else if (kind === 'error') toastFn.error(msg, opts as Record<string, unknown>)
  else toastFn(msg, opts as Record<string, unknown>)
}

const BackupRestore: React.FC<BackupRestoreProps> = ({ experienceLevel = 'beginner' }) => {
  const { t } = useTranslation()
  const { pageSubtitleLabel } = usePlatform()
  const isBeginnerBackupUx = experienceLevel === 'beginner'
  const [activeTab, setActiveTab] = useState<BackupTab>('backup')
  const [backups, setBackups] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [backupType, setBackupType] = useState<'full' | 'incremental' | 'data'>('full')
  const [targets, setTargets] = useState<any[]>([])
  const [backupDirMode, setBackupDirMode] = useState<'default' | 'usb' | 'cloud' | 'custom'>('default')
  const [backupDir, setBackupDir] = useState('/mnt/setuphelfer/backups')
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
  const [usbLabel, setUsbLabel] = useState('')
  const [usbDoFormat, setUsbDoFormat] = useState(false)
  const [usbConfirm, setUsbConfirm] = useState('')
  const [usbWorking, setUsbWorking] = useState(false)
  const [sudoModalOpen, setSudoModalOpen] = useState(false)
  const [sudoModalTitle, setSudoModalTitle] = useState(t('backup.i18n.sudoRequiredTitle'))
  const [sudoModalSubtitle, setSudoModalSubtitle] = useState(t('backup.i18n.sudoRequiredSubtitle'))
  const [sudoModalConfirmText, setSudoModalConfirmText] = useState(t('backup.i18n.confirm'))
  const [pendingAction, setPendingAction] = useState<null | ((sudoPassword: string, skipTest?: boolean) => Promise<void>)>(null)
  const DEFAULT_BACKUP_DIR = '/mnt/setuphelfer/backups'
  const LAST_DIR_KEY = 'pi_installer_last_backup_dir'
  const BACKUP_JOB_STORAGE_KEY = 'pi_installer_running_backup_job'
  const [verifying, setVerifying] = useState<Record<string, boolean>>({})
  const [verifyDiagnosis, setVerifyDiagnosis] = useState<DiagnosisRecord | null>(null)
  const [structuredDiagnostics, setStructuredDiagnostics] = useState<DiagnosticsAnalyzeResponse | null>(null)
  const [backupSettings, setBackupSettings] = useState<any>(null)
  const [settingsLoading, setSettingsLoading] = useState(false)
  const [backupJob, setBackupJob] = useState<any>(null)
  const backupJobNotifiedRef = useRef<Record<string, boolean>>({})
  const [cloudBackups, setCloudBackups] = useState<any[]>([])
  const [cloudBackupsLoading, setCloudBackupsLoading] = useState(false)
  const [cloudBaseUrl, setCloudBaseUrl] = useState<string>('')
  const [cloudRuleFilter, setCloudRuleFilter] = useState<string>('')
  const [cloudVerifying, setCloudVerifying] = useState<Record<string, boolean>>({})
  const [cloudVerified, setCloudVerified] = useState<Record<string, boolean>>({})
  const [selectedBackups, setSelectedBackups] = useState<Set<string>>(new Set())
  const [selectedCloudBackups, setSelectedCloudBackups] = useState<Set<string>>(new Set())
  const [cloneDiskInfo, setCloneDiskInfo] = useState<any>(null)
  const [cloneTargetDevice, setCloneTargetDevice] = useState<string>('')
  const [cloneJob, setCloneJob] = useState<any>(null)
  const cloneJobNotifiedRef = useRef<Record<string, boolean>>({})
  const [restorePreviewResult, setRestorePreviewResult] = useState<{
    backupFile: string
    previewDir: string
    analysis: any
    totalEntries: number
  } | null>(null)
  const [deepVerifyOpen, setDeepVerifyOpen] = useState(false)
  const [deepVerifyFile, setDeepVerifyFile] = useState<string | null>(null)
  const [deepVerifyKey, setDeepVerifyKey] = useState('')
  const [sawSudoRequiredForBackupRun, setSawSudoRequiredForBackupRun] = useState(false)

  const diagnosticsLevel: DiagnosticsUserLevel =
    experienceLevel === 'beginner' ? 'beginner' : experienceLevel === 'advanced' ? 'advanced' : 'expert'

  useEffect(() => {
    loadTargets()
  }, [])

  useEffect(() => {
    loadBackupSettings()
  }, [])

  useEffect(() => {
    if (activeTab === 'clone') {
      loadCloneDiskInfo()
    }
  }, [activeTab])

  const loadCloneDiskInfo = async (withSudoPassword?: string, forceRefresh = false) => {
    try {
      const opts: RequestInit = {}
      if (withSudoPassword) {
        opts.method = 'POST'
        opts.headers = { 'Content-Type': 'application/json' }
        opts.body = JSON.stringify({ sudo_password: withSudoPassword })
      }
      const url = `/api/backup/clone/disk-info${forceRefresh ? '?refresh=1' : ''}`
      const r = await fetchApi(url, opts)
      const d = await r.json()
      if (d.status === 'success') {
        setCloneDiskInfo({ source: d.source, boot: d.boot, targets: d.targets || [] })
        if (d.targets?.length && !cloneTargetDevice) {
          setCloneTargetDevice(d.targets[0]?.device || '')
        }
      } else {
        setCloneDiskInfo({ source: {}, boot: {}, targets: [] })
      }
    } catch {
      setCloneDiskInfo({ source: {}, boot: {}, targets: [] })
    }
  }

  const loadCloneDiskInfoWithSudo = async () => {
    await requireSudo(
      { title: t('backup.i18n.clone.loadTargets.title'), subtitle: t('backup.i18n.clone.loadTargets.subtitle'), confirmText: t('backup.i18n.clone.loadTargets.confirm') },
      async (pwd?: string) => {
        if (pwd) await storeSudoPassword(pwd, true)
        await loadCloneDiskInfo(pwd, true)
        toast.success(t('backup.i18n.clone.targetsRefreshed'))
      }
    )
  }

  useEffect(() => {
    if (!cloneJob?.job_id) return
    let cancelled = false
    let intervalId: number | null = null
    const tick = async () => {
      try {
        const r = await fetchApi(`/api/backup/jobs/${encodeURIComponent(cloneJob.job_id)}`)
        const d = await r.json()
        if (cancelled) return
        if (d.status === 'success' && d.job) {
          const job = d.job
          setCloneJob(job)
          const terminal = job.status === 'success' || job.status === 'error' || job.status === 'cancelled'
          if (terminal && !cloneJobNotifiedRef.current[job.job_id]) {
            cloneJobNotifiedRef.current[job.job_id] = true
            if (job.status === 'success') {
              toast.success(t('backup.i18n.clone.successReboot'))
              loadCloneDiskInfo()
            } else if (job.status === 'cancelled') {
              toast(t('backup.i18n.clone.cancelled'), { duration: 6000 })
            } else {
              toast.error(backupMsg(t, resolveApiFeedbackCode(job, 'clone_job')), { duration: 10000 })
            }
            if (intervalId) window.clearInterval(intervalId)
          }
        }
      } catch {
        /* ignore */
      }
    }
    tick()
    intervalId = window.setInterval(() => {
      if (!cancelled) tick()
    }, 5000)
    return () => {
      cancelled = true
      if (intervalId) window.clearInterval(intervalId)
    }
  }, [cloneJob?.job_id])

  useEffect(() => {
    if (activeTab !== 'backup') setVerifyDiagnosis(null)
  }, [activeTab])

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
          
          // Speichere Job-State in localStorage für globale Komponente
          try {
            const isRunning = job.status === 'queued' || job.status === 'running' || job.status === 'cancel_requested' || !job.status
            if (isRunning) {
              localStorage.setItem(BACKUP_JOB_STORAGE_KEY, JSON.stringify(job))
            } else {
              // Entferne nach kurzer Verzögerung
              setTimeout(() => {
                localStorage.removeItem(BACKUP_JOB_STORAGE_KEY)
              }, 5000)
            }
          } catch {
            // ignore
          }

          const terminal = job.status === 'success' || job.status === 'error' || job.status === 'cancelled'
          if (terminal) {
            if (!backupJobNotifiedRef.current[job.job_id]) {
              backupJobNotifiedRef.current[job.job_id] = true
              if (job.status === 'success') {
                toast.success(t('runningBackup.toast.done'))
                if (job.warning) toast(backupMsg(t, 'job_warning'), { icon: '⚠️', duration: 6000 })
                loadBackups()
                if (job.remote_file) {
                  void loadCloudBackups()
                }
              } else if (job.status === 'cancelled') {
                toast(t('runningBackup.toast.cancelled'), { duration: 6000 })
              } else {
                toast.error(backupMsg(t, resolveApiFeedbackCode(job, 'backup_job')), { duration: 10000 })
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
    if (backupDirMode === 'usb') {
      if (selectedTarget || selectedDevice) {
        loadUsbInfo(selectedTarget, selectedDevice)
        // Setze backupDir basierend auf ausgewähltem USB
        if (selectedTarget) {
          setBackupDir(`${selectedTarget}/pi-installer-backups`)
        }
      }
      // Lade Backups wenn USB-Ziel gesetzt ist
      if (selectedTarget && backupDir.startsWith(selectedTarget)) {
        loadBackups()
      }
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

  const loadBackups = async (dirOverride?: string) => {
    const dir = dirOverride ?? backupDir
    try {
      const response = await fetchApi(`/api/backup/list?backup_dir=${encodeURIComponent(dir)}`)
      const data = await response.json()
      if (data.status === 'success') {
        const newBackups = data.backups || []
        setBackups(newBackups)
        // Entferne Auswahl für Backups, die nicht mehr existieren
        setSelectedBackups((prev) => {
          const backupFiles = new Set(newBackups.map((b: any) => b.file))
          return new Set(Array.from(prev).filter((f) => backupFiles.has(f)))
        })
      } else {
        setBackups([])
        setSelectedBackups(new Set())
        toast.error(backupMsg(t, resolveApiFeedbackCode(data, 'backup_list')), { duration: 8000 })
      }
    } catch (error) {
      console.error('Fehler beim Laden der Backups:', error)
      setBackups([])
      setSelectedBackups(new Set())
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
      { title: t('backup.i18n.settings.save.title'), subtitle: t('backup.i18n.settings.save.subtitle'), confirmText: t('backup.i18n.settings.save.confirm') },
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
            toast.success(t('backup.i18n.settings.saved'))
            setBackupSettings(d.settings)
          } else {
            toast.error(backupMsg(t, resolveApiFeedbackCode(d, 'settings_save')))
          }
        } finally {
          setSettingsLoading(false)
        }
      }
    )
  }

  const runScheduleRuleNow = async (ruleId?: string) => {
    await requireSudo(
      { title: t('backup.i18n.schedule.runNow.title'), subtitle: t('backup.i18n.schedule.runNow.subtitle'), confirmText: t('backup.i18n.schedule.runNow.confirm') },
      async () => {
        const r = await fetchApi('/api/backup/schedule/run-now', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(ruleId ? { rule_id: ruleId } : {}),
        })
        const d = await r.json()
        if (d.status === 'success') {
          toast.success(backupMsg(t, 'schedule_ok'))
          loadBackups()
        } else {
          toast.error(backupMsg(t, resolveApiFeedbackCode(d, 'schedule_run')), { duration: 12000 })
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
        // Speichere base_url für spätere Verwendung
        if (d.base_url) {
          setCloudBaseUrl(d.base_url)
        }
        // Konvertiere Cloud-Backups in das gleiche Format wie lokale Backups
        const formattedBackups = backups.map((b: any) => {
          const sizeBytes = b.size_bytes || 0
          const sizeMB = sizeBytes > 0 ? (sizeBytes / 1024 / 1024).toFixed(2) + ' MB' : t('backup.i18n.unknown')
          const href = b.href || b.name
          // Debug: Zeige die href-Struktur in der Konsole
          if (backups.length > 0 && backups.indexOf(b) === 0) {
            console.log('[Cloud-Backup List] Beispiel href-Struktur:', {
              href: b.href,
              name: b.name,
              base_url: d.base_url,
              full_backup_object: b
            })
          }
          return {
            file: href,
            href: href,  // Stelle sicher, dass href verfügbar ist
            name: b.name,
            size: sizeMB,
            date: b.last_modified || t('backup.i18n.unknown'),
            encrypted: b.encrypted || b.name?.endsWith('.gpg') || b.name?.endsWith('.enc'),
            location: t('backup.i18n.location.cloud'),
          }
        })
        setCloudBackups(formattedBackups)
        // Entferne Auswahl für Cloud-Backups, die nicht mehr existieren
        setSelectedCloudBackups((prev) => {
          const backupKeys = new Set(formattedBackups.map((b: any) => b.href || b.file || b.name))
          return new Set(Array.from(prev).filter((f) => backupKeys.has(f)))
        })
        {
          const cloudListCode = pickStructuredCode(d)
          const sev = String((d as { severity?: unknown }).severity ?? '').toLowerCase()
          if (
            formattedBackups.length === 0 &&
            cloudListCode &&
            !(sev === 'success' && cloudListCode === 'backup.cloud_list_ok')
          ) {
            toast(backupMsg(t, resolveApiFeedbackCode(d, 'cloud_list')), { duration: 4000, icon: 'ℹ️' })
          }
        }
      } else {
        toast.error(backupMsg(t, resolveApiFeedbackCode(d, 'cloud_list')), { duration: 12000 })
        setCloudBackups([])
        setSelectedCloudBackups(new Set())
      }
    } catch (e) {
      toast.error(t('backup.i18n.cloud.loadFailedOffline'))
      setCloudBackups([])
      setSelectedCloudBackups(new Set())
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
        toast.success(t('backup.i18n.cloud.remoteVerified'))
      } else {
        setCloudVerified((m) => ({ ...m, [name]: false }))
        toast.error(backupMsg(t, resolveApiFeedbackCode(d, 'cloud_verify')), { duration: 12000 })
      }
    } catch {
      setCloudVerified((m) => ({ ...m, [name]: false }))
      toast.error(t('backup.i18n.cloud.remoteVerifyOffline'))
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
    } catch {
      setTargetCheck({ status: 'error', message_code: 'server_unreachable' })
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
    } catch {
      setUsbInfo({ status: 'error', message_code: 'usb_info_load_failed' })
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

  const storeSudoPassword = async (sudoPassword: string, skipTest = false) => {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 25000) // 25s Timeout
    try {
      const resp = await fetchApi('/api/users/sudo-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sudo_password: sudoPassword, skip_test: skipTest }),
        signal: controller.signal,
      })
      clearTimeout(timeoutId)
      const data = await resp.json()
      if (data.status !== 'success') {
        throw new BackupI18nError(resolveApiFeedbackCode(data, 'sudo'))
      }
    } catch (e: any) {
      clearTimeout(timeoutId)
      if (e?.name === 'AbortError') {
        throw new BackupI18nError('action_timeout')
      }
      throw e
    }
  }

  const requireSudo = async (opts: { title: string; subtitle?: string; confirmText?: string }, action: (pwd?: string) => Promise<void>) => {
    // wenn Backend schon ein Passwort in der Session hat, direkt ausführen
    if (await hasSavedSudoPassword()) {
      await action()
      return
    }

    setSudoModalTitle(opts.title)
    setSudoModalSubtitle(opts.subtitle || t('backup.i18n.sudoRequiredSubtitle'))
    setSudoModalConfirmText(opts.confirmText || t('backup.i18n.confirm'))
    setPendingAction(() => async (pwd: string, skipTest?: boolean) => {
      await storeSudoPassword(pwd, skipTest ?? false)
      await action(pwd)
    })
    setSudoModalOpen(true)
  }

  const runUsbPrepare = async () => {
    if (!selectedTarget && !selectedDevice) {
      toast.error(t('backup.i18n.usb.selectFirst'))
      return
    }

    if (usbDoFormat) {
      // harte Sicherheitsabfrage
      if (usbConfirm.trim().toUpperCase() !== 'FORMAT') {
        toast.error(t('backup.i18n.usb.confirmFormatRequired'))
        return
      }
    }

    await requireSudo(
      { title: t('backup.i18n.usb.prepare.title'), subtitle: t('backup.i18n.usb.prepare.subtitle'), confirmText: t('backup.i18n.usb.prepare.confirm') },
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
            toast.success(t('backup.i18n.usb.prepared'))
            if (Array.isArray(data.results) && data.results.length > 0) {
              toast.success(backupMsg(t, 'usb_operation_ok', { n: data.results.length }), { duration: 3500 })
            }

            await loadTargets()
            await loadUsbInfo(selectedTarget, selectedDevice)

            if (data.mounted_to) {
              const newDir = `${data.mounted_to}/pi-installer-backups`
              setBackupDirMode('custom')
              setBackupDir(newDir)
              toast.success(t('backup.i18n.targetSet', { dir: newDir }), { duration: 4000 })
            }
            setShowUsbDialog(false)
          } else {
            toast.error(backupMsg(t, resolveApiFeedbackCode(data, 'usb_prepare')))
          }
        } finally {
          setUsbWorking(false)
        }
      }
    )
  }

  const runUsbEject = async () => {
    if (!selectedTarget && !selectedDevice) {
      toast.error(t('backup.i18n.usb.selectFirst'))
      return
    }

    if (!window.confirm(t('backup.i18n.usb.ejectConfirm'))) return

    await requireSudo(
      { title: t('backup.i18n.usb.eject.title'), subtitle: t('backup.i18n.usb.eject.subtitle'), confirmText: t('backup.i18n.usb.eject.confirm') },
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
          toast.success(t('backup.i18n.usb.ejected'))
          if (Array.isArray(data.results) && data.results.length > 0) {
            toast.success(backupMsg(t, 'usb_operation_ok', { n: data.results.length }), { duration: 3000 })
          }
          await loadTargets()
          setSelectedTarget('')
          setSelectedDevice('')
          setUsbInfo(null)
        } else {
          toast.error(backupMsg(t, resolveApiFeedbackCode(data, 'usb_eject')))
          if (Array.isArray(data.still_mounted) && data.still_mounted.length > 0) {
            toast.error(t('backup.i18n.usb.stillMounted', { list: data.still_mounted.join(', ') }), { duration: 8000 })
          }
        }
      }
    )
  }

  const mountSelectedUsb = async (device: string) => {
    if (!device) return
    await requireSudo(
      { title: t('backup.i18n.usb.mount.title'), subtitle: t('backup.i18n.usb.mount.subtitle'), confirmText: t('backup.i18n.usb.mount.confirm') },
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
              toast.success(t('backup.i18n.usb.mountedTo', { path: data.mounted_to }), { duration: 4000 })
            } else {
              toast.success(t('backup.i18n.usb.mounted'), { duration: 4000 })
            }
          } else {
            toast.error(backupMsg(t, resolveApiFeedbackCode(data, 'usb_mount')), { duration: 12000 })
          }
        } catch {
          toast.error(t('backup.i18n.usb.mountFailedOffline'))
        }
      }
    )
  }

  const startClone = async () => {
    if (!cloneTargetDevice) {
      toast.error(t('backup.i18n.clone.selectTargetFirst'))
      return
    }
    if (!window.confirm(
      t('backup.i18n.clone.confirmBody', { target: cloneTargetDevice })
    )) return

    await requireSudo(
      { title: t('backup.i18n.clone.start.title'), subtitle: t('backup.i18n.clone.start.subtitle'), confirmText: t('backup.i18n.clone.start.confirm') },
      async () => {
        try {
          const r = await fetchApi('/api/backup/clone', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_device: cloneTargetDevice }),
          })
          const d = await r.json()
          if (d.status === 'accepted') {
            toast.success(t('backup.i18n.clone.started'))
            setCloneJob({
              job_id: d.job_id,
              status: 'queued',
              message: t('backup.i18n.clone.running'),
              target_device: cloneTargetDevice,
            })
          } else {
            toast.error(backupMsg(t, resolveApiFeedbackCode(d, 'clone_start')))
            setCloneJob(null)
          }
        } catch (e) {
          toast.error(t('backup.i18n.serverUnreachable'))
          setCloneJob(null)
        }
      }
    )
  }

  const onUsbSelectChange = async (v: string) => {
    if (v.startsWith('/dev/')) {
      setSelectedDevice(v)
      setSelectedTarget('')
      // ask before mounting (non-destructive, but needs sudo)
      const ok = window.confirm(t('backup.i18n.usb.notMountedConfirmMount'))
      if (ok) {
        toast(t('backup.i18n.usb.mounting'), { duration: 2500 })
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
        toast.error(t('backup.i18n.cloud.uploadDisabled'))
        return
      }
      // Prüfe Provider-spezifische Settings
      const provider = backupSettings?.cloud?.provider || 'seafile_webdav'
      if (provider.includes('webdav')) {
        if (!backupSettings?.cloud?.webdav_url || !backupSettings?.cloud?.username || !backupSettings?.cloud?.password) {
          toast.error(t('backup.i18n.cloud.settingsMissing'))
          return
        }
      } else if (provider === 's3' || provider === 's3_compatible') {
        if (!backupSettings?.cloud?.bucket || !backupSettings?.cloud?.access_key_id || !backupSettings?.cloud?.secret_access_key) {
          toast.error(t('backup.i18n.cloud.s3SettingsMissing'))
          return
        }
      } else if (provider === 'google_cloud') {
        if (!backupSettings?.cloud?.bucket) {
          toast.error(t('backup.i18n.cloud.gcsSettingsMissing'))
          return
        }
      } else if (provider === 'azure') {
        if (!backupSettings?.cloud?.account_name || !backupSettings?.cloud?.container || !backupSettings?.cloud?.account_key) {
          toast.error(t('backup.i18n.cloud.azureSettingsMissing'))
          return
        }
      }
    }

    const targetText = isCloudTarget ? t('backup.i18n.cloud.targetCloudOnly') : t('backup.i18n.cloud.targetLocalIn', { dir: backupDir })
    if (
      !window.confirm(
        t('backup.i18n.create.confirm', {
          type:
            backupType === 'full'
              ? t('backup.i18n.type.full')
              : backupType === 'incremental'
                ? t('backup.i18n.type.incremental')
                : t('backup.i18n.type.data'),
          target: targetText,
        })
      )
    ) {
      return
    }

    await requireSudo(
      { title: t('backup.i18n.create.title'), subtitle: t('backup.i18n.create.subtitle'), confirmText: t('backup.i18n.create.confirmButton') },
      async () => {
        setLoading(true)
        try {
          // Bestimme target: Wenn USB gewählt ist, immer nur lokal. Cloud nur wenn explizit Cloud-Ziel gewählt.
          let targetValue: string
          if (isCloudTarget) {
            targetValue = 'cloud_only'
          } else if (backupDirMode === 'usb') {
            // USB-Ziel: niemals Cloud-Upload
            targetValue = 'local'
          } else {
            // Lokales Ziel: optional Cloud-Upload wenn aktiviert
            targetValue = backupSettings?.cloud?.enabled ? 'local_and_cloud' : 'local'
          }
          
          const requestBody: any = {
            type: backupType,
            backup_dir: backupDir,
            target: targetValue,
            async: true,
          }
          if (encryptionEnabled && encryptionMethod && encryptionKey) {
            requestBody.encryption_method = encryptionMethod
            requestBody.encryption_key = encryptionKey
          }
          
          const backupTypeText =
            backupType === 'full'
              ? t('backup.i18n.type.full')
              : backupType === 'incremental'
                ? t('backup.i18n.type.incremental')
                : t('backup.i18n.type.data')
          const encryptionText = encryptionEnabled ? t('backup.i18n.create.encryptionPart', { method: encryptionMethod.toUpperCase() }) : ''
          const targetText = isCloudTarget ? t('backup.i18n.location.cloud') : t('backup.i18n.create.targetLocal', { dir: backupDir })
          
          toast(
            t('backup.i18n.create.inProgressToast', { type: backupTypeText, encryptionPart: encryptionText, target: targetText }),
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
            toast.success(t('backup.i18n.create.started'))
            // Setze Backup-Job sofort, damit die Anzeige startet
            const jobData = {
              job_id: data.job_id || String(Date.now()),
              status: 'queued',
              backup_file: data.backup_file || '',
              message: t('backup.i18n.create.running'),
            }
            console.log('Setting backupJob:', jobData) // Debug
            setBackupJob(jobData)
            // Speichere sofort in localStorage für globale Komponente
            try {
              localStorage.setItem(BACKUP_JOB_STORAGE_KEY, JSON.stringify(jobData))
            } catch {
              // ignore
            }
            // Benachrichtige das globale Modal über einen Event
            window.dispatchEvent(new CustomEvent('backup-job-started', { detail: jobData }))
            // Starte sofort Polling
            setTimeout(() => {
              const pollJob = async () => {
                try {
                  const r = await fetchApi(`/api/backup/jobs/${encodeURIComponent(data.job_id)}`)
                  const d = await r.json()
                  if (d.status === 'success' && d.job) {
                    console.log('Polling backupJob update:', d.job) // Debug
                    setBackupJob(d.job)
                    // Aktualisiere localStorage
                    try {
                      const isRunning = d.job.status === 'queued' || d.job.status === 'running' || d.job.status === 'cancel_requested' || !d.job.status
                      if (isRunning) {
                        localStorage.setItem(BACKUP_JOB_STORAGE_KEY, JSON.stringify(d.job))
                      } else {
                        setTimeout(() => {
                          localStorage.removeItem(BACKUP_JOB_STORAGE_KEY)
                        }, 5000)
                      }
                    } catch {
                      // ignore
                    }
                    if (d.job.status === 'success' || d.job.status === 'error' || d.job.status === 'cancelled') {
                      // Zeige Ergebnis an
                      if (d.job.status === 'success') {
                        toast.success(t('backup.i18n.create.success'))
                        if (d.job.warning) {
                          toast(backupMsg(t, 'job_warning'), { icon: '⚠️', duration: 8000 })
                        }
                        // Prüfe ob Cloud-Upload erfolgreich war
                        const hasUpload = d.job.results?.some((r: string) => r.includes('uploaded:'))
                        if (isCloudTarget && hasUpload) {
                          toast.success(t('backup.i18n.cloud.uploadSuccess'), { duration: 6000 })
                          loadCloudBackups() // Lade Cloud-Backups neu
                        } else if (isCloudTarget && !hasUpload) {
                          const uploadFailed = d.job.results?.some((r: string) => r.includes('upload failed'))
                          if (uploadFailed) {
                            toast.error(t('backup.i18n.cloud.uploadFailed'), { duration: 8000 })
                          }
                        }
                        loadBackups() // Lade lokale Backups neu
                      } else if (d.job.status === 'error') {
                        toast.error(backupMsg(t, resolveApiFeedbackCode(d.job, 'backup_job')), { duration: 10000 })
                        if (d.job.warning) {
                          toast.error(backupMsg(t, 'job_warning'), { duration: 10000 })
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
            toast.success(t('backup.i18n.create.created'))
            loadBackups()
          } else {
            const code = resolveApiFeedbackCode(data, 'backup_create')
            if (code === 'backup.sudo_required') setSawSudoRequiredForBackupRun(true)
            toast.error(backupMsg(t, code))
            if (Array.isArray(data.results) && data.results.length > 0) {
              toast.error(backupMsg(t, 'create_extra_results', { n: data.results.length }), { duration: 5000 })
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
    if (!window.confirm(t('runningBackup.confirmCancel'))) return
    try {
      const r = await fetchApi(`/api/backup/jobs/${encodeURIComponent(backupJob.job_id)}/cancel`, { method: 'POST' })
      const d = await r.json()
      if (d.status === 'success') {
        toast.success(t('runningBackup.toast.cancelRequested'))
        setBackupJob((j: any) => (j ? { ...j, status: 'cancel_requested' } : j))
      } else {
        toast.error(backupMsg(t, resolveApiFeedbackCode(d, 'job_cancel')))
      }
    } catch {
      toast.error(t('backup.i18n.cancelFailedOffline'))
    }
  }

  const restoreBackup = async (backupFile: string) => {
    if (
      !window.confirm(
        t('backup.restore.preview.confirm', {
          file: backupFile.split('/').pop() || backupFile,
        }),
      )
    ) {
      return
    }

    await requireSudo(
      {
        title: t('backup.restore.preview.sudoTitle'),
        subtitle: t('backup.restore.preview.sudoSubtitle'),
        confirmText: t('backup.restore.preview.sudoConfirm'),
      },
      async (sudoPassword?: string) => {
        setLoading(true)
        try {
          const response = await fetchApi('/api/backup/restore', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              backup_file: backupFile,
              mode: 'preview',
              sudo_password: sudoPassword,
            }),
          })
          const data = await response.json()

          if (data.status === 'success') {
            setRestorePreviewResult({
              backupFile,
              previewDir: String(data.preview_dir || ''),
              analysis: data.analysis || {},
              totalEntries: typeof data.total_entries === 'number' ? data.total_entries : 0,
            })
            toast.success(t('backup.restore.preview.toastSuccess'))
          } else {
            setRestorePreviewResult(null)
            toast.error(backupMsg(t, resolveApiFeedbackCode(data, 'restore_preview')))
          }
        } finally {
          setLoading(false)
        }
      },
    )
  }

  const applyVerifyFailureDiagnosis = React.useCallback(async (failureCode: string, extra: Record<string, unknown> = {}) => {
    const code = String(failureCode || '').trim()
    if (!code) {
      setVerifyDiagnosis(null)
      return
    }
    const rec = await postDiagnosisInterpret({
      area: 'backup_restore',
      event_type: 'verify_failed',
      message: `code:${code}`.slice(0, 2000),
      extra,
    })
    setVerifyDiagnosis(rec)
  }, [])

  useEffect(() => {
    if (!verifyDiagnosis) {
      setStructuredDiagnostics(null)
      return
    }
    let cancelled = false
    const run = async () => {
      const result = await postDiagnosticsAnalyze({
        question: `Verify/Restore Diagnose: ${verifyDiagnosis.diagnosis_id}`,
        context: { mode: 'backup_verify', user_level: diagnosticsLevel },
        signals: {
          verify_status: 'failed',
          manifest_present: true,
          archive_corrupted: verifyDiagnosis.diagnosis_id.includes('archive'),
          storage_full: verifyDiagnosis.technical_summary.toLowerCase().includes('no space'),
          filesystem_readonly: verifyDiagnosis.technical_summary.toLowerCase().includes('read-only'),
          setuphelfer_group_present: !verifyDiagnosis.technical_summary.toLowerCase().includes('setuphelfer group'),
        },
      })
      if (!cancelled) setStructuredDiagnostics(result)
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [verifyDiagnosis, diagnosticsLevel])

  const verifyBackup = async (backupFile: string, mode: 'basic' | 'deep' = 'basic') => {
    if (mode === 'deep') {
      setDeepVerifyFile(backupFile)
      setDeepVerifyKey('')
      setDeepVerifyOpen(true)
      return
    }
    setVerifyDiagnosis(null)
    setVerifying((m) => ({ ...m, [backupFile]: true }))
    try {
      const body: any = { backup_file: backupFile, mode }
      const res = await fetchApi('/api/backup/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if ((data.status === 'success' || data.status === 'warning') && data.results) {
        const results = data.results
        const verificationMode = results.verification_mode || mode
        if (results.encrypted && verificationMode === 'basic') {
          if (results.size_bytes > 0) {
            setVerifyDiagnosis(null)
            toast.success(
              t('backup.verify.basic.encryptedFound', {
                size: results.size_human,
              }),
              { duration: 8000 },
            )
            toast(t('backup.verify.basic.encryptedInfo'), { duration: 10000, icon: '🔒' })
          } else {
            toast.error(t('backup.verify.basic.encryptedEmpty'), { duration: 9000 })
            void applyVerifyFailureDiagnosis('encrypted_empty', {
              kind: 'encrypted_empty',
              verify_mode: mode,
              backup_file: backupFile,
            })
          }
        } else if (results.valid) {
          setVerifyDiagnosis(null)
          toast.success(
            t('backup.verify.valid', {
              size: results.size_human,
              count: results.file_count,
            }),
            { duration: 8000 },
          )
          if (results.sample_files && results.sample_files.length > 0) {
            toast(backupMsg(t, 'verify_samples_hidden', { count: results.sample_files.length }), { duration: 10000, icon: '📋' })
          }
        } else {
          toast.error(backupMsg(t, 'verify_archive_invalid'), { duration: 12000 })
          void applyVerifyFailureDiagnosis('verify_archive_invalid', {
            verify_mode: mode,
            backup_file: backupFile,
            result_invalid: true,
          })
        }
      } else {
        toast.error(backupMsg(t, resolveApiFeedbackCode(data, 'verify')), { duration: 9000 })
        void applyVerifyFailureDiagnosis('verify_request_failed', {
          verify_mode: mode,
          backup_file: backupFile,
          request_failed: true,
        })
      }
    } catch (error) {
      toast.error(backupMsg(t, 'verify_client_error'), { duration: 9000 })
      void applyVerifyFailureDiagnosis('verify_exception', {
        verify_mode: mode,
        backup_file: backupFile,
        exception: true,
      })
    } finally {
      setVerifying((m) => ({ ...m, [backupFile]: false }))
    }
  }

  const runDeepVerify = async () => {
    if (!deepVerifyFile || !deepVerifyKey) return
    const backupFile = deepVerifyFile
    setVerifyDiagnosis(null)
    setVerifying((m) => ({ ...m, [backupFile]: true }))
    try {
      const body: any = { backup_file: backupFile, mode: 'deep' as const, encryption_key: deepVerifyKey }
      const res = await fetchApi('/api/backup/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
      const data = await res.json()
      if ((data.status === 'success' || data.status === 'warning') && data.results) {
        const results = data.results
        const verificationMode = results.verification_mode || 'deep'
        if (results.encrypted && verificationMode === 'basic') {
          if (results.size_bytes > 0) {
            setVerifyDiagnosis(null)
            toast.success(
              t('backup.verify.basic.encryptedFound', {
                size: results.size_human,
              }),
              { duration: 8000 },
            )
            toast(t('backup.verify.basic.encryptedInfo'), { duration: 10000, icon: '🔒' })
          } else {
            toast.error(t('backup.verify.basic.encryptedEmpty'), { duration: 9000 })
            void applyVerifyFailureDiagnosis('encrypted_empty', {
              kind: 'encrypted_empty',
              verify_mode: 'deep',
              backup_file: backupFile,
            })
          }
        } else if (results.valid) {
          setVerifyDiagnosis(null)
          toast.success(
            t('backup.verify.valid', {
              size: results.size_human,
              count: results.file_count,
            }),
            { duration: 8000 },
          )
          if (results.sample_files && results.sample_files.length > 0) {
            toast(backupMsg(t, 'verify_samples_hidden', { count: results.sample_files.length }), { duration: 10000, icon: '📋' })
          }
        } else {
          toast.error(backupMsg(t, 'verify_archive_invalid'), { duration: 12000 })
          void applyVerifyFailureDiagnosis('verify_archive_invalid', {
            verify_mode: 'deep',
            backup_file: backupFile,
            result_invalid: true,
          })
        }
      } else {
        toast.error(backupMsg(t, resolveApiFeedbackCode(data, 'verify')), { duration: 9000 })
        void applyVerifyFailureDiagnosis('verify_request_failed', {
          verify_mode: 'deep',
          backup_file: backupFile,
          request_failed: true,
        })
      }
    } catch (error) {
      toast.error(backupMsg(t, 'verify_client_error'), { duration: 9000 })
      void applyVerifyFailureDiagnosis('verify_exception', {
        verify_mode: 'deep',
        backup_file: backupFile,
        exception: true,
      })
    } finally {
      setVerifying((m) => ({ ...m, [backupFile]: false }))
      setDeepVerifyOpen(false)
      setDeepVerifyFile(null)
      setDeepVerifyKey('')
    }
  }

  const toggleBackupSelection = (backupFile: string) => {
    setSelectedBackups((prev) => {
      const next = new Set(prev)
      if (next.has(backupFile)) {
        next.delete(backupFile)
      } else {
        next.add(backupFile)
      }
      return next
    })
  }

  const toggleCloudBackupSelection = (backupFile: string) => {
    setSelectedCloudBackups((prev) => {
      const next = new Set(prev)
      if (next.has(backupFile)) {
        next.delete(backupFile)
      } else {
        next.add(backupFile)
      }
      return next
    })
  }

  const selectAllBackups = () => {
    if (selectedBackups.size === backups.length) {
      setSelectedBackups(new Set())
    } else {
      setSelectedBackups(new Set(backups.map((b) => b.file)))
    }
  }

  const selectAllCloudBackups = () => {
    if (selectedCloudBackups.size === cloudBackups.length) {
      setSelectedCloudBackups(new Set())
    } else {
      setSelectedCloudBackups(new Set(cloudBackups.map((b: any) => b.href || b.file || b.name || `cloud-${cloudBackups.indexOf(b)}`)))
    }
  }

  const deleteBackup = async (backupFile: string) => {
    if (!window.confirm(t('backup.i18n.delete.confirmSingle', { file: backupFile }))) return
    await requireSudo(
      { title: t('backup.i18n.delete.single.title'), subtitle: t('backup.i18n.delete.single.subtitle'), confirmText: t('backup.i18n.delete.single.confirm') },
      async () => {
        const res = await fetchApi('/api/backup/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ backup_file: backupFile }),
        })
        const data = await res.json()
        if (data.status === 'success') {
          toast.success(t('backup.i18n.delete.single.success'))
          loadBackups()
          setSelectedBackups((prev) => {
            const next = new Set(prev)
            next.delete(backupFile)
            return next
          })
        } else {
          toast.error(backupMsg(t, resolveApiFeedbackCode(data, 'backup_delete')), { duration: 10000 })
        }
      }
    )
  }

  const deleteSelectedBackups = async () => {
    if (selectedBackups.size === 0) {
      toast.error(t('backup.selection.none'))
      return
    }
    const count = selectedBackups.size
    if (!window.confirm(t('backup.i18n.delete.confirmMultiple', { count }))) return
    await requireSudo(
      { title: t('backup.i18n.delete.multiple.title'), subtitle: t('backup.i18n.delete.multiple.subtitle', { count }), confirmText: t('backup.i18n.delete.multiple.confirm') },
      async (sudoPassword: string) => {
        let successCount = 0
        let failCount = 0
        const errors: string[] = []
        for (const backupFile of selectedBackups) {
          try {
            const res = await fetchApi('/api/backup/delete', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ 
                backup_file: backupFile,
                sudo_password: sudoPassword 
              }),
            })
            const data = await res.json()
            if (data.status === 'success') {
              successCount++
            } else {
              failCount++
              errors.push(String(backupFile.split('/').pop() || backupFile))
            }
          } catch {
            failCount++
            errors.push(String(backupFile.split('/').pop() || backupFile))
          }
        }
        if (successCount > 0) {
          toast.success(t('backup.i18n.delete.multiple.success', { count: successCount }))
          loadBackups()
          setSelectedBackups(new Set())
        }
        if (failCount > 0) {
          const filesHint = errors.slice(0, 3).join(', ')
          toast.error(backupMsg(t, 'delete_batch_partial', { failed: failCount, files: filesHint }), { duration: 15000 })
        }
      }
    )
  }

  const verifySelectedBackups = async () => {
    if (selectedBackups.size === 0) {
      toast.error(t('backup.selection.none'))
      return
    }
    const files = Array.from(selectedBackups)
    for (const backupFile of files) {
      await verifyBackup(backupFile, 'basic')
    }
  }

  const restoreSelectedBackup = async () => {
    if (selectedBackups.size === 0) {
      toast.error(t('backup.selection.none'))
      return
    }
    if (selectedBackups.size > 1) {
      toast.error(t('backup.restore.onlyOne'))
      return
    }
    const backupFile = Array.from(selectedBackups)[0]
    if (String(backupFile).includes('pi-backup-inc-')) {
      toast.error(t('backup.restore.incrementalNotSupported'))
      return
    }
    await restoreBackup(backupFile)
  }

  const backupCompanionStatus = useMemo((): PandaStatus => {
    const st = backupJob?.status
    if (st === 'failed' || st === 'error') return 'danger'
    if (backupJob?.warning) return 'warning'
    if (st && ['queued', 'running', 'cancel_requested'].includes(String(st))) return 'info'
    return 'success'
  }, [backupJob])

  const backupJobUiPhase = useMemo(
    () => inferBackupJobUiPhase(backupJob ?? null),
    [backupJob?.code, backupJob?.message, backupJob?.results],
  )

  const backupSafetyTraffic = useMemo(() => {
    const anyVerifying =
      Object.values(verifying).some(Boolean) || Object.values(cloudVerifying).some(Boolean)
    // Phase 4: Bis ein belastbarer Nachweis "Backup-Lauf erfolgreich + Verify auf diesem Backup"
    // aus persistierten Fakten vorliegt, ist gruene Freigabe nicht erlaubt.
    const hasRealBackupVerification = false
    return deriveBackupSafetyTrafficLight({
      verifyDiagnosis,
      anyVerifying,
      hasRestorePreview: !!restorePreviewResult,
      hasRealBackupVerification,
      sawSudoRequired: sawSudoRequiredForBackupRun,
    })
  }, [verifyDiagnosis, verifying, cloudVerifying, restorePreviewResult, sawSudoRequiredForBackupRun])

  const cloudCompanionStatus = useMemo((): PandaStatus => {
    if (cloudBackupsLoading) return 'info'
    if (showCloudBackups && cloudBackups.length > 0) return 'success'
    if (showCloudBackups && !cloudBackupsLoading) return 'warning'
    if (backupDirMode === 'cloud' && !backupSettings?.cloud?.enabled) return 'warning'
    if (backupSettings?.cloud?.enabled) return 'info'
    return 'info'
  }, [
    cloudBackupsLoading,
    showCloudBackups,
    cloudBackups.length,
    backupDirMode,
    backupSettings?.cloud?.enabled,
  ])

  const cloudCompanionSection = (
    <div className="space-y-2 my-3">
      <PandaHelperStrip experienceLevel={experienceLevel} variant="backup">
        {t('backup.ui.cloudCompanion.helperPartBefore')}
        <span className="text-slate-900 font-medium dark:text-slate-200">{t('backup.ui.cloudCompanion.settingsLink')}</span>
        {t('backup.ui.cloudCompanion.helperPartAfter')}
      </PandaHelperStrip>
      <PandaRail>
        <PandaCompanion
          type="cloud"
          size="sm"
          surface="dark"
          frame={false}
          showTrafficLight
          trafficLightPosition="bottom-right"
          status={cloudCompanionStatus}
          title={t('backup.ui.cloudCompanion.title')}
          subtitle={t('backup.ui.cloudCompanion.subtitle')}
        />
      </PandaRail>
    </div>
  )

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
        onConfirm={async (pwd, skipTest) => {
          try {
            if (!pendingAction) return
            await pendingAction(pwd, skipTest)
            toast.success(t('backup.i18n.sudoSavedSession'))
            setSudoModalOpen(false)
            setPendingAction(null)
          } catch (e: unknown) {
            const code = e instanceof BackupI18nError ? e.code : 'unknown'
            toast.error(backupMsg(t, code === 'unknown' ? 'sudo_invalid_generic' : code))
          }
        }}
      />
      {/* Deep-Verify Dialog */}
      {deepVerifyOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/60">
          <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl max-w-sm w-full p-4 space-y-3">
            <h3 className="text-sm font-semibold text-white">
              {t('backup.verify.deep.title')}
            </h3>
            <p className="text-xs text-slate-300">
              {t('backup.verify.deep.body')}
            </p>
            <div className="space-y-1">
              <label className="text-xs text-slate-200" htmlFor="deep-verify-key">
                {t('backup.verify.deep.label')}
              </label>
              <input
                id="deep-verify-key"
                type="password"
                className="w-full px-2 py-1 rounded bg-slate-950 border border-slate-700 text-xs text-slate-100"
                value={deepVerifyKey}
                onChange={(e) => setDeepVerifyKey(e.target.value)}
                placeholder={t('backup.verify.deep.placeholder')}
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                className="px-3 py-1 text-xs rounded bg-slate-800 text-slate-100 hover:bg-slate-700"
                onClick={() => {
                  setDeepVerifyOpen(false)
                  setDeepVerifyFile(null)
                  setDeepVerifyKey('')
                }}
              >
                {t('backup.verify.deep.cancel')}
              </button>
              <button
                type="button"
                className="px-3 py-1 text-xs rounded bg-sky-600 text-white hover:bg-sky-500 disabled:opacity-50"
                disabled={!deepVerifyKey}
                onClick={() => void runDeepVerify()}
              >
                {t('backup.verify.deep.confirm')}
              </button>
            </div>
          </div>
        </div>
      )}

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
                  <h2 className="text-2xl font-bold text-white">{t('backup.ui.usbDialog.title')}</h2>
                  <p className="text-sm text-slate-400">{t('backup.ui.usbDialog.subtitle')}</p>
                </div>
                <button
                  className="px-3 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg"
                  onClick={() => !usbWorking && setShowUsbDialog(false)}
                >
                  {t('backup.ui.common.close')}
                </button>
              </div>

              <div className="p-4 bg-yellow-900/20 border border-yellow-700/40 rounded-lg text-yellow-100 text-sm mb-4">
                <div className="font-semibold mb-1">{t('backup.ui.usbDialog.warningTitle')}</div>
                <div>
                  {t('backup.ui.usbDialog.warningBody')} {t('backup.ui.usbDialog.warningExtra')}
                </div>
              </div>

              <div className="space-y-4">
                <div className="p-3 bg-slate-900/40 border border-slate-700 rounded-lg text-sm text-slate-200">
                  <div className="font-semibold text-white mb-1">{t('backup.ui.usbDialog.selected')}</div>
                  <div className="text-xs text-slate-300 whitespace-pre-line">
                    {t('backup.ui.usbDialog.selectedDetail', {
                      mount: selectedTarget || t('backup.ui.targetStatus.emDash'),
                      disk: String(usbInfo?.disk ?? t('backup.ui.targetStatus.emDash')),
                      part: String(usbInfo?.partition ?? t('backup.ui.targetStatus.emDash')),
                      fs: String(usbInfo?.fstype ?? t('backup.ui.targetStatus.emDash')),
                      label: String(usbInfo?.label ?? t('backup.ui.targetStatus.emDash')),
                      size: String(usbInfo?.size ?? t('backup.ui.targetStatus.emDash')),
                    })}
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
                    <div className="font-semibold text-white">{t('backup.ui.usbDialog.formatToggle')}</div>
                    <div className="text-xs text-slate-400">{t('backup.ui.usbDialog.formatHint')}</div>
                  </div>
                </label>

                <div>
                  <label className="block text-sm font-semibold text-white mb-2">{t('backup.ui.usbDialog.labelField')}</label>
                  <input
                    value={usbLabel}
                    onChange={(e) => setUsbLabel(e.target.value)}
                    placeholder={t('backup.ui.usbDialog.defaultLabel')}
                    className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-sky-600"
                  />
                  <div className="mt-1 text-xs text-slate-400">{t('backup.ui.usbDialog.labelHelp')}</div>
                </div>

                {usbDoFormat && (
                  <div>
                    <label className="block text-sm font-semibold text-white mb-2">{t('backup.ui.usbDialog.confirmLabel')}</label>
                    <input
                      value={usbConfirm}
                      onChange={(e) => setUsbConfirm(e.target.value)}
                      placeholder={t('backup.ui.usbDialog.formatPlaceholder')}
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
                  {t('backup.ui.common.cancel')}
                </button>
                <button
                  className="flex-1 px-4 py-3 bg-red-600 hover:bg-red-500 text-white rounded-lg disabled:opacity-50"
                  disabled={usbWorking || (usbDoFormat && usbConfirm.trim().toUpperCase() !== t('backup.ui.usbDialog.formatPlaceholder'))}
                  onClick={runUsbPrepare}
                >
                  {usbWorking ? t('backup.i18n.pleaseWait') : usbDoFormat ? t('backup.i18n.usb.formatAndRename') : t('backup.i18n.usb.renameOrMount')}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      <PageHeader
        visualStyle="hero-card"
        tone="backup"
        title={t('backup.ui.pageHeader.title')}
        subtitle={t('backup.ui.pageHeader.subtitle', { system: pageSubtitleLabel })}
      />

      <div className="flex flex-wrap items-center gap-2">
        <TrafficLightBadge
          state={backupSafetyTraffic.lamp}
          label={t(`backup.ui.traffic.${backupSafetyTraffic.copyKey}.label`)}
          detail={t(`backup.ui.traffic.${backupSafetyTraffic.copyKey}.detail`)}
        />
      </div>
      <div className="text-xs text-slate-300">
        {backupSafetyTraffic.lamp === 'red'
          ? t('backup.ui.trafficReason.red')
          : t('backup.ui.trafficReason.yellow')}
      </div>

      {isBeginnerBackupUx && (
        <div className="rounded-xl border border-sky-500/35 bg-slate-900/50 p-4 sm:p-5 space-y-2">
          <p className="text-sm font-semibold text-slate-100">{t('backup.ui.beginner.introTitle')}</p>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">{t('backup.ui.beginner.introBody')}</p>
          <p className="text-xs text-amber-200/90 border border-amber-500/25 rounded-lg px-2 py-1.5 bg-amber-950/20">
            {t('backup.ui.beginner.warningRestore')}
          </p>
        </div>
      )}

      <PandaHelperStrip experienceLevel={experienceLevel} variant="backup">
        {t('backup.ui.panda.helper')}
      </PandaHelperStrip>

      <PandaRail>
        <PandaCompanion
          type="backup"
          size="lg"
          surface="dark"
          frame={false}
          showTrafficLight
          trafficLightPosition="bottom-right"
          status={backupCompanionStatus}
          title={t('backup.ui.panda.title')}
          subtitle={t('backup.ui.panda.subtitle')}
        />
      </PandaRail>

      {/* Hauptwahl Einsteiger: drei klare Einstiege */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className={`grid gap-3 ${isBeginnerBackupUx ? 'md:grid-cols-3' : 'md:grid-cols-2'}`}
      >
        <button
          type="button"
          onClick={() => setActiveTab('backup')}
          className="card flex items-start gap-3 hover:border-sky-500/60 hover:bg-sky-900/10 transition-colors text-left"
        >
          <div className="mt-1 hidden md:block shrink-0">
            <Download className="text-emerald-400" />
          </div>
          <div className="text-left min-w-0">
            <p className="text-sm font-semibold text-slate-100">{t('backup.ui.card.createTitle')}</p>
            <p className="text-xs text-slate-400 mt-1">{t('backup.ui.card.createDesc')}</p>
          </div>
        </button>
        {isBeginnerBackupUx && (
          <button
            type="button"
            onClick={() => setActiveTab('restore')}
            className="card flex items-start gap-3 hover:border-amber-500/40 hover:bg-amber-950/15 transition-colors text-left border-amber-500/20"
          >
            <div className="mt-1 hidden md:block shrink-0">
              <ClipboardCheck className="text-amber-300" />
            </div>
            <div className="text-left min-w-0">
              <div className="flex flex-wrap items-center gap-1.5">
                <p className="text-sm font-semibold text-slate-100">{t('backup.ui.card.verifyTitle')}</p>
                <BeginnerGuidanceMarker kind="advanced" compact />
              </div>
              <p className="text-xs text-slate-400 mt-1">{t('backup.ui.card.verifyDesc')}</p>
            </div>
          </button>
        )}
        <button
          type="button"
          onClick={() => setActiveTab('restore')}
          className="card flex items-start gap-3 hover:border-sky-500/60 hover:bg-sky-900/10 transition-colors text-left"
        >
          <div className="mt-1 hidden md:block shrink-0">
            <Upload className="text-sky-400" />
          </div>
          <div className="text-left min-w-0">
            <p className="text-sm font-semibold text-slate-100">{t('backup.ui.card.restoreTitle')}</p>
            <p className="text-xs text-slate-400 mt-1">{t('backup.ui.card.restoreDesc')}</p>
          </div>
        </button>
      </motion.div>

      {/* Tabs */}
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="card">
        {isBeginnerBackupUx ? (
          <div className="border-b border-slate-700 mb-6 space-y-3">
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => setActiveTab('backup')}
                className={`px-4 py-2 font-medium transition-all relative flex items-center gap-2 ${
                  activeTab === 'backup' ? 'text-sky-400' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Download size={18} className="hidden md:block shrink-0" aria-hidden />
                {t('backup.ui.tab.create')}
                {activeTab === 'backup' && (
                  <motion.div
                    layoutId="activeTabBeginner"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400"
                    initial={false}
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}
              </button>
              <button
                type="button"
                onClick={() => setActiveTab('restore')}
                className={`px-4 py-2 font-medium transition-all relative flex items-center gap-2 ${
                  activeTab === 'restore' ? 'text-sky-400' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <HardDrive size={18} className="hidden md:block shrink-0" aria-hidden />
                {t('backup.ui.tab.restoreVerify')}
                {activeTab === 'restore' && (
                  <motion.div
                    layoutId="activeTabBeginner"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400"
                    initial={false}
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                  />
                )}
              </button>
            </div>
            <details className="group rounded-lg border border-slate-500/70 bg-slate-900/55">
              <summary className="cursor-pointer list-none px-3 py-2 text-xs font-medium text-slate-100 hover:text-white hover:bg-slate-800/55 flex items-center justify-between rounded-lg [&::-webkit-details-marker]:hidden focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-500">
                <span className="flex items-center gap-2">
                  {t('backup.ui.tab.more')}
                  <BeginnerGuidanceMarker kind="advanced" compact />
                </span>
                <span className="text-slate-300 shrink-0 group-open:rotate-180 transition-transform" aria-hidden>
                  ▼
                </span>
              </summary>
              <div className="flex flex-wrap gap-2 px-3 pb-3 pt-0 border-t border-slate-600/80">
                <button
                  type="button"
                  onClick={() => setActiveTab('settings')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 ${
                    activeTab === 'settings' ? 'bg-sky-600 text-white' : 'bg-slate-700/80 text-slate-200 hover:bg-slate-600'
                  }`}
                >
                  <Settings size={16} aria-hidden />
                  {t('backup.ui.tab.settings')}
                </button>
                <button
                  type="button"
                  onClick={() => setActiveTab('clone')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-2 ${
                    activeTab === 'clone' ? 'bg-sky-600 text-white' : 'bg-slate-700/80 text-slate-200 hover:bg-slate-600'
                  }`}
                >
                  <Copy size={16} aria-hidden />
                  {t('backup.ui.clone.introTitle')}
                </button>
              </div>
            </details>
          </div>
        ) : (
          <div className="flex gap-2 border-b border-slate-700 mb-6 flex-wrap">
            <button
              onClick={() => setActiveTab('backup')}
              className={`px-4 py-2 font-medium transition-all relative flex items-center gap-2 ${
                activeTab === 'backup' ? 'text-sky-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Download size={18} className="hidden md:block shrink-0" aria-hidden />
              {t('backup.ui.tab.create')}
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
                activeTab === 'settings' ? 'text-sky-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Settings size={18} className="hidden md:block shrink-0" aria-hidden />
              {t('backup.ui.tab.settings')}
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
                activeTab === 'restore' ? 'text-sky-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <HardDrive size={18} className="hidden md:block shrink-0" aria-hidden />
              {t('backup.ui.tab.existingBackups')}
              {activeTab === 'restore' && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400"
                  initial={false}
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              )}
            </button>
            <button
              onClick={() => setActiveTab('clone')}
              className={`px-4 py-2 font-medium transition-all relative flex items-center gap-2 ${
                activeTab === 'clone' ? 'text-sky-400' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Copy size={18} className="hidden md:block shrink-0" aria-hidden />
              {t('backup.ui.clone.introTitle')}
              {activeTab === 'clone' && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-sky-400"
                  initial={false}
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              )}
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
      {activeTab === 'backup' && (
      <div className="space-y-6">
        <p className="text-slate-400 text-sm">{t('backup.ui.backupTab.flow')}</p>
        {/* Ein-Klick-Backup Hero (Milestone 3 – Transformationsplan) */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-sky-600/40 bg-sky-900/20 dark:bg-sky-900/20 p-6"
        >
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 mb-2 flex items-center gap-2">
            <Database className="text-sky-500 hidden md:block shrink-0" aria-hidden />
            {t('backup.ui.hero.oneClickTitle')}
          </h2>
          <p className="text-slate-600 dark:text-slate-400 text-sm mb-4">{t('backup.ui.hero.oneClickBody')}</p>
          <p className="text-xs text-slate-500 dark:text-slate-500 mb-0">{t('backup.ui.hero.oneClickNote')}</p>
        </motion.div>

      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Backup erstellen */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card"
          >
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <Download className="text-green-500 hidden md:block shrink-0" aria-hidden />
              {t('backup.ui.page.createHeading')}
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
                          {backupJob.status === 'cancel_requested'
                            ? t('runningBackup.title.cancelPending')
                            : backupJobUiPhase === 'check_cloud'
                              ? t('runningBackup.title.checkCloud')
                              : backupJobUiPhase === 'upload'
                                ? t('runningBackup.title.uploading')
                                : t('runningBackup.title.running')}
                        </div>
                      </div>
                      <div className="text-xs text-sky-100/80 mt-1">
                        {backupJob.backup_file ? t('backup.i18n.job.fileLabel', { file: String(backupJob.backup_file).split('/').pop() }) : backupJob.job_id ? t('backup.i18n.job.idLabel', { id: backupJob.job_id }) : ''}
                      </div>
                      <div className="text-xs text-sky-100/80 mt-1">
                        {t('runningBackup.label.status')}{' '}
                        <span className="font-semibold">{backupJob.status || t('backup.ui.status.queued')}</span>
                        {typeof backupJob.bytes_current === 'number' ? t('backup.i18n.job.sizeMb', { mb: (backupJob.bytes_current / 1024 / 1024).toFixed(1) }) : ''}
                      </div>
                      {backupJobUiPhase === 'encrypt' && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: [0.5, 1, 0.5] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                          className="mt-2 p-2 bg-purple-800/30 rounded border border-purple-600/40"
                        >
                          <div className="flex items-center gap-2 text-sm">
                            <Lock className="animate-pulse" size={16} />
                            <span>{t('runningBackup.encryptionRunning')}</span>
                          </div>
                        </motion.div>
                      )}
                      {(backupJobUiPhase === 'upload' || backupJobUiPhase === 'check_cloud' || typeof backupJob.upload_progress_pct === 'number') &&
                        !backupJob.remote_file && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: [0.5, 1, 0.5] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                          className="mt-2 p-2 bg-sky-800/30 rounded border border-sky-600/40"
                        >
                          <div className="flex items-center gap-2 text-sm">
                            <Cloud className="animate-pulse" size={16} />
                            <span>
                              {backupJobUiPhase === 'check_cloud' ? t('runningBackup.checkCloudHint') : t('runningBackup.uploadRunning')}
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
                            <span>
                              {t('runningBackup.uploadOk', {
                                file: String(backupJob.remote_file).split('/').pop() || t('backup.i18n.unknown'),
                              })}
                            </span>
                          </div>
                        </motion.div>
                      )}
                      {backupJob.warning && (
                        <motion.div
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          className="mt-2 p-2 bg-yellow-900/30 rounded border border-yellow-600/40"
                        >
                          <div className="text-sm text-yellow-300">⚠ {backupMsg(t, 'job_warning')}</div>
                        </motion.div>
                      )}
                      {Array.isArray(backupJob.results) && backupJob.results.length > 0 && (
                        <div className="mt-2 text-xs text-sky-100/80">
                          {backupMsg(t, 'job_log_lines', { n: backupJob.results.length })}
                        </div>
                      )}
                    </div>
                    {(backupJob.status === 'queued' || backupJob.status === 'running') && (
                      <button
                        onClick={cancelBackupJob}
                        className="px-3 py-2 bg-red-600/25 hover:bg-red-600/35 border border-red-500/40 text-red-100 rounded-lg text-sm"
                      >
                        {t('runningBackup.cancel')}
                      </button>
                    )}
                  </div>
                </motion.div>
              )}
              {/* Schritt 1: Ziel wählen */}
              <div>
                <h3 className="text-sm font-semibold text-sky-300 mb-1">{t('backup.ui.step1.title')}</h3>
                <label className="block text-white font-semibold mb-2">{t('backup.ui.step1.targetLabel')}</label>
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
                    <div className="font-bold text-white mb-1 flex items-center gap-2">
                      <AppIcon name="nvme" category="devices" size={24} className="hidden md:inline-block shrink-0 opacity-95" alt="" />
                      {t('backup.ui.target.standard')}
                    </div>
                    <div className="text-xs text-slate-400">{t('backup.ui.target.standardPath')}</div>
                  </button>

                  <button
                    onClick={() => {
                      setBackupDirMode('usb')
                      const mounted = (targets || []).find((row: any) => row.mountpoint && String(row.mountpoint).startsWith('/'))
                      const unmounted = (targets || []).find((row: any) => row.device && String(row.device).startsWith('/dev/'))
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
                    <div className="font-bold text-white mb-1 flex items-center gap-2">
                      <Usb size={22} className="text-sky-300 shrink-0 hidden md:block" aria-hidden />
                      {t('backup.ui.target.usb')}
                    </div>
                    <div className="text-xs text-slate-400">{t('backup.ui.target.usbHint')}</div>
                  </button>

                  <button
                    onClick={() => {
                      setBackupDirMode('cloud')
                      // local staging dir stays as-is; default to standard if unset
                      if (!backupDir || typeof backupDir !== 'string') setBackupDir(DEFAULT_BACKUP_DIR)
                      toast(t('backup.ui.cloud.toastChosen'), { duration: 4500 })
                    }}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      backupDirMode === 'cloud'
                        ? 'bg-sky-600/20 border-sky-500'
                        : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
                    }`}
                  >
                    <div className="font-bold text-white mb-1 flex items-center gap-2">
                      <Cloud size={22} className="text-sky-300 shrink-0 hidden md:block" strokeWidth={2} aria-hidden />
                      {t('backup.ui.target.cloud')}
                    </div>
                    <div className="text-xs text-slate-400">{t('backup.ui.target.cloudHint')}</div>
                  </button>

                  <button
                    onClick={() => setBackupDirMode('custom')}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      backupDirMode === 'custom'
                        ? 'bg-sky-600/20 border-sky-500'
                        : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
                    }`}
                  >
                    <div className="font-bold text-white mb-1 flex items-center gap-2">
                      <FolderOpen size={22} className="text-sky-300 shrink-0 hidden md:block" aria-hidden />
                      {t('backup.ui.target.custom')}
                    </div>
                    <div className="text-xs text-slate-400">{t('backup.ui.target.customHint')}</div>
                  </button>
                </div>

                {backupDirMode === 'cloud' && (
                  <>
                    <div className="mt-3 p-3 bg-sky-900/20 border border-sky-700/40 rounded-lg text-sky-100 text-sm">
                      <div className="font-semibold mb-1">{t('backup.ui.cloud.boxTitle')}</div>
                      <div className="text-xs text-sky-100/80">{t('backup.ui.cloud.boxBody')}</div>
                      {!backupSettings?.cloud?.enabled && (
                        <div className="mt-2 text-xs text-yellow-200">{t('backup.ui.cloud.disabledHint')}</div>
                      )}
                    </div>
                    {cloudCompanionSection}
                  </>
                )}

                {backupDirMode === 'usb' && (
                  <div className="mt-3">
                    <label className="block text-sm text-slate-300 mb-2">{t('backup.ui.usb.driveLabel')}</label>
                    {(targets || []).length === 0 && (
                      <div className="mb-3 p-3 bg-yellow-900/20 border border-yellow-700/40 rounded-lg text-yellow-100 text-sm">
                        <div className="font-semibold mb-1">{t('backup.ui.usb.noDriveTitle')}</div>
                        <div className="text-xs text-yellow-100/80">{t('backup.ui.usb.noDriveBody')}</div>
                        <button
                          type="button"
                          onClick={() => loadTargets()}
                          className="mt-3 px-3 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg border border-slate-600 transition-all text-sm"
                        >
                          {t('backup.ui.usb.rescan')}
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
                      <option value="">{t('backup.ui.usb.optionEmpty')}</option>
                      {(targets || []).map((row: any, idx: number) => (
                        <option key={idx} value={row.mountpoint || row.device || ''}>
                          {row.mountpoint
                            ? row.mountpoint
                            : t('backup.ui.usb.notMountedOption', { device: row.device || '' })}
                          {row.label ? ` (${row.label})` : ''} {row.size ? `- ${row.size}` : ''}{' '}
                          {row.tran ? `- ${row.tran}` : ''} {row.model ? `- ${row.model}` : ''}
                        </option>
                      ))}
                    </select>
                    <p className="mt-2 text-xs text-slate-400">
                      {selectedDevice && !selectedTarget ? (
                        <span className="inline-flex items-center gap-2 flex-wrap">
                          <span>
                            {t('backup.ui.usb.unmountedHint')}
                            <span className="text-slate-200 font-semibold"> {t('backup.ui.usb.prepareInline')}</span>{' '}
                            {t('backup.ui.usb.orMount')}{' '}
                          </span>
                          <button
                            type="button"
                            onClick={() => void mountSelectedUsb(selectedDevice)}
                            className="px-2 py-1 bg-slate-700/60 hover:bg-slate-700 text-white rounded-md border border-slate-600 transition-all text-xs"
                          >
                            {t('backup.ui.usb.mountNow')}
                          </button>
                        </span>
                      ) : (
                        <>{t('backup.ui.usb.backupInto', { dir: backupDir })}</>
                      )}
                    </p>

                    {/* USB-Hinweis + Aktion */}
                    {(selectedTarget || selectedDevice) && (
                      <div className="mt-3 p-3 bg-slate-900/40 border border-slate-700 rounded-lg">
                        <div className="flex items-start justify-between gap-3">
                          <div className="text-sm text-slate-300">
                            <div className="font-semibold text-white">{t('backup.ui.usb.statusTitle')}</div>
                            {usbInfo?.status === 'success' ? (
                              <div className="text-xs text-slate-400 mt-1 whitespace-pre-line">
                                {t('backup.ui.usb.fsLine', {
                                  disk: String(usbInfo.disk ?? ''),
                                  partition: String(usbInfo.partition ?? ''),
                                  fstype: String(usbInfo.fstype || t('backup.ui.targetStatus.emDash')),
                                  label: String(usbInfo.label || t('backup.ui.targetStatus.emDash')),
                                  size: String(usbInfo.size || t('backup.ui.targetStatus.emDash')),
                                  isUsb: usbInfo.is_usb ? t('backup.ui.bool.yes') : t('backup.ui.bool.no'),
                                  removable: usbInfo.is_removable ? t('backup.ui.bool.yes') : t('backup.ui.bool.no'),
                                })}
                              </div>
                            ) : (
                              <div className="text-xs text-red-300 mt-1">
                                {usbInfo
                                  ? backupMsg(t, pickStructuredCode(usbInfo) ?? resolveApiFeedbackCode(usbInfo, 'usb_info'))
                                  : backupMsg(t, 'usb_info_error')}
                              </div>
                            )}
                          </div>
                          <div className="flex flex-col gap-2">
                            <button
                              type="button"
                              onClick={() => {
                                setUsbDoFormat(false)
                                setUsbConfirm('')
                                setUsbLabel(t('backup.ui.usbDialog.defaultLabel'))
                                setShowUsbDialog(true)
                              }}
                              className="px-3 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-200 rounded-lg border border-red-700/40 transition-all text-sm"
                            >
                              {t('backup.ui.usb.prepareBtn')}
                            </button>
                            <button
                              type="button"
                              onClick={runUsbEject}
                              className="px-3 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg border border-slate-600 transition-all text-sm"
                            >
                              {t('backup.ui.usb.ejectBtn')}
                            </button>
                          </div>
                        </div>
                        {!checkingTarget && targetCheck?.status === 'success' && targetCheck?.write_test?.success === false && (
                          <div className="mt-2 text-xs text-yellow-200">{t('backup.ui.usb.writeTestHint')}</div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {backupDirMode === 'custom' && (
                  <div className="mt-3">
                    <label className="block text-sm text-slate-300 mb-2">{t('backup.ui.customDir.label')}</label>
                    <input
                      value={backupDir}
                      onChange={(e) => setBackupDir(e.target.value)}
                      placeholder={t('backup.ui.customDir.placeholder')}
                      className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-sky-600"
                    />
                    <p className="mt-2 text-xs text-slate-400">{t('backup.ui.customDir.hint')}</p>
                  </div>
                )}

                {/* Ziel-Status (Speicherplatz + Schreibtest) */}
                <div className="mt-4 p-4 bg-slate-900/40 border border-slate-700 rounded-lg">
                  <div className="flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <div className="text-sm font-semibold text-white">{t('backup.ui.targetStatus.title')}</div>
                      <div className="text-xs text-slate-400 truncate">{backupDir}</div>
                    </div>
                    <div className="text-xs text-slate-300">
                      {checkingTarget ? t('backup.ui.targetStatus.checking') : ' '}
                    </div>
                  </div>

                  {!checkingTarget && targetCheck?.status === 'success' && targetCheck?.storage_validation?.ok === true && (
                    <div className="mt-2 text-xs text-emerald-300/90">{t('backup.ui.targetStatus.storageOk')}</div>
                  )}

                  {!checkingTarget && targetCheck?.status === 'success' && (
                    <div className="mt-3 grid sm:grid-cols-3 gap-3 text-sm items-stretch">
                      <div className="p-3 bg-slate-800/40 border border-slate-700 rounded-lg min-w-0">
                        <div className="text-xs text-slate-400 mb-1">{t('backup.ui.targetStatus.free')}</div>
                        <div className="font-semibold text-white">
                          {targetCheck.fs?.free_human ?? t('backup.ui.targetStatus.emDash')}
                          <span className="text-slate-400 font-normal">
                            {targetCheck.fs?.total_human ? ` / ${targetCheck.fs.total_human}` : ''}
                          </span>
                        </div>
                        {typeof targetCheck.fs?.used_percent === 'number' && (
                          <div className="text-xs text-slate-400">
                            {t('backup.ui.targetStatus.usedPct', { pct: targetCheck.fs.used_percent })}
                          </div>
                        )}
                      </div>
                      <div className="p-3 bg-slate-800/40 border border-slate-700 rounded-lg min-w-0">
                        <div className="text-xs text-slate-400 mb-1">{t('backup.ui.targetStatus.dir')}</div>
                        <div className={`font-semibold ${targetCheck.exists && targetCheck.is_dir ? 'text-green-300' : 'text-yellow-300'}`}>
                          {targetCheck.exists
                            ? targetCheck.is_dir
                              ? t('backup.ui.targetStatus.dirOk')
                              : t('backup.ui.targetStatus.dirNotDir')
                            : t('backup.ui.targetStatus.dirMissing')}
                        </div>
                        {targetCheck.created && (
                          <div className="text-xs text-slate-400">{t('backup.ui.targetStatus.created')}</div>
                        )}
                      </div>
                      <div className="p-3 bg-slate-800/40 border border-slate-700 rounded-lg min-w-0 flex flex-col">
                        <div className="text-xs text-slate-400 mb-1 shrink-0">{t('backup.ui.targetStatus.writeTest')}</div>
                        <div className={`font-semibold shrink-0 ${targetCheck.write_test?.success ? 'text-green-300' : 'text-red-300'}`}>
                          {targetCheck.write_test?.success ? t('backup.ui.okShort') : t('backup.ui.targetStatus.writeFail')}
                        </div>
                        <div className="mt-1 min-h-0 max-h-40 overflow-y-auto overflow-x-hidden rounded-md border border-slate-700/60 bg-slate-950/40 p-2">
                          <div className="text-xs text-slate-200 break-words hyphens-auto">
                            {targetCheck.write_test?.success
                              ? t('backup.ui.okShort')
                              : backupMsg(t, 'write_test_failed')}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {!checkingTarget && targetCheck?.status === 'error' && (
                    <div className="mt-3 text-sm text-red-300">
                      {backupMsg(t, pickStructuredCode(targetCheck) ?? resolveApiFeedbackCode(targetCheck, 'target_check'))}
                    </div>
                  )}
                </div>
              </div>

              {/* Schritt 2: Backup-Typ wählen */}
              <div>
                <h3 className="text-sm font-semibold text-sky-300 mb-1">{t('backup.ui.step2.title')}</h3>
                <label className="block text-white font-semibold mb-2">{t('backup.ui.step2.typeLabel')}</label>
                <div className="grid grid-cols-3 gap-3">
                  {(['full', 'incremental', 'data'] as const).map((typeId) => (
                    <button
                      key={typeId}
                      onClick={() => setBackupType(typeId)}
                      className={`p-4 rounded-lg border-2 transition-all relative group text-left ${
                        backupType === typeId
                          ? 'bg-sky-600/20 border-sky-500'
                          : 'bg-slate-700/30 border-slate-600 hover:border-slate-500'
                      }`}
                    >
                      <div className="font-bold text-white mb-1">{t(`backup.ui.backupType.${typeId}.label`)}</div>
                      <div className="text-xs text-slate-400">{t(`backup.ui.backupType.${typeId}.desc`)}</div>
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-slate-900 text-white text-xs rounded-lg shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 w-72">
                        {t(`backup.ui.backupType.${typeId}.hint`)}
                        <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-900"></div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Schritt 3: Optional verschlüsseln & starten */}
              <div className="p-4 bg-slate-900/40 border border-slate-700 rounded-lg">
                <h3 className="text-sm font-semibold text-sky-300 mb-2">{t('backup.ui.step3.title')}</h3>
                <label className="flex items-center gap-3 mb-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={encryptionEnabled}
                    onChange={(e) => setEncryptionEnabled(e.target.checked)}
                    className="w-5 h-5 accent-purple-500"
                  />
                  <div>
                    <div className="font-semibold text-white">{t('backup.ui.encrypt.enable')}</div>
                    <div className="text-xs text-slate-400">{t('backup.ui.encrypt.sub')}</div>
                  </div>
                </label>
                {encryptionEnabled && (
                  <div className="space-y-3 mt-3">
                    <div>
                      <div className="text-xs text-slate-400 mb-1">{t('backup.ui.encrypt.method')}</div>
                      <select
                        value={encryptionMethod}
                        onChange={(e) => setEncryptionMethod(e.target.value as 'gpg' | 'openssl')}
                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      >
                        <option value="gpg">{t('backup.ui.encrypt.gpg')}</option>
                        <option value="openssl">{t('backup.ui.encrypt.openssl')}</option>
                      </select>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">
                        {t('backup.ui.encrypt.keyLabel')}{' '}
                        {encryptionMethod === 'openssl' ? t('backup.ui.encrypt.keyRequiredSuffix') : ''}
                      </div>
                      <input
                        type="password"
                        value={encryptionKey}
                        onChange={(e) => setEncryptionKey(e.target.value)}
                        placeholder={
                          encryptionMethod === 'gpg'
                            ? t('backup.ui.encrypt.placeholderGpg')
                            : t('backup.ui.encrypt.placeholderSsl')
                        }
                        className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                      />
                      <div className="text-xs text-slate-500 mt-1">
                        {encryptionMethod === 'gpg' ? t('backup.ui.encrypt.hintGpg') : t('backup.ui.encrypt.hintSsl')}
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
                {loading ? t('backup.ui.create.loading') : t('backup.ui.create.button')}
              </button>
            </div>
          </motion.div>
        </div>
        <div className="space-y-4">
          <div className="card bg-gradient-to-br from-yellow-900/30 to-yellow-900/10 border-yellow-500/50">
            <h3 className="text-lg font-bold text-yellow-300 mb-3">{t('backup.ui.notices.title')}</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>{t('backup.ui.notices.li1')}</li>
              <li>{t('backup.ui.notices.li2')}</li>
              <li>{t('backup.ui.notices.li3')}</li>
              <li>{t('backup.ui.notices.li4')}</li>
            </ul>
          </div>
        </div>
      </div>
      </div>
      )}

      {activeTab === 'restore' && (
        <div className="space-y-4">
          <p className="text-slate-400 text-sm">{t('backup.ui.restore.flow')}</p>
          {restorePreviewResult && (
            <div className="p-4 bg-slate-900/60 border border-slate-600 rounded-lg space-y-3">
              <h3 className="text-sm font-semibold text-sky-300">
                {t('backup.preview.title')}
              </h3>
              <p className="text-xs text-slate-300">
                {t('backup.preview.info')}
              </p>
              <div className="grid md:grid-cols-2 gap-3 text-xs text-slate-200">
                <div>
                  <div className="font-semibold">{t('backup.preview.file')}</div>
                  <div className="break-all text-slate-100">{restorePreviewResult.backupFile}</div>
                </div>
                <div>
                  <div className="font-semibold">{t('backup.preview.dir')}</div>
                  <div className="break-all text-slate-100">{restorePreviewResult.previewDir}</div>
                </div>
                <div>
                  <div className="font-semibold">{t('backup.preview.totalEntries')}</div>
                  <div>{restorePreviewResult.totalEntries}</div>
                </div>
                <div>
                  <div className="font-semibold">{t('backup.preview.counts')}</div>
                  <div>
                    {t('backup.preview.countsDetail', {
                      files: restorePreviewResult.analysis?.total_files ?? 0,
                      dirs: restorePreviewResult.analysis?.total_dirs ?? 0,
                      other: restorePreviewResult.analysis?.total_other ?? 0,
                    })}
                  </div>
                </div>
              </div>
              <p className="text-xs text-emerald-300">
                {t('backup.preview.safeHint')}
              </p>
              {Array.isArray(restorePreviewResult.analysis?.system_like_entries) &&
                restorePreviewResult.analysis.system_like_entries.length > 0 && (
                  <div className="p-3 bg-blue-900/40 border border-blue-600/70 rounded-lg">
                    <div className="text-xs font-semibold text-blue-100 mb-1">
                      {t('backup.preview.systemLike.title')}
                    </div>
                    <p className="text-xs text-blue-100 mb-1">
                      {t('backup.preview.systemLike.hint')}
                    </p>
                    <ul className="text-[11px] text-blue-100 max-h-32 overflow-auto space-y-0.5">
                      {restorePreviewResult.analysis.system_like_entries.slice(0, 30).map((p: string, idx: number) => (
                        <li key={idx} className="break-all">• {p}</li>
                      ))}
                    </ul>
                  </div>
                )}
              {Array.isArray(restorePreviewResult.analysis?.blocked_entries) &&
                restorePreviewResult.analysis.blocked_entries.length > 0 && (
                  <div className="p-3 bg-red-900/60 border-2 border-red-500 rounded-lg">
                    <div className="text-xs font-semibold text-red-100 mb-1">
                      {t('backup.preview.blocked.title')}
                    </div>
                    <p className="text-xs text-red-100 mb-1">
                      {t('backup.preview.blocked.hint')}
                    </p>
                    <ul className="text-[11px] text-red-100 max-h-32 overflow-auto space-y-0.5">
                      {restorePreviewResult.analysis.blocked_entries.slice(0, 30).map((p: string, idx: number) => (
                        <li key={idx} className="break-all">• {p}</li>
                      ))}
                    </ul>
                  </div>
                )}
            </div>
          )}
          <div className="grid lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
          {/* Backup-Liste */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="card"
          >
            <h2 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
              <HardDrive className="text-blue-500 hidden md:block shrink-0" aria-hidden />
              {t('backup.ui.restore.listTitle')}
            </h2>
            <p className="text-xs text-slate-400 mb-4">{t('backup.ui.restore.listHint')}</p>

            {/* Schritt 1: Ziel & Medium wählen */}
            <div className="mb-4 p-4 bg-slate-900/40 border border-slate-700 rounded-lg space-y-3">
              <h3 className="text-sm font-semibold text-sky-300 mb-1">{t('backup.ui.restore.step1')}</h3>
              {/* Buttons oben */}
              <div className="flex gap-2 flex-wrap justify-start">
                <button
                  onClick={() => {
                    setBackupDirMode('default')
                    setBackupDir(DEFAULT_BACKUP_DIR)
                    setShowCloudBackups(false)
                    loadBackups()
                  }}
                  className={`px-3 py-2 rounded-lg border text-sm transition-all whitespace-nowrap ${
                    backupDirMode === 'default' && !showCloudBackups
                      ? 'bg-sky-600/20 border-sky-500 text-white'
                      : 'bg-slate-800/40 border-slate-700 text-slate-200 hover:border-slate-500'
                  }`}
                >
                  {t('backup.ui.target.standard')}
                </button>
                <button
                  onClick={() => {
                    setBackupDirMode('usb')
                    setShowCloudBackups(false)
                    loadTargets()
                    // Beim Wechsel zurück zu USB: backupDir auf USB-Pfad setzen und Backups laden,
                    // damit die Liste des zuvor gemounteten Datenträgers angezeigt wird
                    if (selectedTarget) {
                      const usbPath = `${selectedTarget}/pi-installer-backups`
                      setBackupDir(usbPath)
                      loadBackups(usbPath)
                    }
                  }}
                  className={`px-3 py-2 rounded-lg border text-sm transition-all whitespace-nowrap ${
                    backupDirMode === 'usb' && !showCloudBackups
                      ? 'bg-sky-600/20 border-sky-500 text-white'
                      : 'bg-slate-800/40 border-slate-700 text-slate-200 hover:border-slate-500'
                  }`}
                >
                  {t('backup.ui.target.usb').split(' ')[0]}
                </button>
                <button
                  onClick={() => {
                    setBackupDirMode('cloud')
                    setShowCloudBackups(true)
                    loadCloudBackups()
                  }}
                  className={`px-3 py-2 rounded-lg border text-sm transition-all whitespace-nowrap ${
                    backupDirMode === 'cloud'
                      ? 'bg-sky-600/20 border-sky-500 text-white'
                      : 'bg-slate-800/40 border-slate-700 text-slate-200 hover:border-slate-500'
                  }`}
                >
                  {t('backup.ui.target.cloud')}
                </button>
                <button
                  onClick={() => {
                    if (showCloudBackups) {
                      loadCloudBackups()
                    } else {
                      loadBackups()
                    }
                  }}
                  className="px-3 py-2 rounded-lg border text-sm transition-all bg-slate-800/40 border-slate-700 text-slate-200 hover:border-slate-500 whitespace-nowrap"
                >
                  {t('backup.ui.refresh')}
                </button>
              </div>
              {/* Ziel darunter, farblich hervorgehoben */}
              <div className="pt-2 border-t border-slate-700">
                <div className="text-xs text-slate-400 mb-1">{t('backup.ui.restore.pickTarget')}</div>
                <div className="text-sm text-slate-200 font-semibold break-words bg-slate-800/50 px-3 py-2 rounded border border-slate-600">
                  {showCloudBackups ? t('backup.ui.restore.cloudTargetLine') : backupDir}
                </div>
              </div>
              {/* USB-Auswahl, wenn USB-Modus aktiv */}
              {backupDirMode === 'usb' && (
                <div className="mt-3">
                  <label className="block text-sm text-slate-300 mb-2">{t('backup.ui.restore.usbDriveLabel')}</label>
                  {(targets || []).length === 0 ? (
                    <div className="mb-3 p-3 bg-yellow-900/20 border border-yellow-700/40 rounded-lg text-yellow-100 text-sm">
                      <div className="font-semibold mb-1">{t('backup.ui.usb.noDriveTitle')}</div>
                      <div className="text-xs text-yellow-100/80">{t('backup.ui.usb.noDriveBody')}</div>
                      <button
                        type="button"
                        onClick={() => loadTargets()}
                        className="mt-3 px-3 py-2 bg-slate-700/50 hover:bg-slate-700 text-white rounded-lg border border-slate-600 transition-all text-sm"
                      >
                        {t('backup.ui.usb.rescan')}
                      </button>
                    </div>
                  ) : (
                    <select
                      value={selectedTarget || selectedDevice}
                      onChange={(e) => {
                        const v = e.target.value
                        void onUsbSelectChange(v)
                      }}
                      className="w-full bg-slate-800 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-sky-600"
                    >
                      <option value="">{t('backup.ui.usb.optionEmpty')}</option>
                      {(targets || []).map((row: any, idx: number) => (
                        <option key={idx} value={row.mountpoint || row.device || ''}>
                          {row.mountpoint
                            ? row.mountpoint
                            : t('backup.ui.usb.notMountedOption', { device: row.device || '' })}
                          {row.label ? ` (${row.label})` : ''} {row.size ? `- ${row.size}` : ''}{' '}
                          {row.tran ? `- ${row.tran}` : ''} {row.model ? `- ${row.model}` : ''}
                        </option>
                      ))}
                    </select>
                  )}
                </div>
              )}
            </div>

            {showCloudBackups ? cloudCompanionSection : null}

            {/* Schritt 2: Backup auswählen & Aktionen */}
            {showCloudBackups ? (
              cloudBackupsLoading ? (
                <div className="text-center py-8 text-slate-400">
                  <Clock size={48} className="mx-auto mb-4 opacity-50 animate-spin" />
                  <p>{t('backup.ui.cloud.loading')}</p>
                </div>
              ) : cloudBackups.length === 0 ? (
                <div className="text-center py-8 text-slate-400">
                  <Clock size={48} className="mx-auto mb-4 opacity-50" />
                  <p>{t('backup.ui.cloud.empty')}</p>
                </div>
              ) : (
                <>
                  {/* Toolbar mit Aktionen für Cloud-Backups */}
                  {selectedCloudBackups.size > 0 && (
                    <div className="mb-4 p-4 bg-slate-700/50 rounded-lg border border-slate-600 flex flex-wrap items-center gap-3">
                      <span className="text-sm text-slate-300">
                        {t('backup.ui.cloud.selectedCount', { count: selectedCloudBackups.size })}
                      </span>
                      <div className="flex gap-2 flex-wrap">
                        <button
                          onClick={async () => {
                            if (selectedCloudBackups.size === 0) {
                              toast.error(t('backup.i18n.cloud.noneSelected'))
                              return
                            }
                            const files = Array.from(selectedCloudBackups)
                            for (const backupFile of files) {
                              await verifyCloudBackup(String(backupFile))
                            }
                          }}
                          className="px-3 py-2 bg-slate-700/60 hover:bg-slate-700 text-white rounded-lg transition-all text-sm"
                        >
                          {t('backup.i18n.cloud.verify')}
                        </button>
                        <button
                          onClick={async () => {
                            if (selectedCloudBackups.size === 0) {
                              toast.error(t('backup.i18n.cloud.noneSelected'))
                              return
                            }
                            if (selectedCloudBackups.size > 1) {
                              toast.error(t('backup.i18n.cloud.selectOneForRestore'))
                              return
                            }
                            const backupFile = Array.from(selectedCloudBackups)[0]
                            // Cloud-Backups müssen erst heruntergeladen werden
                            toast.error(t('backup.i18n.cloud.restoreUnsupported'), { duration: 10000 })
                          }}
                          disabled={selectedCloudBackups.size !== 1}
                          className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                          <Upload size={16} />
                          {t('backup.ui.restore.restoreButton')}
                        </button>
                        <button
                          onClick={async () => {
                            if (selectedCloudBackups.size === 0) {
                              toast.error(t('backup.i18n.cloud.noneSelected'))
                              return
                            }
                            const count = selectedCloudBackups.size
                            if (!window.confirm(t('backup.i18n.delete.confirmMultiple', { count }))) return
                            
                            // Führe DELETE-Requests parallel aus für bessere Performance
                            const deletePromises = Array.from(selectedCloudBackups).map(async (backupFile) => {
                              try {
                                // Finde das vollständige href aus cloudBackups
                                const backup = cloudBackups.find((b: any) => (b.href || b.file || b.name) === backupFile)
                                // Verwende href wenn verfügbar, sonst name oder file
                                const href = backup?.href || backup?.file || backup?.name || backupFile
                                const fileName = backup?.name || backupFile.split('/').pop() || backupFile
                                
                                const res = await fetchApi('/api/backup/cloud/delete', {
                                  method: 'POST',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({ 
                                    backup_file: href,
                                    href: href,  // Auch als href senden für Kompatibilität
                                    base_url: cloudBaseUrl  // Sende base_url mit für korrekte URL-Konstruktion
                                  }),
                                })
                                const data = await res.json()
                                
                                // Zeige immer die vollständige Response in der Konsole
                                console.log('[Cloud-Delete] Vollständige Response für', fileName, ':', JSON.stringify(data, null, 2))
                                console.log('[Cloud-Delete] backup_file gesendet:', href, 'base_url gesendet:', cloudBaseUrl)
                                
                                // Zeige Debug-Info in der Konsole für Entwickler
                                if (data.debug && Object.keys(data.debug).length > 0) {
                                  console.log('[Cloud-Delete Debug]', fileName, data.debug)
                                } else {
                                  console.warn('[Cloud-Delete] KEINE Debug-Info in Response für', fileName)
                                }
                                
                                return {
                                  success: data.status === 'success',
                                  fileName,
                                }
                              } catch {
                                const backup = cloudBackups.find((b: any) => (b.file || b.name || b.href) === backupFile)
                                const fileName = backup?.name || backupFile.split('/').pop() || backupFile
                                return {
                                  success: false,
                                  fileName,
                                }
                              }
                            })
                            
                            // Warte auf alle Requests
                            const results = await Promise.all(deletePromises)
                            
                            let successCount = 0
                            let failCount = 0
                            const failedNames: string[] = []
                            
                            for (const result of results) {
                              if (result.success) {
                                successCount++
                              } else {
                                failCount++
                                failedNames.push(result.fileName)
                              }
                            }
                            if (successCount > 0) {
                              toast.success(backupMsg(t, 'cloud_delete_ok', { n: successCount }))
                              loadCloudBackups()
                              setSelectedCloudBackups(new Set())
                            }
                            if (failCount > 0) {
                              const filesHint = failedNames.slice(0, 3).join(', ')
                              toast.error(backupMsg(t, 'cloud_delete_partial', { failed: failCount, files: filesHint }), { duration: 15000 })
                            }
                          }}
                          className="px-3 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/40 text-red-100 rounded-lg transition-all text-sm flex items-center gap-2"
                        >
                          <Trash2 size={16} />
                          {t('backup.ui.delete')}
                        </button>
                        <button
                          onClick={() => setSelectedCloudBackups(new Set())}
                          className="px-3 py-2 bg-slate-600/50 hover:bg-slate-600 text-white rounded-lg transition-all text-sm"
                        >
                          {t('backup.ui.deselect')}
                        </button>
                      </div>
                    </div>
                  )}
                  <div className="space-y-3">
                    {/* "Alle auswählen" Checkbox für Cloud-Backups */}
                    <div className="flex items-center gap-2 pb-2 border-b border-slate-700">
                      <button
                        onClick={selectAllCloudBackups}
                        className="flex items-center gap-2 text-sm text-slate-300 hover:text-white transition-colors"
                      >
                        {selectedCloudBackups.size === cloudBackups.length ? (
                          <CheckSquare size={20} className="text-sky-500" />
                        ) : (
                          <Square size={20} className="text-slate-500" />
                        )}
                        <span>
                          {selectedCloudBackups.size === cloudBackups.length
                            ? t('backup.ui.deselectAll')
                            : t('backup.ui.selectAll')}
                        </span>
                      </button>
                    </div>
                    {cloudBackups.map((backup: any, index: number) => {
                      // Verwende href als primären Key, da das die vollständige URL ist
                      const backupKey = backup.href || backup.file || backup.name || `cloud-${index}`
                      return (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className={`p-4 bg-slate-700/30 rounded-lg border ${
                            selectedCloudBackups.has(backupKey)
                              ? 'border-sky-500 bg-slate-700/50'
                              : 'border-slate-600'
                          } flex items-start gap-3 cursor-pointer hover:bg-slate-700/40 transition-colors`}
                          onClick={() => toggleCloudBackupSelection(backupKey)}
                        >
                          <div className="mt-1 shrink-0">
                            {selectedCloudBackups.has(backupKey) ? (
                              <CheckSquare size={20} className="text-sky-500" />
                            ) : (
                              <Square size={20} className="text-slate-500" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="font-semibold text-white mb-1">
                              <div className="flex items-center gap-2 flex-wrap">
                                <span className="break-words">
                                  {backup.file?.split('/').pop() || backup.name || t('backup.ui.unknownFile')}
                                </span>
                                <span className="text-xs px-2 py-1 rounded-full bg-sky-600/25 border border-sky-400/40 text-sky-200 whitespace-nowrap">
                                  {t('backup.ui.cloud.badge')}
                                </span>
                                {(backup.encrypted === true || String(backup.file || backup.name || '').endsWith('.gpg') || String(backup.file || backup.name || '').endsWith('.enc') || String(backup.file || backup.name || '').includes('.tar.gz.gpg') || String(backup.file || backup.name || '').includes('.tar.gz.enc')) && (
                                  <span className="text-xs px-2 py-1 rounded-full bg-purple-600/30 border border-purple-400/40 text-purple-200 flex items-center gap-1 whitespace-nowrap">
                                    <Lock size={12} />
                                    {t('backup.ui.encrypted.badge')}
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-4 text-sm text-slate-400 flex-wrap">
                              {backup.size && <span>📦 {backup.size}</span>}
                              {backup.date && <span>📅 {backup.date}</span>}
                              <span className="text-xs">{t('backup.ui.cloud.locationLine')}</span>
                            </div>
                          </div>
                        </motion.div>
                      )
                    })}
                  </div>
                </>
              )
            ) : backups.length === 0 ? (
              <div className="text-center py-8 text-slate-400">
                <Clock size={48} className="mx-auto mb-4 opacity-50" />
                <p>{t('backup.ui.local.empty')}</p>
                <p className="text-sm mt-2">{t('backup.ui.local.emptyHint')}</p>
              </div>
            ) : (
              <>
                {verifyDiagnosis && (
                  <div className="mb-4 space-y-2">
                    <DiagnosisPanel record={verifyDiagnosis} />
                    {structuredDiagnostics && (
                      <DiagnosticsAssistantPanel result={structuredDiagnostics} level={diagnosticsLevel} />
                    )}
                    <button
                      type="button"
                      onClick={() => setVerifyDiagnosis(null)}
                      className="text-xs text-slate-400 hover:text-slate-200 underline"
                    >
                      {t('diagnosis.dismiss')}
                    </button>
                  </div>
                )}
                {/* Toolbar mit Aktionen */}
                {selectedBackups.size > 0 && (
                  <div className="mb-4 p-4 bg-slate-700/50 rounded-lg border border-slate-600 flex flex-col gap-2">
                    <div className="flex flex-wrap items-center gap-3">
                      <span className="text-sm text-slate-300">
                        {t('backup.selection.count', { count: selectedBackups.size })}
                      </span>
                      <div className="flex gap-2 flex-wrap">
                        <button
                          onClick={verifySelectedBackups}
                          className="px-3 py-2 bg-slate-700/60 hover:bg-slate-700 text-white rounded-lg transition-all text-sm"
                        >
                          {t('backup.verify.basic.button')}
                        </button>
                        <button
                          onClick={restoreSelectedBackup}
                          disabled={selectedBackups.size !== 1}
                          className="px-3 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-all text-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                          <Upload size={16} />
                          {t('backup.restore.preview.button')}
                        </button>
                        <button
                          onClick={deleteSelectedBackups}
                          className="px-3 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/40 text-red-100 rounded-lg transition-all text-sm flex items-center gap-2"
                        >
                          <Trash2 size={16} />
                          {t('backup.delete.selected')}
                        </button>
                        <button
                          onClick={() => setSelectedBackups(new Set())}
                          className="px-3 py-2 bg-slate-600/50 hover:bg-slate-600 text-white rounded-lg transition-all text-sm"
                        >
                          {t('backup.selection.clear')}
                        </button>
                      </div>
                    </div>
                    {Array.from(selectedBackups).some((f) => String(f).includes('pi-backup-inc-')) && (
                      <p className="text-xs text-yellow-300">
                        {t('backup.restore.incrementalNotSupported')}
                      </p>
                    )}
                  </div>
                )}
                <div className="space-y-3">
                  {/* "Alle auswählen" Checkbox */}
                  <div className="flex items-center gap-2 pb-2 border-b border-slate-700">
                    <button
                      onClick={selectAllBackups}
                      className="flex items-center gap-2 text-sm text-slate-300 hover:text-white transition-colors"
                    >
                      {selectedBackups.size === backups.length ? (
                        <CheckSquare size={20} className="text-sky-500" />
                      ) : (
                        <Square size={20} className="text-slate-500" />
                      )}
                      <span>
                        {selectedBackups.size === backups.length ? t('backup.ui.deselectAll') : t('backup.ui.selectAll')}
                      </span>
                    </button>
                  </div>
                  {backups.map((backup, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className={`p-4 bg-slate-700/30 rounded-lg border ${
                        selectedBackups.has(backup.file)
                          ? 'border-sky-500 bg-slate-700/50'
                          : 'border-slate-600'
                      } flex items-start gap-3 cursor-pointer hover:bg-slate-700/40 transition-colors`}
                      onClick={() => toggleBackupSelection(backup.file)}
                    >
                      <div className="mt-1 shrink-0">
                        {selectedBackups.has(backup.file) ? (
                          <CheckSquare size={20} className="text-sky-500" />
                        ) : (
                          <Square size={20} className="text-slate-500" />
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="font-semibold text-white mb-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="break-words">{backup.file.split('/').pop()}</span>
                            {String(backup.file).includes('pi-backup-inc-') && (
                              <span className="text-xs px-2 py-1 rounded-full bg-purple-600/30 border border-purple-400/40 text-purple-200 whitespace-nowrap">
                                {t('backup.ui.badge.incremental')}
                              </span>
                            )}
                            {String(backup.file).includes('pi-backup-full-') && (
                              <span className="text-xs px-2 py-1 rounded-full bg-sky-600/25 border border-sky-400/40 text-sky-200 whitespace-nowrap">
                                {t('backup.ui.badge.full')}
                              </span>
                            )}
                            {String(backup.file).includes('pi-backup-data-') && (
                              <span className="text-xs px-2 py-1 rounded-full bg-emerald-600/25 border border-emerald-400/40 text-emerald-200 whitespace-nowrap">
                                {t('backup.ui.badge.data')}
                              </span>
                            )}
                            {(backup.encrypted === true || String(backup.file).endsWith('.gpg') || String(backup.file).endsWith('.enc') || String(backup.file).includes('.tar.gz.gpg') || String(backup.file).includes('.tar.gz.enc')) && (
                              <span className="text-xs px-2 py-1 rounded-full bg-purple-600/30 border border-purple-400/40 text-purple-200 flex items-center gap-1 whitespace-nowrap">
                                <Lock size={12} />
                                {t('backup.ui.encrypted.badge')}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-slate-400 flex-wrap">
                          <span>📦 {backup.size}</span>
                          <span>📅 {backup.date}</span>
                          {backup.location && <span className="text-xs">📍 {backup.location}</span>}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </>
            )}
          </motion.div>
        </div>
        <div className="space-y-4">
          <div className="card bg-gradient-to-br from-yellow-900/30 to-yellow-900/10 border-yellow-500/50">
            <h3 className="text-lg font-bold text-yellow-300 mb-3">{t('backup.ui.notices.title')}</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>{t('backup.ui.notices.li1')}</li>
              <li>{t('backup.ui.notices.li2')}</li>
              <li>{t('backup.ui.notices.li3')}</li>
              <li>{t('backup.ui.notices.li4')}</li>
            </ul>
          </div>
        </div>
      </div>
      </div>
      )}

      {activeTab === 'clone' && (
      <div className="space-y-6">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-emerald-600/40 bg-emerald-900/20 dark:bg-emerald-900/20 p-6"
        >
          <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 mb-2 flex items-center gap-2">
            <Copy className="text-emerald-500 hidden md:block shrink-0" aria-hidden />
            {t('backup.ui.clone.heroTitle')}
          </h2>
          <p className="text-slate-600 dark:text-slate-400 text-sm mb-4">{t('backup.ui.clone.introBody')}</p>
          <p className="text-xs text-slate-500 dark:text-slate-500 mb-0">{t('backup.ui.clone.introNote')}</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card"
        >
          <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
            <Copy className="text-emerald-500 hidden md:block shrink-0" aria-hidden />
            {t('backup.ui.clone.introTitle')}
          </h2>

          {/* Klon-Job Anzeige */}
          {cloneJob && cloneJob.job_id && cloneJob.job_id !== 'pending' &&
           (cloneJob.status === 'queued' || cloneJob.status === 'running' || cloneJob.status === 'cancel_requested' || !cloneJob.status) && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 bg-emerald-900/20 border border-emerald-700/40 rounded-lg text-emerald-100 mb-6"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                      className="w-5 h-5 border-2 border-emerald-400 border-t-transparent rounded-full shrink-0"
                    />
                    <div className="font-semibold">
                      {cloneJob.status === 'cancel_requested'
                        ? t('runningBackup.title.cancelPending')
                        : typeof (cloneJob as any).progress_pct === 'number'
                          ? t('backup.i18n.clone.runningWithProgress', { pct: (cloneJob as any).progress_pct })
                          : t('backup.i18n.clone.running')}
                    </div>
                    {cloneJob.status !== 'cancel_requested' && (
                      <button
                        onClick={async () => {
                          try {
                            await fetchApi(`/api/backup/jobs/${encodeURIComponent(cloneJob.job_id)}/cancel`, { method: 'POST' })
                            toast(t('runningBackup.toast.cancelRequested'))
                          } catch {
                            toast.error(t('backup.i18n.cancelFailed'))
                          }
                        }}
                        className="ml-auto px-3 py-1 text-xs bg-red-900/50 hover:bg-red-800/50 rounded-lg text-red-200"
                      >
                        {t('runningBackup.cancel')}
                      </button>
                    )}
                  </div>
                  <div className="text-xs text-emerald-100/80 mt-1">
                    {cloneJob.status === 'cancel_requested'
                      ? t('backup.i18n.clone.cancelPending')
                      : backupMsg(t, resolveApiFeedbackCode(cloneJob, 'clone_running'))}
                  </div>
                  {cloneJob.results && cloneJob.results.length > 0 && (
                    <div className="mt-2 text-xs text-emerald-200/90">
                      {backupMsg(t, 'clone_log_lines', { n: cloneJob.results.length })}
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {cloneJob && (cloneJob.status === 'success' || cloneJob.status === 'error' || cloneJob.status === 'cancelled') && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`p-4 rounded-lg mb-6 ${
                cloneJob.status === 'success'
                  ? 'bg-emerald-900/20 border border-emerald-700/40 text-emerald-100'
                  : cloneJob.status === 'cancelled'
                    ? 'bg-yellow-900/20 border border-yellow-700/40 text-yellow-100'
                    : 'bg-red-900/20 border border-red-700/40 text-red-100'
              }`}
            >
              <div className="font-semibold mb-2">
                {cloneJob.status === 'success' ? t('backup.i18n.clone.successLabel') : cloneJob.status === 'cancelled' ? t('backup.i18n.clone.cancelledLabel') : t('backup.i18n.clone.failedLabel')}
              </div>
              <div className="text-sm">
                {backupMsg(t, resolveApiFeedbackCode(cloneJob, 'clone_terminal'))}
              </div>
              {cloneJob.results && cloneJob.results.length > 0 && (
                <div className="mt-2 text-xs opacity-90">
                  {backupMsg(t, 'clone_log_lines', { n: cloneJob.results.length })}
                </div>
              )}
              <button
                onClick={() => setCloneJob(null)}
                className="mt-3 px-3 py-2 bg-slate-700/50 hover:bg-slate-600/50 rounded-lg text-sm"
              >
                {t('runningBackup.close')}
              </button>
            </motion.div>
          )}

          <div className="space-y-4">
            {/* Quelle */}
            {cloneDiskInfo?.source?.device && (
              <div>
                <div className="text-xs text-slate-400 mb-1">{t('backup.ui.clone.source')}</div>
                <div className="p-3 bg-slate-800/50 border border-slate-700 rounded-lg text-slate-200 font-mono">
                  {cloneDiskInfo.source.device} {cloneDiskInfo.source.size && `(${cloneDiskInfo.source.size})`}
                  {cloneDiskInfo.source.model && (
                    <div className="text-xs text-slate-500 mt-1">{cloneDiskInfo.source.model}</div>
                  )}
                </div>
              </div>
            )}

            {/* Ziel */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-slate-400">{t('backup.ui.clone.target')}</span>
                <button
                  type="button"
                  onClick={() => loadCloneDiskInfo(undefined, true)}
                  className="text-xs text-sky-400 hover:text-sky-300"
                >
                  {t('backup.ui.clone.refresh')}
                </button>
              </div>
              <select
                value={cloneTargetDevice}
                onChange={(e) => setCloneTargetDevice(e.target.value)}
                className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-white"
                disabled={!cloneDiskInfo?.targets?.length}
              >
                <option value="">{t('backup.ui.clone.selectPlaceholder')}</option>
                {(cloneDiskInfo?.targets || []).map((ct: any) => (
                  <option key={ct.device} value={ct.device}>
                    {ct.device} – {ct.size || '?'} {ct.model ? `(${ct.model})` : ''}{' '}
                    {ct.tran === 'nvme'
                      ? t('backup.ui.clone.tran.nvme')
                      : ct.tran === 'usb'
                        ? t('backup.ui.clone.tran.usb')
                        : ''}
                  </option>
                ))}
              </select>
              {(!cloneDiskInfo?.targets || cloneDiskInfo.targets.length === 0) && (
                <div className="mt-2 space-y-2">
                  <div className="text-xs text-slate-500">{t('backup.ui.clone.noTargets')}</div>
                  <button
                    onClick={loadCloneDiskInfoWithSudo}
                    className="text-sm px-3 py-2 bg-sky-600/30 hover:bg-sky-600/50 border border-sky-500/50 rounded-lg text-sky-200"
                  >
                    {t('backup.ui.clone.loadWithSudo')}
                  </button>
                </div>
              )}
            </div>

            <button
              onClick={startClone}
              disabled={!cloneTargetDevice || (cloneJob && cloneJob.job_id && cloneJob.job_id !== 'pending' && ['queued', 'running'].includes(cloneJob.status))}
              className="btn-primary w-full"
            >
              {(cloneJob?.status === 'queued' || cloneJob?.status === 'running') ? t('backup.i18n.clone.running') : t('backup.i18n.clone.start.title')}
            </button>
          </div>
        </motion.div>

        <div className="card bg-gradient-to-br from-yellow-900/30 to-yellow-900/10 border-yellow-500/50">
          <h3 className="text-lg font-bold text-yellow-300 mb-3">{t('backup.ui.clone.notesTitle')}</h3>
          <ul className="space-y-2 text-sm text-slate-300">
            <li>{t('backup.ui.clone.noteBoot')}</li>
            <li>{t('backup.ui.clone.noteRoot')}</li>
            <li>{t('backup.ui.clone.noteReboot')}</li>
            <li>{t('backup.ui.clone.noteSd')}</li>
          </ul>
        </div>
      </div>
      )}

      {activeTab === 'settings' && (
      <div className="space-y-4">
        <p className="text-slate-400 text-sm">{t('backup.ui.settings.lead')}</p>
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="card"
          >
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
              <Settings className="text-purple-500 hidden md:block shrink-0" aria-hidden />
              {t('backup.ui.settings.title')}
            </h2>
            <div className="space-y-4">
              <div className="card bg-gradient-to-br from-sky-900/25 to-sky-900/10 border-sky-500/30">
                <h3 className="text-lg font-bold text-sky-300 mb-3">{t('backup.ui.settings.section')}</h3>
              {!backupSettings ? (
                <div className="text-sm text-slate-300">
                  <button className="px-3 py-2 bg-slate-700/50 hover:bg-slate-700 rounded-lg" onClick={loadBackupSettings}>
                    {t('backup.ui.settings.loadBtn')}
                  </button>
                </div>
              ) : (
                <div className="space-y-4 text-sm text-slate-200">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <div className="text-xs text-slate-400 mb-1">{t('backup.ui.settings.retention')}</div>
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
                    <div className="mt-1 text-xs text-slate-400">{t('backup.ui.settings.retentionHint')}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">{t('backup.ui.settings.rules')}</div>
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
                                  name: t('backup.ui.settings.newRuleName'),
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
                                  name: t('backup.ui.settings.newRuleName'),
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
                      {t('backup.ui.settings.addRule')}
                    </button>
                  </div>
                </div>

                <div className="p-3 bg-slate-900/40 border border-slate-700 rounded-lg">
                  <div className="font-semibold text-white mb-2">{t('backup.ui.settings.scheduleRules')}</div>
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
                                  placeholder={t('backup.ui.settings.ruleNamePh')}
                                />
                              </div>

                              <div className="grid grid-cols-2 gap-2">
                                <div>
                                  <div className="text-xs text-slate-400 mb-1">{t('backup.ui.settings.ruleType')}</div>
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
                                    <option value="full">{t('backup.ui.schedule.full')}</option>
                                    <option value="incremental">{t('backup.ui.schedule.incremental')}</option>
                                    <option value="data">{t('backup.ui.schedule.data')}</option>
                                    <option value="personal">{t('backup.ui.schedule.personal')}</option>
                                  </select>
                                </div>
                                <div>
                                  <div className="text-xs text-slate-400 mb-1">{t('backup.ui.settings.target')}</div>
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
                                    <option value="cloud_only">{t('backup.ui.schedule.target.cloud_only')}</option>
                                    <option value="local_and_cloud">{t('backup.ui.schedule.target.local_and_cloud')}</option>
                                    <option value="local">{t('backup.ui.schedule.target.local')}</option>
                                  </select>
                                </div>
                                <div>
                                  <div className="text-xs text-slate-400 mb-1">{t('backup.ui.settings.days')}</div>
                                  <div className="flex flex-wrap gap-2">
                                    {(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const).map((d) => (
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
                                        {t(`backup.ui.weekday.${d}`)}
                                      </label>
                                    ))}
                                  </div>
                                </div>
                                <div>
                                  <div className="text-xs text-slate-400 mb-1">{t('backup.ui.settings.time')}</div>
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
                                  <div className="text-xs text-slate-400 mb-1">{t('backup.ui.settings.keep')}</div>
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
                                    <div className="text-xs text-slate-400 mb-1">{t('backup.ui.settings.personalFolders')}</div>
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
                                          {t(`backup.ui.stdFolder.${f}`)}
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
                                      {t('backup.ui.settings.incrementalPersonal')}
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
                                {t('backup.ui.settings.runNow')}
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
                                {t('backup.ui.settings.removeRule')}
                              </button>
                              <div className="text-xs text-slate-400">
                                {t('backup.ui.settings.timerPrefix')}{' '}
                                {backupSettings._timer_status?.[rule.id]?.enabled || t('backup.ui.targetStatus.emDash')} /{' '}
                                {backupSettings._timer_status?.[rule.id]?.active || t('backup.ui.targetStatus.emDash')}
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-sm text-slate-400">{t('backup.ui.settings.noRules')}</div>
                  )}
                </div>

                <div className="p-3 bg-slate-900/40 border border-slate-700 rounded-lg">
                  {backupSettings.cloud?.enabled ? cloudCompanionSection : null}
                  <div className="font-semibold text-white mb-2">{t('backup.ui.settings.cloudSection')}</div>
                  <div className="text-xs text-slate-400 mb-3">
                    {t('backup.ui.settings.cloudIntroBefore')}{' '}
                    <span className="text-sky-400 font-semibold">{t('backup.ui.settings.cloudIntroLink')}</span>
                  </div>
                  {backupSettings.cloud?.enabled ? (
                    <div className="space-y-2">
                      <div>
                        <div className="text-xs text-slate-400 mb-1">{t('backup.ui.settings.providerLabel')}</div>
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
                                toast.success(t('backup.i18n.cloud.providerSaved'))
                                setBackupSettings(d.settings)
                              }
                            } catch {
                              toast.error(t('backup.i18n.settings.saveFailed'))
                            }
                          }}
                          className="w-full bg-slate-900/50 border border-slate-600 rounded-lg px-3 py-2 text-white text-sm"
                        >
                          <option value="seafile_webdav">{t('backup.ui.provider.seafile_webdav')}</option>
                          <option value="webdav">{t('backup.ui.provider.webdav')}</option>
                          <option value="nextcloud_webdav">{t('backup.ui.provider.nextcloud_webdav')}</option>
                          <option value="s3">{t('backup.ui.provider.s3')}</option>
                          <option value="s3_compatible">{t('backup.ui.provider.s3_compatible')}</option>
                          <option value="google_cloud">{t('backup.ui.provider.google_cloud')}</option>
                          <option value="azure">{t('backup.ui.provider.azure')}</option>
                        </select>
                      </div>
                      {Array.isArray(backupSettings.schedules) && backupSettings.schedules.length > 0 && (
                        <div className="p-2 bg-slate-950/30 border border-slate-800 rounded-lg">
                          <div className="text-xs text-slate-400 mb-1">{t('backup.ui.settings.filterCloudByRule')}</div>
                          <select
                            value={cloudRuleFilter}
                            onChange={(e) => setCloudRuleFilter(e.target.value)}
                            className="w-full bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm"
                          >
                            <option value="">{t('backup.ui.settings.allRules')}</option>
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
                        {cloudBackupsLoading ? t('backup.i18n.cloud.loadingExternal') : t('backup.i18n.cloud.showExternal')}
                      </button>

                      {cloudBackups.length > 0 && (
                        <div className="mt-2 p-2 bg-slate-950/40 border border-slate-800 rounded-lg">
                          <div className="text-xs text-slate-400 mb-2">{t('backup.ui.settings.externalListTitle')}</div>
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
                                      {cloudVerifying[String(b.name)] ? '⏳' : cloudVerified[String(b.name)] === true ? '✓' : t('backup.i18n.cloud.verify')}
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
                      {t('backup.i18n.cloud.uploadDisabledHint')}
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={saveBackupSettings}
                    disabled={settingsLoading}
                    className="w-full px-3 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-lg disabled:opacity-50"
                  >
                    {settingsLoading ? t('backup.i18n.settings.applying') : t('backup.i18n.settings.apply')}
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
            <h3 className="text-lg font-bold text-yellow-300 mb-3">{t('backup.ui.settings.noticesTitle')}</h3>
            <ul className="space-y-2 text-sm text-slate-300">
              <li>{t('backup.ui.notices.li1')}</li>
              <li>{t('backup.ui.notices.li2')}</li>
              <li>{t('backup.ui.notices.li3')}</li>
              <li>{t('backup.ui.notices.li4')}</li>
            </ul>
          </div>
        </div>
      </div>
      </div>
      )}
      </motion.div>
    </div>
  )
}

export default BackupRestore
