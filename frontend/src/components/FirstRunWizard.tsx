import React, { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Home, Cloud, Tv, Code, ChevronRight, CheckCircle, Package, Cpu, HardDrive, Activity } from 'lucide-react'
import { usePlatform } from '../context/PlatformContext'
import { fetchApi } from '../api'
import AppIcon from './AppIcon'

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

/** Phase 7: Empfohlene erste Schritte – gleiche Aufgaben wie Dashboard (Plan 6.5 Schritt 3). */
const FIRST_STEPS_CARDS = [
  { pageId: 'wizard' as const, title: 'System einrichten', desc: 'Geführter Assistent für Grundkonfiguration, Sicherheit und Benutzer.', icon: 'installation' as const, style: 'sky' },
  { pageId: 'app-store' as const, title: 'Apps installieren', desc: 'Fertige Pakete für Media-Server, NAS, Smart Home und mehr.', icon: 'app-store' as const, style: 'emerald' },
  { pageId: 'backup' as const, title: 'Backup erstellen', desc: 'System sichern oder wiederherstellen, bevor du Neues ausprobierst.', icon: 'backup' as const, style: 'indigo' },
  { pageId: 'monitoring' as const, title: 'Systemzustand prüfen', desc: 'CPU, Speicher, Temperatur und Dienste im Blick behalten.', icon: 'monitoring' as const, style: 'amber' },
  { pageId: 'learning' as const, title: 'Lernen & entdecken', desc: 'Beispiele und Ideen, was du mit deinem System machen kannst.', icon: 'documentation' as const, style: 'teal' },
  { pageId: 'control-center' as const, title: 'Erweiterte Funktionen', desc: 'Netzwerk, Dienste und Entwickler-Werkzeuge für Fortgeschrittene.', icon: 'advanced' as const, style: 'slate' },
]

interface FirstRunWizardProps {
  onComplete: (experienceLevel?: 'beginner' | 'advanced' | 'developer') => void
  setCurrentPage?: (page: string) => void
  systemInfo?: any
}

