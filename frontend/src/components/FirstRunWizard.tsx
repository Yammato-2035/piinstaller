import React, { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Home, Cloud, Tv, Code, ChevronRight, CheckCircle, Package, Wifi, Shield, Database } from 'lucide-react'
import { usePlatform } from '../context/PlatformContext'

export const FIRST_RUN_DONE_KEY = 'pi-installer-first-run-done'

const INTERESTS = [
  { id: 'smarthome', label: 'Smart Home steuern', icon: Home },
  { id: 'cloud', label: 'Dateien teilen (Cloud)', icon: Cloud },
  { id: 'media', label: 'Medien streamen', icon: Tv },
  { id: 'dev', label: 'Entwickeln lernen', icon: Code },
] as const

const RECOMMENDED_APPS: Record<string, { id: string; name: string; desc: string }[]> = {
  smarthome: [
    { id: 'home-assistant', name: 'Home Assistant', desc: 'Smart Home zentral steuern' },
    { id: 'node-red', name: 'Node-RED', desc: 'Automatisierungen visuell bauen' },
    { id: 'pi-hole', name: 'Pi-hole', desc: 'Werbung im Netz blockieren' },
  ],
  cloud: [
    { id: 'nextcloud', name: 'Nextcloud', desc: 'Eigene Cloud für Dateien & Kalender' },
    { id: 'pi-hole', name: 'Pi-hole', desc: 'Werbung im Netz blockieren' },
    { id: 'home-assistant', name: 'Home Assistant', desc: 'Smart Home optional' },
  ],
  media: [
    { id: 'jellyfin', name: 'Jellyfin', desc: 'Medien streamen (Filme, Musik)' },
    { id: 'pi-hole', name: 'Pi-hole', desc: 'Werbung blockieren' },
    { id: 'nextcloud', name: 'Nextcloud', desc: 'Dateien teilen' },
  ],
  dev: [
    { id: 'code-server', name: 'VS Code Server', desc: 'Code im Browser bearbeiten' },
    { id: 'node-red', name: 'Node-RED', desc: 'Flows programmieren' },
    { id: 'home-assistant', name: 'Home Assistant', desc: 'Smart Home & Automatisierung' },
  ],
}

const DEFAULT_RECOMMENDED = [
  { id: 'home-assistant', name: 'Home Assistant', desc: 'Smart Home zentral steuern' },
  { id: 'nextcloud', name: 'Nextcloud', desc: 'Eigene Cloud für Dateien' },
  { id: 'pi-hole', name: 'Pi-hole', desc: 'Werbung im Netz blockieren' },
]

interface FirstRunWizardProps {
  onComplete: () => void
  setCurrentPage?: (page: string) => void
}

