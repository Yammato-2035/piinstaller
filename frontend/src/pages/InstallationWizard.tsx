import React, { useState } from 'react'
import { ChevronRight } from 'lucide-react'
import AppIcon from '../components/AppIcon'
import toast from 'react-hot-toast'
import { fetchApi } from '../api'
import { usePlatform } from '../context/PlatformContext'

const InstallationWizard: React.FC = () => {
  const { systemLabel, isRaspberryPi, pageSubtitleLabel, wizardWelcomeHeadline } = usePlatform()
  const [step, setStep] = useState(1)
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

  const steps = [
    { number: 1, title: 'Willkommen', processIcon: 'connect' as const },
    { number: 2, title: 'Sicherheit', processIcon: 'prepare' as const },
    { number: 3, title: 'Benutzer', processIcon: 'prepare' as const },
    { number: 4, title: 'Entwicklung', processIcon: 'prepare' as const },
    { number: 5, title: 'Webserver', processIcon: 'prepare' as const },
    { number: 6, title: 'Zusammenfassung', processIcon: 'complete' as const },
  ]

  const startInstallation = async () => {
    // Prüfe ob sudo-Passwort benötigt wird
    const sudoPassword = prompt('Sudo-Passwort eingeben (für Installation):')
    if (!sudoPassword) {
      toast.error('Sudo-Passwort erforderlich')
      return
    }
    
    setInstalling(true)
    try {
      const response = await fetchApi('/api/install/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...allConfigs,
          sudo_password: sudoPassword,
        }),
      })
      const data = await response.json()
      
      if (data.status === 'success') {
        toast.success(`Installation gestartet: ${data.completed_steps}/${data.total_steps} Schritte abgeschlossen`)
        
        // Zeige Ergebnisse
        if (data.results && data.results.length > 0) {
          console.log('Installations-Ergebnisse:', data.results)
          data.results.forEach((result: string) => {
            if (result.includes('Fehler')) {
              toast.error(result)
            } else {
              toast.success(result, { duration: 3000 })
            }
          })
        }
        
        // Simuliere Progress basierend auf tatsächlichen Schritten
        let progress = (data.completed_steps / data.total_steps) * 100
        setInstallProgress(Math.floor(progress))
        
        const interval = setInterval(async () => {
          // Prüfe Fortschritt vom Server
          const progressResponse = await fetchApi('/api/install/progress')
          const progressData = await progressResponse.json()
          
          if (progressData.progress) {
            progress = progressData.progress
            setInstallProgress(Math.floor(progress))
          } else {
            progress += 5
            if (progress > 95) progress = 95
            setInstallProgress(Math.floor(progress))
          }

          if (progress >= 95) {
            clearInterval(interval)
            setInstalling(false)
            toast.success('Installation abgeschlossen!')
          }
        }, 3000)
      } else {
        if (data.requires_sudo_password) {
          toast.error('Sudo-Passwort erforderlich')
        } else {
          toast.error(data.message || 'Fehler beim Starten der Installation')
        }
        setInstalling(false)
      }

      console.log(data)
    } catch (error) {
      toast.error('Fehler beim Starten der Installation')
      setInstalling(false)
    }
  }

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
          <AppIcon name={s.processIcon} category="process" size={48} className="mb-0.5" />
          <div className="text-sm">{s.title}</div>
        </button>
      ))}
    </div>
  )

  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <div className="page-title-category mb-2 inline-flex">
          <h1 className="flex items-center gap-3">
            <AppIcon name="installation" category="navigation" size={32} />
            Installationsassistent
          </h1>
        </div>
        <p className="text-slate-400">Assistent – {pageSubtitleLabel}</p>
      </div>

      {/* Installation in Progress */}
      {installing && (
        <div className="card bg-gradient-to-br from-green-900/30 to-green-900/10 border-green-500/50">
          <h3 className="text-xl font-bold text-green-300 mb-4 flex items-center gap-2">
            <AppIcon name="running" category="status" size={24} statusColor="ok" />
            Installation läuft
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
            <h2 className="text-3xl font-bold text-white">
              {isRaspberryPi ? '🎉 Willkommen zum PI-Installer!' : `🎉 ${wizardWelcomeHeadline}`}
            </h2>
            <div className="space-y-4">
              <p className="text-slate-300 text-lg">
                Dieser Assistent hilft Ihnen, Ihr System von der Grundkonfiguration auf den nächsten Level zu bringen.
              </p>

              <div className="grid md:grid-cols-2 gap-4 mt-6">
                <FeatureBox
                  icon="🔒"
                  title="Sicherheit"
                  desc="Härtung & automatische Updates"
                />
                <FeatureBox
                  icon="👥"
                  title="Benutzerverwaltung"
                  desc="Mehrere Benutzer mit Rollen"
                />
                <FeatureBox
                  icon="💻"
                  title="Entwicklungsumgebung"
                  desc="IDE, Sprachen, Datenbanken"
                />
                <FeatureBox
                  icon="🌐"
                  title="Webserver"
                  desc="Nginx/Apache + CMS"
                />
              </div>
            </div>

            <div className="bg-blue-900/20 border border-blue-600/50 rounded-lg p-4">
              <p className="text-blue-300 text-sm">
                ⏱️ Die Installation dauert 45-90 Minuten, je nach ausgewählten Komponenten.
              </p>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold text-white">🔒 Schritt 1: Sicherheit</h2>
            <p className="text-slate-300">
              Wählen Sie die Sicherheitsmaßnahmen, die Sie installieren möchten:
            </p>

            <div className="space-y-3">
              <CheckOption
                label="🔥 Firewall (UFW) aktivieren"
                checked={allConfigs.security.enable_firewall}
                onChange={(v) => setAllConfigs({
                  ...allConfigs,
                  security: { ...allConfigs.security, enable_firewall: v }
                })}
              />
              <CheckOption
                label="⚔️ Fail2Ban (Brute-Force Schutz)"
                checked={allConfigs.security.enable_fail2ban}
                onChange={(v) => setAllConfigs({
                  ...allConfigs,
                  security: { ...allConfigs.security, enable_fail2ban: v }
                })}
              />
              <CheckOption
                label="🔄 Automatische Sicherheitsupdates"
                checked={allConfigs.security.enable_auto_updates}
                onChange={(v) => setAllConfigs({
                  ...allConfigs,
                  security: { ...allConfigs.security, enable_auto_updates: v }
                })}
              />
              <CheckOption
                label="🔐 SSH Härtung"
                checked={allConfigs.security.enable_ssh_hardening}
                onChange={(v) => setAllConfigs({
                  ...allConfigs,
                  security: { ...allConfigs.security, enable_ssh_hardening: v }
                })}
              />
              <CheckOption
                label="📝 Audit Logging"
                checked={allConfigs.security.enable_audit_logging}
                onChange={(v) => setAllConfigs({
                  ...allConfigs,
                  security: { ...allConfigs.security, enable_audit_logging: v }
                })}
              />
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold text-white">👥 Schritt 2: Benutzer</h2>
            <p className="text-slate-300">
              Sie können später weitere Benutzer hinzufügen. Ein Administrator-Benutzer wird empfohlen.
            </p>

            <div className="bg-slate-700/30 p-4 rounded-lg">
              <p className="text-slate-400 text-sm">
                Standard Benutzer: pi (existiert bereits)
              </p>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold text-white">💻 Schritt 3: Entwicklungsumgebung</h2>
            <p className="text-slate-300">
              Welche Programmiersprachen und Tools benötigen Sie?
            </p>

            <div className="grid md:grid-cols-2 gap-4">
              <SelectableOption label="🐍 Python" />
              <SelectableOption label="⚡ Node.js" />
              <SelectableOption label="🔹 Go" />
              <SelectableOption label="🦀 Rust" />
              <SelectableOption label="🐘 PostgreSQL" />
              <SelectableOption label="🐬 MySQL" />
              <SelectableOption label="🐳 Docker" />
              <SelectableOption label="🔀 Git" />
            </div>
          </div>
        )}

        {step === 5 && (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold text-white">🌐 Schritt 4: Webserver</h2>
            <p className="text-slate-300">
              Konfigurieren Sie Ihren Webserver und optionales CMS.
            </p>

            <div className="grid md:grid-cols-2 gap-4">
              <SelectableOption label="⚡ Nginx" selected />
              <SelectableOption label="🪚 Apache" />
              <SelectableOption label="🔒 SSL/TLS" selected />
              <SelectableOption label="💻 PHP" />
              <SelectableOption label="📰 WordPress" />
              <SelectableOption label="☁️ Nextcloud" />
            </div>
          </div>
        )}

        {step === 6 && (
          <div className="space-y-6">
            <h2 className="text-3xl font-bold text-white">✓ Zusammenfassung</h2>
            <p className="text-slate-300 mb-6">
              Überprüfen Sie Ihre Einstellungen und starten Sie die Installation:
            </p>

            <div className="space-y-3">
              <SummaryItem icon="🔒" title="Sicherheit" items={['Firewall', 'Fail2Ban', 'Auto-Updates', 'SSH-Härtung']} />
              <SummaryItem icon="👥" title="Benutzer" items={['Standard Benutzer: pi']} />
              <SummaryItem icon="💻" title="Entwicklung" items={['Python, Node.js', 'PostgreSQL']} />
              <SummaryItem icon="🌐" title="Webserver" items={['Nginx mit SSL', 'Cockpit Panel']} />
            </div>

            <button
              onClick={startInstallation}
              disabled={installing}
              className="w-full btn-primary text-lg py-3 mt-8 flex items-center justify-center gap-2"
            >
              🚀 Installation jetzt starten
            </button>
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      {!installing && (
        <div className="flex gap-4 justify-between">
          <button
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1}
            className="btn-secondary px-8"
          >
            ← Zurück
          </button>
          <button
            onClick={() => setStep(Math.min(6, step + 1))}
            disabled={step === 6}
            className="btn-primary px-8 flex items-center gap-2"
          >
            Weiter <ChevronRight size={20} />
          </button>
        </div>
      )}
    </div>
  )
}

const CheckOption = ({ label, checked, onChange }: any) => (
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

const FeatureBox = ({ icon, title, desc }: any) => (
  <div className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
    <div className="text-3xl mb-2">{icon}</div>
    <p className="font-bold text-white">{title}</p>
    <p className="text-sm text-slate-400">{desc}</p>
  </div>
)

const SelectableOption = ({ label, selected = false }: any) => (
  <button
    className={`p-4 rounded-lg border-2 font-semibold transition-all ${
      selected
        ? 'bg-sky-600/20 border-sky-500 text-white'
        : 'bg-slate-700/30 border-slate-600 text-slate-300 hover:border-slate-500'
    }`}
  >
    {label}
  </button>
)

const SummaryItem = ({ icon, title, items }: any) => (
  <div className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
    <p className="font-bold text-white mb-2 flex items-center gap-2">
      {icon} {title}
    </p>
    <ul className="text-sm text-slate-300 space-y-1">
      {items.map((item: string, i: number) => (
        <li key={i}>✓ {item}</li>
      ))}
    </ul>
  </div>
)

export default InstallationWizard