const FirstRunWizard: React.FC<FirstRunWizardProps> = ({ onComplete, setCurrentPage, systemInfo }) => {
  const { wizardWelcomeHeadline } = usePlatform()
  const [step, setStep] = useState(1)
  const [selected, setSelected] = useState<string[]>([])
  const [experienceLevel, setExperienceLevel] = useState<'beginner' | 'advanced' | 'developer'>('beginner')
  const [savingProfile, setSavingProfile] = useState(false)

  const handleInterestToggle = useCallback((id: string) => {
    setSelected(prev => (prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]))
  }, [])

  const recommended = selected.length > 0
    ? selected.flatMap(s => RECOMMENDED_APPS[s] || []).filter((v, i, a) => a.findIndex(x => x.id === v.id) === i).slice(0, 3)
    : DEFAULT_RECOMMENDED

  const persistProfile = useCallback(async () => {
    setSavingProfile(true)
    try {
      await fetchApi('/api/user-profile', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ experience_level: experienceLevel }),
      })
    } catch {
      // stiller Fehler – Wizard soll nicht blockieren
    } finally {
      setSavingProfile(false)
    }
  }, [experienceLevel])

  const handleDone = useCallback(async () => {
    try {
      localStorage.setItem(FIRST_RUN_DONE_KEY, '1')
    } catch { /* ignore */ }
    await persistProfile()
    onComplete(experienceLevel)
    if (setCurrentPage) setCurrentPage('dashboard')
  }, [onComplete, setCurrentPage, persistProfile, experienceLevel])

  /** Phase 7: Wizard abschließen und zu einer Seite wechseln (Empfohlene erste Schritte). */
  const handleFirstStepNavigate = useCallback(async (pageId: string) => {
    try {
      localStorage.setItem(FIRST_RUN_DONE_KEY, '1')
    } catch { /* ignore */ }
    await persistProfile()
    onComplete(experienceLevel)
    if (setCurrentPage) setCurrentPage(pageId)
  }, [persistProfile, onComplete, experienceLevel, setCurrentPage])

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
                key="step0-systemcheck"
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 12 }}
              >
                <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 mb-2">
                  Systemcheck
                </h2>
                <p className="text-slate-600 dark:text-slate-400 mb-4 text-sm">
                  Wir schauen kurz, auf welcher Hardware PI-Installer läuft. So können wir bessere Empfehlungen geben.
                </p>
                <div className="grid gap-3 mb-6">
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-100 dark:bg-slate-800/60">
                    <Cpu className="w-5 h-5 text-sky-500" />
                    <div className="flex-1">
                      <div className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                        {systemInfo?.is_raspberry_pi ? 'Raspberry Pi' : 'Linux-System'}
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        {systemInfo?.cpu_summary?.name || systemInfo?.cpu_name || 'CPU erkannt'}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-100 dark:bg-slate-800/60">
                    <HardDrive className="w-5 h-5 text-emerald-500" />
                    <div className="flex-1">
                      <div className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                        Speicher & Laufwerk
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        RAM: {systemInfo?.memory?.total ? `${Math.round(systemInfo.memory.total / (1024 * 1024 * 1024))} GB` : 'wird ermittelt'} ·
                        {' '}Systemlaufwerk: {systemInfo?.disk?.total ? `${Math.round(systemInfo.disk.total / (1024 * 1024 * 1024))} GB` : 'wird ermittelt'}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 rounded-xl bg-slate-100 dark:bg-slate-800/60">
                    <Activity className="w-5 h-5 text-amber-500" />
                    <div className="flex-1">
                      <div className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                        Internetverbindung
                      </div>
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        {systemInfo?.network?.online
                          ? 'Online – Updates und App-Installationen sind möglich.'
                          : 'Nicht sicher – falls etwas nicht lädt, prüfe bitte deine Netzwerkverbindung.'}
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex justify-end">
                  <button
                    onClick={() => setStep(2)}
                    className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium inline-flex items-center gap-2"
                  >
                    Weiter <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </motion.div>
            )}

            {step === 2 && (
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
                <p className="text-slate-600 dark:text-slate-400 mb-4">
                  Damit wir dir passende Inhalte anzeigen können: Wie vertraut bist du mit Linux und Raspberry Pi?
                </p>
                <div className="space-y-3 mb-6 text-left">
                  <button
                    type="button"
                    onClick={() => setExperienceLevel('beginner')}
                    className={`w-full p-3 rounded-xl border-2 text-left transition-colors ${
                      experienceLevel === 'beginner'
                        ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
                        : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500'
                    }`}
                  >
                    <div className="font-semibold text-sm text-slate-800 dark:text-slate-100">Einsteiger</div>
                    <div className="text-xs text-slate-600 dark:text-slate-400">
                      Klare Erklärungen, sichere Voreinstellungen, nur die wichtigsten Funktionen.
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setExperienceLevel('advanced')}
                    className={`w-full p-3 rounded-xl border-2 text-left transition-colors ${
                      experienceLevel === 'advanced'
                        ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
                        : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500'
                    }`}
                  >
                    <div className="font-semibold text-sm text-slate-800 dark:text-slate-100">Fortgeschritten</div>
                    <div className="text-xs text-slate-600 dark:text-slate-400">
                      Mehr Einstellungen und Tools, aber weiterhin mit Hinweisen zu Risiken.
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setExperienceLevel('developer')}
                    className={`w-full p-3 rounded-xl border-2 text-left transition-colors ${
                      experienceLevel === 'developer'
                        ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20'
                        : 'border-slate-200 dark:border-slate-600 hover:border-slate-300 dark:hover:border-slate-500'
                    }`}
                  >
                    <div className="font-semibold text-sm text-slate-800 dark:text-slate-100">Entwickler</div>
                    <div className="text-xs text-slate-600 dark:text-slate-400">
                      Alle Module sichtbar, inklusive Dev-Umgebung, Docker und Server-Diensten.
                    </div>
                  </button>
                </div>
                <div className="flex justify-between">
                  <span />
                  <button
                    onClick={() => setStep(3)}
                    className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium inline-flex items-center gap-2"
                  >
                    Weiter <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </motion.div>
            )}

            {/* Phase 7: Schritt 3 – Empfohlene erste Schritte (Plan 6.5) */}
            {step === 3 && (
              <motion.div
                key="step3-first-steps"
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 12 }}
              >
                <h2 className="text-xl font-bold text-slate-800 dark:text-slate-100 mb-2">
                  Empfohlene erste Schritte
                </h2>
                <p className="text-slate-600 dark:text-slate-400 mb-4 text-sm">
                  Wähle, womit du starten möchtest – oder sieh dir alles auf dem Startbildschirm an.
                </p>
                <div className="grid gap-2 mb-6 max-h-[50vh] overflow-y-auto pr-1">
                  {FIRST_STEPS_CARDS.map((card) => {
                    const styleMap: Record<string, string> = {
                      sky: 'border-sky-300 dark:border-sky-600/60 bg-sky-50 dark:bg-sky-900/20 hover:bg-sky-100 dark:hover:bg-sky-900/30',
                      emerald: 'border-emerald-300 dark:border-emerald-600/60 bg-emerald-50 dark:bg-emerald-900/20 hover:bg-emerald-100 dark:hover:bg-emerald-900/30',
                      indigo: 'border-indigo-300 dark:border-indigo-600/60 bg-indigo-50 dark:bg-indigo-900/20 hover:bg-indigo-100 dark:hover:bg-indigo-900/30',
                      amber: 'border-amber-300 dark:border-amber-600/60 bg-amber-50 dark:bg-amber-900/20 hover:bg-amber-100 dark:hover:bg-amber-900/30',
                      teal: 'border-teal-300 dark:border-teal-600/60 bg-teal-50 dark:bg-teal-900/20 hover:bg-teal-100 dark:hover:bg-teal-900/30',
                      slate: 'border-slate-300 dark:border-slate-600 bg-slate-100 dark:bg-slate-700/40 hover:bg-slate-200 dark:hover:bg-slate-700/60',
                    }
                    return (
                      <button
                        key={card.pageId}
                        type="button"
                        onClick={() => handleFirstStepNavigate(card.pageId)}
                        className={`flex items-start gap-3 p-3 rounded-xl border-2 text-left transition-colors ${styleMap[card.style] || styleMap.slate}`}
                      >
                        <AppIcon name={card.icon} category="navigation" size={24} className="mt-0.5 shrink-0" />
                        <div className="min-w-0">
                          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{card.title}</p>
                          <p className="text-xs text-slate-600 dark:text-slate-400">{card.desc}</p>
                        </div>
                      </button>
                    )
                  })}
                </div>
                <div className="flex justify-between items-center gap-4">
                  <button onClick={() => setStep(2)} className="text-slate-600 dark:text-slate-400 hover:underline text-sm">Zurück</button>
                  <div className="flex gap-2">
                    {setCurrentPage && (
                      <button
                        type="button"
                        onClick={() => handleFirstStepNavigate('dashboard')}
                        className="px-4 py-2.5 bg-slate-200 dark:bg-slate-600 hover:bg-slate-300 dark:hover:bg-slate-500 text-slate-800 dark:text-slate-100 rounded-xl font-medium text-sm"
                      >
                        Zum Start
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => setStep(4)}
                      className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium inline-flex items-center gap-2 text-sm"
                    >
                      Weiter zu App-Vorschlägen <ChevronRight className="w-5 h-5" />
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Schritt 4: Interessen für App-Vorschläge */}
            {step === 4 && (
              <motion.div
                key="step4-interests"
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
                    onClick={() => setStep(3)}
                    className="text-slate-600 dark:text-slate-400 hover:underline"
                  >
                    Zurück
                  </button>
                  <button
                    onClick={() => setStep(5)}
                    className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-medium inline-flex items-center gap-2"
                  >
                    Weiter <ChevronRight className="w-5 h-5" />
                  </button>
                </div>
              </motion.div>
            )}

            {/* Schritt 5: Empfohlene Apps + Abschluss */}
            {step === 5 && (
              <motion.div
                key="step5-apps"
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
                    onClick={() => setStep(4)}
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