const FirstRunWizard: React.FC<FirstRunWizardProps> = ({ onComplete, setCurrentPage }) => {
  const { wizardWelcomeHeadline } = usePlatform()
  const [step, setStep] = useState(1)
  const [selected, setSelected] = useState<string[]>([])

  const handleInterestToggle = useCallback((id: string) => {
    setSelected(prev => (prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]))
  }, [])

  const recommended = selected.length > 0
    ? selected.flatMap(s => RECOMMENDED_APPS[s] || []).filter((v, i, a) => a.findIndex(x => x.id === v.id) === i).slice(0, 3)
    : DEFAULT_RECOMMENDED

  const handleDone = useCallback(() => {
    try {
      localStorage.setItem(FIRST_RUN_DONE_KEY, '1')
    } catch { /* ignore */ }
    onComplete()
    if (setCurrentPage) setCurrentPage('app-store')
  }, [onComplete, setCurrentPage])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/90 dark:bg-slate-950/95 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white dark:bg-slate-800 rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-y-auto"
      >
        <div className="p-8">
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 12 }}
                className="text-center"
              >
                <h2 className="text-2xl font-bold text-slate-800 dark:text-slate-100 mb-2">
                  {wizardWelcomeHeadline}
                </h2>
                <p className="text-slate-600 dark:text-slate-400 mb-8">
                  In wenigen Schritten zeigen wir dir, was möglich ist und welche Apps zu dir passen.
                </p>
                <button
                  onClick={() => setStep(2)}
                  className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium inline-flex items-center gap-2"
                >
                  Weiter <ChevronRight className="w-5 h-5" />
                </button>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div
                key="step2-optional"
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 12 }}
              >
                <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 mb-2">
                  Optional: Später einrichten
                </h2>
                <p className="text-slate-600 dark:text-slate-400 mb-6 text-sm">
                  Du kannst jetzt direkt zu den App-Vorschlägen oder zuerst Netzwerk, Sicherheit oder Backup einrichten.
                </p>
                <div className="grid gap-3 mb-6">
                  {setCurrentPage && (
                    <>
                      <button
                        type="button"
                        onClick={() => { setCurrentPage('settings'); onComplete(); try { localStorage.setItem(FIRST_RUN_DONE_KEY, '1') } catch { /* ignore */ } }}
                        className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700/50 text-left"
                      >
                        <Wifi className="w-5 h-5 text-sky-500" />
                        <span className="font-medium">Netzwerk (WLAN/Ethernet)</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => { setCurrentPage('security'); onComplete(); try { localStorage.setItem(FIRST_RUN_DONE_KEY, '1') } catch { /* ignore */ } }}
                        className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700/50 text-left"
                      >
                        <Shield className="w-5 h-5 text-emerald-500" />
                        <span className="font-medium">Sicherheit (Passwort ändern)</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => { setCurrentPage('backup'); onComplete(); try { localStorage.setItem(FIRST_RUN_DONE_KEY, '1') } catch { /* ignore */ } }}
                        className="flex items-center gap-3 p-3 rounded-xl border border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-700/50 text-left"
                      >
                        <Database className="w-5 h-5 text-amber-500" />
                        <span className="font-medium">Backup einrichten</span>
                      </button>
                    </>
                  )}
                </div>
                <div className="flex justify-between">
                  <button onClick={() => setStep(1)} className="text-slate-600 dark:text-slate-400 hover:underline">Zurück</button>
                  <button onClick={() => setStep(3)} className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium inline-flex items-center gap-2">
                    Weiter zu App-Vorschlägen <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 12 }}
              >
                <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 mb-2">
                  Was möchtest du tun?
                </h2>
                <p className="text-slate-600 dark:text-slate-400 mb-6 text-sm">
                  Wähle ein oder mehrere Ziele – wir empfehlen dir passende Apps.
                </p>
                <div className="grid gap-3 mb-8">
                  {INTERESTS.map(({ id, label, icon: Icon }) => (
                    <button
                      key={id}
                      type="button"
                      onClick={() => handleInterestToggle(id)}
                      className={`flex items-center gap-3 p-4 rounded-xl border-2 text-left transition-colors ${
                        selected.includes(id)
                          ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-800 dark:text-emerald-200'
                          : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500'
                      }`}
                    >
                      <Icon className="w-6 h-6 shrink-0" />
                      <span className="font-medium">{label}</span>
                      {selected.includes(id) && <CheckCircle className="w-5 h-5 ml-auto text-emerald-600" />}
                    </button>
                  ))}
                </div>
                <div className="flex justify-between">
                  <button
                    onClick={() => setStep(2)}
                    className="text-slate-600 dark:text-slate-400 hover:underline"
                  >
                    Zurück
                  </button>
                  <button
                    onClick={() => setStep(4)}
                    className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium inline-flex items-center gap-2"
                  >
                    Weiter <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </motion.div>
            )}

            {step === 4 && (
              <motion.div
                key="step4"
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 12 }}
              >
                <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 mb-2">
                  Empfohlene Apps für dich
                </h2>
                <p className="text-slate-600 dark:text-slate-400 mb-6 text-sm">
                  Diese Apps kannst du im App Store mit einem Klick installieren.
                </p>
                <div className="space-y-3 mb-8">
                  {recommended.map(app => (
                    <div
                      key={app.id}
                      className="flex items-center gap-3 p-3 rounded-xl bg-slate-100 dark:bg-slate-700/50"
                    >
                      <Package className="w-5 h-5 text-slate-500" />
                      <div className="flex-1 min-w-0">
                        <div className="font-medium text-slate-800 dark:text-slate-100">{app.name}</div>
                        <div className="text-sm text-slate-500 dark:text-slate-400">{app.desc}</div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex justify-between">
                  <button
                    onClick={() => setStep(3)}
                    className="text-slate-600 dark:text-slate-400 hover:underline"
                  >
                    Zurück
                  </button>
                  <button
                    onClick={handleDone}
                    className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium inline-flex items-center gap-2"
                  >
                    App Store erkunden <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  )
}

export default FirstRunWizard
