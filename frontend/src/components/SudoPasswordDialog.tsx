import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { fetchApi } from '../api'
import { Lock, X, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

interface SudoPasswordDialogProps {
  onPasswordSaved: () => void
}

const SudoPasswordDialog: React.FC<SudoPasswordDialogProps> = ({ onPasswordSaved }) => {
  const [show, setShow] = useState(false)
  const [password, setPassword] = useState('')
  const [skipTest, setSkipTest] = useState(true)
  const [loading, setLoading] = useState(false)
  const [checking, setChecking] = useState(true)
  const [backendReachable, setBackendReachable] = useState(true)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    const maxRetries = 3

    const run = async () => {
      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 15000)
        try {
          const response = await fetchApi('/api/users/sudo-password/check', {
            signal: controller.signal,
          })
          clearTimeout(timeoutId)
          if (!mountedRef.current) return

          if (!response.ok) {
            if (attempt === maxRetries) {
              setBackendReachable(false)
              setShow(true)
            }
            continue
          }

          const data = await response.json()
          if (!mountedRef.current) return

          if (data.status === 'success' && !data.has_password) {
            setShow(true)
          } else {
            onPasswordSaved()
          }
          if (mountedRef.current) setChecking(false)
          return
        } catch (error) {
          clearTimeout(timeoutId)
          if (!mountedRef.current) return
          if (attempt < maxRetries) {
            await new Promise((r) => setTimeout(r, 1500))
            continue
          }
          if (error instanceof Error && error.name === 'AbortError') {
            setBackendReachable(false)
          } else {
            console.error('Fehler beim Prüfen des sudo-Passworts:', error)
            setBackendReachable(false)
          }
          setShow(true)
        }
        if (attempt === maxRetries && mountedRef.current) setChecking(false)
      }
    }

    run()
    return () => {
      mountedRef.current = false
    }
  }, [onPasswordSaved])

  const handleSave = async () => {
    if (!password.trim()) {
      toast.error('Bitte geben Sie das sudo-Passwort ein')
      return
    }

    setLoading(true)
    try {
      const response = await fetchApi('/api/users/sudo-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sudo_password: password, skip_test: skipTest }),
      })
      let data: { status?: string; message?: string; detail?: string } = {}
      try {
        data = await response.json()
      } catch {
        toast.error(
          'Ungültige Antwort vom Backend. Bitte zuerst „PI-Installer Backend starten“ (Port 8000).',
          { duration: 5000 }
        )
        return
      }
      if (data.status === 'success') {
        sessionStorage.setItem('sudo_password_saved', 'true')
        const checkRes = await fetchApi('/api/users/sudo-password/check')
        try {
          const checkData = await checkRes.json()
          if (checkData.status === 'success' && !checkData.has_password) {
            toast.success('Sudo-Passwort gespeichert')
            toast('Hinweis: Backend meldet kein Passwort. Evtl. mehrere Worker?', { icon: '⚠️', duration: 5000 })
          } else {
            toast.success('Sudo-Passwort gespeichert')
          }
        } catch {
          toast.success('Sudo-Passwort gespeichert')
        }
        setShow(false)
        onPasswordSaved()
      } else {
        const msg = data.message || data.detail || 'Sudo-Passwort konnte nicht gespeichert werden.'
        toast.error(msg)
      }
    } catch (error) {
      toast.error(
        'Fehler beim Speichern – Backend erreichbar? Starten Sie zuerst „PI-Installer Backend starten“ (Port 8000).',
        { duration: 6000 }
      )
      console.error(error)
    } finally {
      setLoading(false)
    }
  }

  const handleSkip = () => {
    toast('Sie können das sudo-Passwort später in den Benutzereinstellungen eingeben', { icon: 'ℹ️' })
    setShow(false)
    onPasswordSaved()
  }

  // Zeige nichts während der Prüfung
  if (checking) {
    return null
  }

  return (
    <AnimatePresence>
      {show && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50"
            onClick={handleSkip}
          />
          
          {/* Dialog */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="card bg-slate-800/95 backdrop-blur-xl border border-slate-700 max-w-md w-full shadow-2xl">
              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-sky-600/20 rounded-lg">
                    <Lock className="text-sky-400" size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">Sudo-Passwort erforderlich</h2>
                    <p className="text-sm text-slate-400">Für Systemoperationen benötigt</p>
                  </div>
                </div>
                <button
                  onClick={handleSkip}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <X className="text-slate-400" size={20} />
                </button>
              </div>

              {/* Backend nicht erreichbar */}
              {!backendReachable && (
                <div className="mb-4 p-4 bg-red-900/30 border border-red-700/50 rounded-lg">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="text-red-400 mt-0.5 shrink-0" size={20} />
                    <div className="flex-1">
                      <p className="text-sm font-medium text-red-200">Backend nicht erreichbar</p>
                      <p className="text-xs text-red-300/90 mt-1">
                        Bitte zuerst „PI-Installer Backend starten“ (Port 8000) ausführen, dann hier erneut speichern.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Info */}
              <div className="mb-6 p-4 bg-yellow-900/20 border border-yellow-800/50 rounded-lg">
                <div className="flex items-start gap-3">
                  <AlertCircle className="text-yellow-400 mt-0.5" size={20} />
                  <div className="flex-1">
                    <p className="text-sm text-yellow-200">
                      Das sudo-Passwort wird nur für die aktuelle Session gespeichert und nicht dauerhaft gesichert.
                    </p>
                  </div>
                </div>
              </div>

              {/* Input */}
              <form
                className="mb-6"
                onSubmit={(e) => {
                  e.preventDefault()
                  if (!loading && password.trim()) handleSave()
                }}
              >
                <label htmlFor="sudo-password" className="block text-sm font-medium text-slate-300 mb-2">
                  Sudo-Passwort
                </label>
                <input
                  id="sudo-password"
                  type="password"
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Ihr sudo-Passwort eingeben"
                  className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all"
                  autoFocus
                />
                <p className="mt-2 text-xs text-slate-400">
                  Das Passwort wird verwendet für: Firewall-Konfiguration, Benutzerverwaltung, System-Updates, etc.
                </p>
                <label className="mt-3 flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={skipTest}
                    onChange={(e) => setSkipTest(e.target.checked)}
                    className="rounded border-slate-500 bg-slate-800 text-sky-500 focus:ring-sky-500"
                  />
                  <span className="text-sm text-slate-400">
                    Ohne Prüfung speichern (Standard; beim ersten Einsatz wird geprüft)
                  </span>
                </label>
              </form>

              {/* Actions */}
              <div className="flex gap-3">
                <button
                  onClick={handleSkip}
                  disabled={loading}
                  className="flex-1 px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Später
                </button>
                <button
                  onClick={handleSave}
                  disabled={loading || !password.trim()}
                  className="flex-1 px-4 py-3 bg-sky-600 hover:bg-sky-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Speichere...
                    </>
                  ) : (
                    <>
                      <Lock size={18} />
                      Speichern
                    </>
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

export default SudoPasswordDialog
