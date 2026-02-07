import React, { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Lock, X } from 'lucide-react'

interface SudoPasswordModalProps {
  open: boolean
  title?: string
  subtitle?: string
  confirmText?: string
  /** Option „Ohne Prüfung speichern“ anzeigen (bei hängender sudo-Prüfung nutzbar) */
  showSkipTest?: boolean
  onCancel: () => void
  onConfirm: (password: string, skipTest?: boolean) => Promise<void> | void
}

const SudoPasswordModal: React.FC<SudoPasswordModalProps> = ({
  open,
  title = 'Sudo-Passwort erforderlich',
  subtitle = 'Für diese Aktion werden Administrator-Rechte benötigt.',
  confirmText = 'Bestätigen',
  showSkipTest = true,
  onCancel,
  onConfirm,
}) => {
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [skipTest, setSkipTest] = useState(false)

  useEffect(() => {
    if (!open) {
      setPassword('')
      setLoading(false)
      setSkipTest(false)
    }
  }, [open])

  const submit = async () => {
    if (!password.trim()) return
    setLoading(true)
    try {
      await onConfirm(password, skipTest)
    } finally {
      setLoading(false)
    }
  }

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50"
            onClick={() => !loading && onCancel()}
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="card bg-slate-800/95 border border-slate-700 max-w-md w-full shadow-2xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-sky-600/20 rounded-lg">
                    <Lock className="text-sky-400" size={22} />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-white">{title}</h2>
                    <p className="text-xs text-slate-400">{subtitle}</p>
                  </div>
                </div>
                <button
                  onClick={() => !loading && onCancel()}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <X className="text-slate-400" size={20} />
                </button>
              </div>

              <label className="block text-sm font-medium text-slate-300 mb-2">
                Sudo-Passwort
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !loading) submit()
                }}
                className="w-full px-4 py-3 bg-slate-900/50 border border-slate-600 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all"
                placeholder="••••••••"
                autoFocus
              />
              <p className="mt-2 text-xs text-slate-400">
                Die Eingabe ist verdeckt und wird nur für diese Session gespeichert.
              </p>

              {showSkipTest && (
                <label className="mt-3 flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={skipTest}
                    onChange={(e) => setSkipTest(e.target.checked)}
                    className="rounded border-slate-600 bg-slate-800 text-sky-500 focus:ring-sky-500"
                  />
                  <span className="text-sm text-slate-400">
                    Ohne Prüfung speichern (falls die App hängt)
                  </span>
                </label>
              )}

              <div className="mt-5 flex gap-3">
                <button
                  onClick={() => !loading && onCancel()}
                  className="flex-1 px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                  disabled={loading}
                >
                  Abbrechen
                </button>
                <button
                  onClick={submit}
                  className="flex-1 px-4 py-3 bg-sky-600 hover:bg-sky-500 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
                  disabled={loading || !password.trim()}
                >
                  {loading ? (
                    <>
                      <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Prüfe…
                    </>
                  ) : (
                    confirmText
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

export default SudoPasswordModal

