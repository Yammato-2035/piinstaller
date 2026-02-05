import React, { useEffect, useState, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'

const BACKUP_JOB_STORAGE_KEY = 'pi_installer_running_backup_job'

interface BackupJob {
  job_id: string
  status?: string
  message?: string
  backup_file?: string
  bytes_current?: number
  upload_progress_pct?: number
  remote_file?: string
  warning?: string
  results?: string[]
  encrypted?: boolean
}

const RunningBackupModal: React.FC = () => {
  const [backupJob, setBackupJob] = useState<BackupJob | null>(null)
  const [isOpen, setIsOpen] = useState(false)
  const backupJobNotifiedRef = useRef<Record<string, boolean>>({})
  const hasCheckedOnStartRef = useRef<boolean>(false)
  const shouldPollRef = useRef<boolean>(false)

  // Lade gespeicherten Job beim Start und höre auf Events
  useEffect(() => {
    const loadSavedJob = async () => {
      try {
        const saved = localStorage.getItem(BACKUP_JOB_STORAGE_KEY)
        if (saved) {
          const job = JSON.parse(saved) as BackupJob
          if (job.job_id) {
            // Prüfe, ob Job noch läuft
            try {
              const r = await fetchApi(`/api/backup/jobs/${encodeURIComponent(job.job_id)}`)
              const d = await r.json()
              if (d.status === 'success' && d.job) {
                const currentJob = d.job
                const isRunning = currentJob.status === 'queued' || 
                                 currentJob.status === 'running' || 
                                 currentJob.status === 'cancel_requested' ||
                                 !currentJob.status
                if (isRunning) {
                  setBackupJob(currentJob)
                  setIsOpen(true)
                } else {
                  // Job ist fertig, entferne aus localStorage
                  localStorage.removeItem(BACKUP_JOB_STORAGE_KEY)
                }
              }
            } catch {
              // Job existiert nicht mehr, entferne aus localStorage
              localStorage.removeItem(BACKUP_JOB_STORAGE_KEY)
            }
          }
        }
      } catch {
        // ignore
      }
    }
    loadSavedJob()

    // Höre auf Events für neue Backup-Jobs
    const handleBackupJobStarted = (event: CustomEvent) => {
      const jobData = event.detail as BackupJob
      if (jobData && jobData.job_id) {
        setBackupJob(jobData)
        setIsOpen(true)
        try {
          localStorage.setItem(BACKUP_JOB_STORAGE_KEY, JSON.stringify(jobData))
        } catch {
          // ignore
        }
      }
    }

    window.addEventListener('backup-job-started', handleBackupJobStarted as EventListener)
    
    return () => {
      window.removeEventListener('backup-job-started', handleBackupJobStarted as EventListener)
    }
  }, [])

  // Prüfe einmalig beim Start, dann nur wenn ein Backup läuft
  useEffect(() => {
    let cancelled = false
    let intervalId: number | null = null

    const checkRunningJobs = async () => {
      if (cancelled) return
      
      try {
        // Prüfe zuerst localStorage beim ersten Start
        if (!hasCheckedOnStartRef.current) {
          try {
            const saved = localStorage.getItem(BACKUP_JOB_STORAGE_KEY)
            if (saved) {
              const savedJob = JSON.parse(saved) as BackupJob
              // Prüfe, ob Job noch läuft
              const r = await fetchApi(`/api/backup/jobs/${encodeURIComponent(savedJob.job_id)}`)
              const d = await r.json()
              if (d.status === 'success' && d.job) {
                const currentJob = d.job
                const isRunning = currentJob.status === 'queued' || 
                                 currentJob.status === 'running' || 
                                 currentJob.status === 'cancel_requested' ||
                                 !currentJob.status
                if (isRunning) {
                  setBackupJob(currentJob)
                  setIsOpen(true)
                  shouldPollRef.current = true // Aktiviere Polling
                  hasCheckedOnStartRef.current = true
                  return
                } else {
                  localStorage.removeItem(BACKUP_JOB_STORAGE_KEY)
                }
              } else {
                localStorage.removeItem(BACKUP_JOB_STORAGE_KEY)
              }
            }
          } catch {
            // ignore
          }
        }
        
        // Prüfe Server nach laufenden Jobs
        const r = await fetchApi('/api/backup/jobs')
        const d = await r.json()
        if (cancelled) return
        
        hasCheckedOnStartRef.current = true
        
        if (d.status === 'success' && Array.isArray(d.jobs) && d.jobs.length > 0) {
          const runningJob = d.jobs[0] // Nimm den ersten laufenden Job
          if (runningJob && runningJob.job_id) {
            setBackupJob(runningJob)
            setIsOpen(true)
            shouldPollRef.current = true // Aktiviere Polling
            // Speichere in localStorage
            try {
              localStorage.setItem(BACKUP_JOB_STORAGE_KEY, JSON.stringify(runningJob))
            } catch {
              // ignore
            }
          }
        } else {
          // Keine laufenden Jobs - stoppe Polling
          shouldPollRef.current = false
          if (backupJob) {
            setBackupJob(null)
            setIsOpen(false)
          }
        }
      } catch {
        // ignore
      }
    }

    // Sofort prüfen beim Start
    checkRunningJobs()
    
    // Starte Interval nur wenn Polling aktiviert werden soll
    const startPolling = () => {
      if (intervalId) return // Bereits gestartet
      intervalId = window.setInterval(() => {
        if (!cancelled && shouldPollRef.current) {
          checkRunningJobs()
        } else if (!shouldPollRef.current && intervalId) {
          // Stoppe Interval wenn kein Backup läuft
          window.clearInterval(intervalId)
          intervalId = null
        }
      }, 3000)
    }
    
    // Starte Polling nur wenn ein Backup läuft
    if (shouldPollRef.current) {
      startPolling()
    }

    return () => {
      cancelled = true
      if (intervalId) window.clearInterval(intervalId)
    }
  }, []) // Nur beim Mount ausführen

  // Höre auf Events für neue Backup-Jobs (wenn ein Backup gestartet wird)
  useEffect(() => {
    const handleBackupJobStarted = (event: CustomEvent) => {
      const jobData = event.detail as BackupJob
      if (jobData && jobData.job_id) {
        setBackupJob(jobData)
        setIsOpen(true)
        shouldPollRef.current = true // Aktiviere Polling
        try {
          localStorage.setItem(BACKUP_JOB_STORAGE_KEY, JSON.stringify(jobData))
        } catch {
          // ignore
        }
      }
    }

    window.addEventListener('backup-job-started', handleBackupJobStarted as EventListener)
    
    return () => {
      window.removeEventListener('backup-job-started', handleBackupJobStarted as EventListener)
    }
  }, [])

  // Polling für laufenden Job - nur wenn shouldPollRef aktiv ist
  useEffect(() => {
    if (!backupJob?.job_id || !shouldPollRef.current) return
    
    let cancelled = false
    let intervalId: number | null = null
    
    const tick = async () => {
      if (!shouldPollRef.current || cancelled) return
      try {
        const r = await fetchApi(`/api/backup/jobs/${encodeURIComponent(backupJob.job_id)}`)
        const d = await r.json()
        if (cancelled) return
        
        if (d.status === 'success' && d.job) {
          const job = d.job
          setBackupJob(job)
          
          // Speichere aktualisierten Job
          try {
            localStorage.setItem(BACKUP_JOB_STORAGE_KEY, JSON.stringify(job))
          } catch {
            // ignore
          }

          const terminal = job.status === 'success' || job.status === 'error' || job.status === 'cancelled'
          if (terminal) {
            if (!backupJobNotifiedRef.current[job.job_id]) {
              backupJobNotifiedRef.current[job.job_id] = true
              if (job.status === 'success') {
                toast.success('Backup fertig')
                if (job.warning) toast(String(job.warning), { icon: '⚠️', duration: 6000 })
              } else if (job.status === 'cancelled') {
                toast('Backup abgebrochen', { duration: 6000 })
              } else {
                toast.error(job.message || 'Backup fehlgeschlagen', { duration: 10000 })
              }
            }
            // Stoppe Polling
            shouldPollRef.current = false
            // Entferne aus localStorage nach kurzer Verzögerung
            setTimeout(() => {
              localStorage.removeItem(BACKUP_JOB_STORAGE_KEY)
            }, 5000)
            if (intervalId) window.clearInterval(intervalId)
            intervalId = null
            // Schließe Modal nach 3 Sekunden
            setTimeout(() => setIsOpen(false), 3000)
          }
        }
      } catch {
        // ignore
      }
    }
    
    tick()
    intervalId = window.setInterval(() => {
      if (!cancelled && shouldPollRef.current) tick()
      else if (intervalId) {
        window.clearInterval(intervalId)
        intervalId = null
      }
    }, 2000)
    
    return () => {
      cancelled = true
      if (intervalId) window.clearInterval(intervalId)
    }
  }, [backupJob?.job_id, shouldPollRef.current])

  const cancelBackup = async () => {
    if (!backupJob?.job_id) return
    if (!window.confirm('Backup wirklich abbrechen?')) return
    
    try {
      const r = await fetchApi(`/api/backup/jobs/${encodeURIComponent(backupJob.job_id)}/cancel`, { method: 'POST' })
      const d = await r.json()
      if (d.status === 'success') {
        toast.success('Abbruch angefordert…')
        setBackupJob((j) => (j ? { ...j, status: 'cancel_requested' } : j))
      }
    } catch {
      toast.error('Fehler beim Abbrechen')
    }
  }

  const isRunning = backupJob?.status === 'queued' || 
                   backupJob?.status === 'running' || 
                   backupJob?.status === 'cancel_requested' ||
                   !backupJob?.status

  // Zeige Modal immer, wenn ein Backup läuft, auch wenn isOpen false ist
  const shouldShow = backupJob && (isRunning || isOpen)

  if (!shouldShow) return null

  return (
    <AnimatePresence>
      {shouldShow && (
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -20 }}
          className="fixed top-4 right-4 z-50 max-w-md w-full sm:max-w-lg"
          style={{ pointerEvents: 'none' }}
        >
          <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.95, opacity: 0 }}
            className="bg-slate-800 rounded-lg shadow-2xl border border-slate-700 overflow-hidden"
            style={{ pointerEvents: 'auto' }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="bg-slate-800 border-b border-slate-700 px-4 py-3 flex items-center justify-between">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                {backupJob.status === 'success' && <CheckCircle2 className="w-5 h-5 text-green-500" />}
                {backupJob.status === 'error' && <AlertCircle className="w-5 h-5 text-red-500" />}
                {isRunning && <Loader2 className="w-5 h-5 text-sky-500 animate-spin" />}
                <span className="text-sm sm:text-base">
                  {backupJob.status === 'cancel_requested' ? '⏳ Abbruch läuft…' : 
                   backupJob.message?.includes('Prüfe') ? '☁️ Prüfe Cloud…' : 
                   backupJob.message?.includes('Upload') ? '☁️ Upload läuft…' : 
                   backupJob.status === 'success' ? '✅ Backup fertig' :
                   backupJob.status === 'error' ? '❌ Backup fehlgeschlagen' :
                   '⏳ Backup läuft…'}
                </span>
              </h2>
              <button
                onClick={() => setIsOpen(false)}
                className="text-slate-400 hover:text-white transition-colors ml-2"
                disabled={isRunning}
                title={isRunning ? 'Backup läuft - kann nicht geschlossen werden' : 'Schließen'}
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 space-y-3 max-h-[60vh] overflow-y-auto">
              {backupJob.backup_file && (
                <div className="text-xs text-slate-300">
                  <span className="font-semibold">Datei:</span> <span className="break-words">{String(backupJob.backup_file).split('/').pop()}</span>
                </div>
              )}
              
              {backupJob.status && (
                <div className="text-xs text-slate-300">
                  <span className="font-semibold">Status:</span> <span className="font-semibold">{backupJob.status}</span>
                </div>
              )}

              {typeof backupJob.bytes_current === 'number' && (
                <div className="text-xs text-slate-300">
                  <span className="font-semibold">Größe:</span> {(backupJob.bytes_current / 1024 / 1024).toFixed(1)} MB
                </div>
              )}

              {backupJob.message && (
                <div className="text-xs text-slate-300">
                  <span className="font-semibold">Meldung:</span> {backupJob.message}
                </div>
              )}

              {backupJob.message?.includes('Verschlüsselung') && (
                <div className="p-2 bg-blue-900/20 border border-blue-700/40 rounded-lg text-blue-200 text-xs">
                  🔒 Verschlüsselung läuft…
                </div>
              )}

              {(backupJob.message?.includes('Upload') || backupJob.message?.includes('Prüfe') || 
                backupJob.results?.some((r: string) => String(r).includes('upload'))) && 
               !backupJob.remote_file && (
                <div className="space-y-2">
                  <div className="text-xs text-slate-300">
                    {backupJob.message?.includes('Prüfe') ? 'Prüfe in 1 Min, ob Datei in Cloud…' : 'Upload zu Cloud läuft…'}
                    {typeof backupJob.upload_progress_pct === 'number' && (
                      <span className="ml-2 font-semibold">{backupJob.upload_progress_pct} %</span>
                    )}
                  </div>
                  {typeof backupJob.upload_progress_pct === 'number' && (
                    <div className="w-full bg-slate-700 rounded-full h-1.5">
                      <motion.div
                        className="bg-sky-500 h-1.5 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${backupJob.upload_progress_pct}%` }}
                        transition={{ duration: 0.3 }}
                      />
                    </div>
                  )}
                </div>
              )}

              {backupJob.remote_file && (
                <div className="p-2 bg-green-900/20 border border-green-700/40 rounded-lg text-green-200 text-xs">
                  ✅ Upload erfolgreich: {String(backupJob.remote_file).split('/').pop()}
                </div>
              )}

              {backupJob.warning && (
                <div className="p-2 bg-yellow-900/20 border border-yellow-700/40 rounded-lg">
                  <div className="text-xs text-yellow-300">⚠ {String(backupJob.warning)}</div>
                </div>
              )}

              {isRunning && (
                <div className="flex gap-2 pt-2">
                  <button
                    onClick={cancelBackup}
                    className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors text-xs"
                  >
                    Abbrechen
                  </button>
                </div>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default RunningBackupModal
