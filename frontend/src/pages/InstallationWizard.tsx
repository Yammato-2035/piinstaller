import React, { useEffect, useMemo, useState } from 'react'
import { ChevronRight, Loader2, CheckCircle2, AlertTriangle, Info } from 'lucide-react'
import AppIcon from '../components/AppIcon'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'
import { usePlatform } from '../context/PlatformContext'
import SudoPasswordModal from '../components/SudoPasswordModal'
import { PandaCompanion, PandaRail, type PandaStatus } from '../components/companions'
import PageHeader from '../components/layout/PageHeader'

const InstallationWizard: React.FC = () => {
  const { isRaspberryPi, pageSubtitleLabel, wizardWelcomeHeadline } = usePlatform()
  const [step, setStep] = useState(1)
  const [sudoOpen, setSudoOpen] = useState(false)
  const [installDone, setInstallDone] = useState(false)
  const [installResultText, setInstallResultText] = useState<string[]>([])
  const [systemFacts, setSystemFacts] = useState<any>(null)
  const [systemCheckLoading, setSystemCheckLoading] = useState(false)
  const [allConfigs, setAllConfigs] = useState({
    security: {
      enable_firewall: true,
      enable_fail2ban: true,
      enable_auto_updates: true,
      enable_ssh_hardening: true,
      enable_audit_logging: true,
      open_ports: [22, 80, 443],
    },
    users: [] as any[],
    devenv: null as any,
    webserver: null as any,
    mail: null as any,
  })

  const [installing, setInstalling] = useState(false)
  const [installProgress, setInstallProgress] = useState(0)
  const [targetProfile, setTargetProfile] = useState<'basic' | 'server' | 'media' | 'beginner' | 'advanced'>('beginner')
  const [showDetails, setShowDetails] = useState(false)

  const steps = [
    { number: 1, title: 'System erkennen', processIcon: 'search' as const },
    { number: 2, title: 'Ziel wählen', processIcon: 'connect' as const },
    { number: 3, title: 'Optionen prüfen', processIcon: 'prepare' as const },
    { number: 4, title: 'Ausführen', processIcon: 'write' as const },
    { number: 5, title: 'Ergebnis', processIcon: 'complete' as const },
  ]

  const prerequisites = useMemo(() => {
    const items = [
      { label: 'System erreichbar', ok: !!systemFacts, hint: 'Systemdaten konnten geladen werden.' },
      { label: 'Betriebssystem erkannt', ok: !!systemFacts?.os?.name || !!systemFacts?.platform?.system, hint: systemFacts?.os?.name || systemFacts?.platform?.system || 'Unbekannt' },
      { label: 'Netzwerk verfügbar', ok: !!systemFacts?.network?.online || (systemFacts?.network?.ips?.length ?? 0) > 0, hint: systemFacts?.network?.online ? 'Online' : 'Prüfen' },
      { label: 'Speicher erkannt', ok: (systemFacts?.memory?.total ?? 0) > 0, hint: systemFacts?.memory?.total ? `${Math.round(systemFacts.memory.total / 1024 / 1024 / 1024)} GB RAM` : 'Keine Daten' },
      { label: 'Datenträger erkannt', ok: (systemFacts?.disk?.total ?? 0) > 0, hint: systemFacts?.disk?.total ? `${Math.round(systemFacts.disk.total / 1024 / 1024 / 1024)} GB` : 'Keine Daten' },
    ]
    return items
  }, [systemFacts])

  const riskHints = useMemo(() => {
    const hints: { level: 'info' | 'warning'; text: string }[] = []
    if ((systemFacts?.memory?.total ?? 0) > 0 && systemFacts.memory.total < 2 * 1024 * 1024 * 1024) {
      hints.push({ level: 'warning', text: 'Wenig RAM erkannt. Für größere Module zuerst Basiskonfiguration wählen.' })
    }
    if (!(systemFacts?.network?.online || (systemFacts?.network?.ips?.length ?? 0) > 0)) {
      hints.push({ level: 'warning', text: 'Kein stabiles Netzwerk erkannt. Paketinstallationen können fehlschlagen.' })
    }
    hints.push({ level: 'info', text: 'Während der Einrichtung können Dienste neu gestartet werden.' })
    return hints
  }, [systemFacts])

  const wizardCompanionStatus = useMemo((): PandaStatus => {
    if (installing) return 'info'
    if (installDone && step >= 5) return 'success'
    if (riskHints.some((h) => h.level === 'warning')) return 'warning'
    if (prerequisites.some((p) => !p.ok)) return 'warning'
    return 'info'
  }, [installing, installDone, step, riskHints, prerequisites])

  const pollProgress = async () => {
    let done = false
    while (!done) {
      try {
        const progressResponse = await fetchApi('/api/install/progress')
        const progressData = await progressResponse.json()
        const next = typeof progressData?.progress === 'number' ? progressData.progress : null
        if (next != null) {
          setInstallProgress(Math.max(0, Math.min(100, Math.floor(next))))
          if (next >= 100 || progressData?.status === 'completed') {
            done = true
          }
        } else {
          setInstallProgress((p) => Math.min(95, p + 4))
        }
      } catch {
        setInstallProgress((p) => Math.min(95, p + 3))
      }
      if (!done) {
        await new Promise((resolve) => setTimeout(resolve, 2500))
      }
    }
  }

  const startInstallation = async (sudoPassword: string) => {
    setInstalling(true)
    setInstallDone(false)
    setInstallResultText([])
    setInstallProgress(3)
    try {
      const response = await fetchApi('/api/install/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...allConfigs,
          sudo_password: sudoPassword,
          wizard_profile: targetProfile,
        }),
      })
      const data = await response.json()

      if (data.status === 'success') {
        toast.success('Einrichtung gestartet')
        await pollProgress()
        setInstallProgress(100)
        setInstallDone(true)
        setStep(5)
        const results: string[] = Array.isArray(data.results) ? data.results : []
        setInstallResultText(results.length > 0 ? results : ['Einrichtung abgeschlossen.'])
        toast.success('Einrichtung abgeschlossen')
      } else {
        toast.error(data.message || 'Fehler beim Starten der Einrichtung')
      }
    } catch {
      toast.error('Fehler beim Starten der Einrichtung')
    } finally {
      setInstalling(false)
    }
  }

  const loadSystemFacts = async () => {
    setSystemCheckLoading(true)
    try {
      const response = await fetchApi('/api/system-info?light=1')
      const data = await response.json()
      setSystemFacts(data)
    } catch {
      setSystemFacts(null)
    } finally {
      setSystemCheckLoading(false)
    }
  }

  useEffect(() => {
    loadSystemFacts()
  }, [])

  const StepIndicator = () => (
    <div className="flex gap-2 mb-8">
      {steps.map((s) => (
        <button
          key={s.number}
          onClick={() => setStep(s.number)}
          disabled={s.number > step && !installing}
          className={`flex-1 py-4 rounded-lg text-center font-semibold transition-all flex flex-col items-center gap-1 ${
            step === s.number
              ? 'bg-sky-600 text-white shadow-lg shadow-sky-600/50'
              : step > s.number
              ? 'bg-green-600/50 text-green-200 cursor-pointer'
              : 'bg-slate-700/30 text-slate-400 cursor-not-allowed'
          }`}
        >
          <AppIcon name={s.processIcon} category="process" size={32} className="mb-0.5" />
          <div className="text-sm">{s.title}</div>
        </button>
      ))}
    </div>
  )

  return (
    <div className="space-y-8 animate-fade-in">
      <PageHeader
        visualStyle="hero-card"
        tone="setup"
        title="Setupflow"
        subtitle={`Geführte Einrichtung – ${pageSubtitleLabel}`}
        badge={<AppIcon name="installation" category="navigation" size={32} className="shrink-0" />}
      />

      <PandaRail>
        <PandaCompanion
          type="install"
          size="sm"
          surface="dark"
          frame={false}
          showTrafficLight
          trafficLightPosition="bottom-right"
          status={wizardCompanionStatus}
          title="Installations-Begleiter"
          subtitle="Schritt-für-Schritt-Einrichtung: Voraussetzungen prüfen, Optionen wählen, ausführen. Ampel = geschätzter Stand (Hinweise gelb, Abschluss grün)."
        />
      </PandaRail>

      {/* Installation in Progress */}
      {installing && (
        <div className="card bg-gradient-to-br from-green-900/30 to-green-900/10 border-green-500/50">
          <h3 className="text-xl font-bold text-green-300 mb-4 flex items-center gap-2">
            <Loader2 className="w-6 h-6 text-green-400 animate-spin shrink-0" aria-hidden />
            <AppIcon name="running" category="status" size={24} statusColor="ok" />
            Einrichtung wird ausgeführt
          </h3>
          <div className="space-y-4">
            <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-green-500 to-green-600 transition-all duration-500"
                style={{ width: `${installProgress}%` }}
              />
            </div>
            <p className="text-sm text-slate-300">{installProgress}% abgeschlossen</p>
          </div>
        </div>
      )}

      {/* Step Indicator */}
      {!installing && <StepIndicator />}

      {/* Step Content */}
      <div className="card min-h-96">
        {step === 1 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">
              {isRaspberryPi ? 'System erkennen und prüfen' : wizardWelcomeHeadline}
            </h2>
            <p className="text-slate-300">
              Bevor die Einrichtung startet, prüfen wir die wichtigsten Systeminformationen.
            </p>
            <div className="grid md:grid-cols-2 gap-3">
              {prerequisites.map((item) => (
                <div key={item.label} className="p-3 rounded-lg border border-slate-600 bg-slate-800/40 flex items-start gap-3">
                  {item.ok ? <CheckCircle2 className="text-emerald-400 mt-0.5" size={18} /> : <AlertTriangle className="text-amber-400 mt-0.5" size={18} />}
                  <div>
                    <p className="text-sm font-semibold text-white">{item.label}</p>
                    <p className="text-xs text-slate-400">{item.hint}</p>
                  </div>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <button onClick={loadSystemFacts} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm" disabled={systemCheckLoading}>
                {systemCheckLoading ? 'Prüfe…' : 'System erneut prüfen'}
              </button>
              <button onClick={() => setShowDetails((v) => !v)} className="px-4 py-2 bg-slate-700/70 hover:bg-slate-700 text-white rounded-lg text-sm">
                {showDetails ? 'Details ausblenden' : 'Details anzeigen'}
              </button>
            </div>
            {showDetails && (
              <pre className="bg-slate-900/60 border border-slate-700 rounded-lg p-3 text-xs text-slate-300 overflow-auto max-h-60">
                {JSON.stringify(systemFacts, null, 2)}
              </pre>
            )}
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Ziel auswählen</h2>
            <p className="text-slate-300">
              Wähle ein Setup-Ziel. Du kannst später weitere Module ergänzen.
            </p>
            <div className="grid md:grid-cols-2 gap-3">
              <SelectableOption label="Basis-Setup" desc="Sicherheit, Grundkonfiguration, stabile Basis." selected={targetProfile === 'basic'} onClick={() => setTargetProfile('basic')} />
              <SelectableOption label="Server / Dienste" desc="Web-/Netzwerkdienste und Betriebsgrundlagen." selected={targetProfile === 'server'} onClick={() => setTargetProfile('server')} />
              <SelectableOption label="Medien / Tools" desc="Medienorientierte Pakete und Hilfstools." selected={targetProfile === 'media'} onClick={() => setTargetProfile('media')} />
              <SelectableOption label="Anfänger-Setup" desc="Geführte, vorsichtige Standardeinstellungen." selected={targetProfile === 'beginner'} onClick={() => setTargetProfile('beginner')} />
              <SelectableOption label="Erweiterte Einrichtung" desc="Mehr Optionen und technische Konfiguration." selected={targetProfile === 'advanced'} onClick={() => setTargetProfile('advanced')} />
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Optionen und Hinweise</h2>
            <p className="text-slate-300">
              Diese Optionen werden angewendet. Prüfe die Hinweise vor dem Start.
            </p>
            <div className="space-y-3">
              <CheckOption
                label="Firewall aktivieren"
                checked={allConfigs.security.enable_firewall}
                onChange={(v: boolean) => setAllConfigs((prev) => ({ ...prev, security: { ...prev.security, enable_firewall: v } }))}
              />
              <CheckOption
                label="Fail2Ban aktivieren"
                checked={allConfigs.security.enable_fail2ban}
                onChange={(v: boolean) => setAllConfigs((prev) => ({ ...prev, security: { ...prev.security, enable_fail2ban: v } }))}
              />
              <CheckOption
                label="Automatische Sicherheitsupdates"
                checked={allConfigs.security.enable_auto_updates}
                onChange={(v: boolean) => setAllConfigs((prev) => ({ ...prev, security: { ...prev.security, enable_auto_updates: v } }))}
              />
              <CheckOption
                label="SSH-Härtung"
                checked={allConfigs.security.enable_ssh_hardening}
                onChange={(v: boolean) => setAllConfigs((prev) => ({ ...prev, security: { ...prev.security, enable_ssh_hardening: v } }))}
              />
              <CheckOption
                label="Audit-Logging"
                checked={allConfigs.security.enable_audit_logging}
                onChange={(v: boolean) => setAllConfigs((prev) => ({ ...prev, security: { ...prev.security, enable_audit_logging: v } }))}
              />
            </div>
            <div className="space-y-2">
              {riskHints.map((hint, idx) => (
                <div key={`${hint.level}-${idx}`} className={`rounded-lg border p-3 text-sm flex items-start gap-2 ${hint.level === 'warning' ? 'bg-amber-900/20 border-amber-600/50 text-amber-200' : 'bg-sky-900/20 border-sky-600/50 text-sky-200'}`}>
                  {hint.level === 'warning' ? <AlertTriangle size={16} className="mt-0.5 shrink-0" /> : <Info size={16} className="mt-0.5 shrink-0" />}
                  <span>{hint.text}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Ausführen</h2>
            <p className="text-slate-300">
              Starte jetzt die Einrichtung. Fortschritt und Rückmeldungen werden live angezeigt.
            </p>
            <div className="p-4 rounded-xl border border-slate-600 bg-slate-800/40">
              <p className="text-sm text-slate-200 mb-2">Ausgewähltes Profil: <span className="font-semibold text-white">{targetProfile}</span></p>
              <p className="text-xs text-slate-400">Während der Einrichtung können Dienste neu gestartet werden.</p>
            </div>
            <button
              onClick={() => setSudoOpen(true)}
              disabled={installing}
              className="w-full btn-primary text-lg py-3 mt-2 flex items-center justify-center gap-2"
            >
              {installing ? <Loader2 className="animate-spin" size={18} /> : null}
              Einrichtung starten
            </button>
          </div>
        )}

        {step === 5 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-white">Ergebnis</h2>
            <p className="text-slate-300">
              {installDone ? 'Einrichtung abgeschlossen. Prüfe die Ergebnisse und starte mit den nächsten Schritten.' : 'Noch keine abgeschlossene Einrichtung vorhanden.'}
            </p>
            <div className="space-y-3">
              {(installResultText.length > 0 ? installResultText : ['Noch keine Ergebnisdaten vorhanden.']).map((line, i) => (
                <div key={i} className="p-3 rounded-lg bg-slate-800/50 border border-slate-600 text-sm text-slate-200">
                  {line}
                </div>
              ))}
            </div>
            <div className="grid md:grid-cols-3 gap-3">
              <button onClick={() => toast('Zur Übersicht: Dashboard öffnen')} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm">Zur Übersicht</button>
              <button onClick={() => toast('Logs findest du unter Einstellungen > Logs')} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm">Logs ansehen</button>
              <button onClick={() => toast('Weitere Module über App-Store oder Sidebar öffnen')} className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm">Weitere Module</button>
            </div>
          </div>
        )}
      </div>

      <SudoPasswordModal
        open={sudoOpen}
        title="Sudo-Berechtigung für Einrichtung"
        subtitle="Für Installation und Systemkonfiguration wird ein Passwort benötigt."
        confirmText="Einrichtung starten"
        onCancel={() => setSudoOpen(false)}
        onConfirm={async (password) => {
          setSudoOpen(false)
          await startInstallation(password)
        }}
      />

      {/* Navigation Buttons */}
      {!installing && (
        <div className="flex gap-4 justify-between">
          <button
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1}
            className="btn-secondary px-8"
          >
            Zurück
          </button>
          <button
            onClick={() => setStep(Math.min(5, step + 1))}
            disabled={step === 5}
            className="btn-primary px-8 flex items-center gap-2"
          >
            Weiter <ChevronRight size={20} />
          </button>
        </div>
      )}
    </div>
  )
}

const CheckOption = ({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) => (
  <label className="flex items-center gap-3 p-4 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 cursor-pointer transition-all">
    <input
      type="checkbox"
      checked={checked}
      onChange={(e) => onChange(e.target.checked)}
      className="w-5 h-5 accent-sky-600"
    />
    <span className="font-medium text-white">{label}</span>
  </label>
)

const SelectableOption = ({
  label,
  desc,
  selected = false,
  onClick,
}: {
  label: string
  desc: string
  selected?: boolean
  onClick: () => void
}) => (
  <button
    onClick={onClick}
    className={`p-4 rounded-lg border-2 font-semibold transition-all text-left ${
      selected
        ? 'bg-sky-600/20 border-sky-500 text-white'
        : 'bg-slate-700/30 border-slate-600 text-slate-300 hover:border-slate-500'
    }`}
  >
    <p>{label}</p>
    <p className="text-xs mt-1 opacity-85">{desc}</p>
  </button>
)

export default InstallationWizard
