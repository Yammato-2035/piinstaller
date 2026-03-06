import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BookOpen, Cloud, HardDrive, Settings, Cpu, Monitor, HelpCircle, Film,
  LayoutDashboard, Zap, Shield, Users, Code, Globe, Mail, Home, Music, Activity, Database, Scan,
  Package, LayoutGrid, Radio, Image,
} from 'lucide-react'
import { usePlatform } from '../context/PlatformContext'

type SectionId =
  | 'dashboard' | 'wizard' | 'presets' | 'einstellungen' | 'security' | 'users'
  | 'devenv' | 'webserver' | 'mailserver' | 'nas'   | 'homeautomation' | 'musicbox' | 'kino-streaming' | 'learning'
  | 'monitoring' | 'backup-restore' | 'raspberry-pi-config' | 'control-center' | 'periphery-scan'
  | 'cloud' | 'desktop-app' | 'freenove-case' | 'dualdisplay' | 'radio-app' | 'picture-frame-app' | 'troubleshooting' | 'versionen'

const SECTIONS: { id: SectionId; label: string; icon: React.ElementType }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'wizard', label: 'Assistent', icon: Zap },
  { id: 'presets', label: 'Voreinstellungen', icon: Settings },
  { id: 'einstellungen', label: 'Einstellungen', icon: Settings },
  { id: 'security', label: 'Sicherheit', icon: Shield },
  { id: 'users', label: 'Benutzer', icon: Users },
  { id: 'devenv', label: 'Dev-Umgebung', icon: Code },
  { id: 'webserver', label: 'Webserver', icon: Globe },
  { id: 'mailserver', label: 'Mailserver', icon: Mail },
  { id: 'nas', label: 'NAS', icon: HardDrive },
  { id: 'homeautomation', label: 'Hausautomatisierung', icon: Home },
  { id: 'musicbox', label: 'Musikbox', icon: Music },
  { id: 'kino-streaming', label: 'Kino / Streaming', icon: Film },
  { id: 'learning', label: 'Lerncomputer', icon: BookOpen },
  { id: 'monitoring', label: 'Monitoring', icon: Activity },
  { id: 'backup-restore', label: 'Backup & Restore', icon: Database },
  { id: 'raspberry-pi-config', label: 'Raspberry Pi Config', icon: Cpu },
  { id: 'control-center', label: 'Control Center', icon: Settings },
  { id: 'periphery-scan', label: 'Peripherie-Scan (Assimilation)', icon: Scan },
  { id: 'cloud', label: 'Cloud-Einstellungen', icon: Cloud },
  { id: 'desktop-app', label: 'Desktop-App (Tauri)', icon: Monitor },
  { id: 'freenove-case', label: 'Freenove Pro – 4,3″ Touchscreen im Gehäuse', icon: Package },
  { id: 'dualdisplay', label: 'Dualdisplay DSI0 + HDMI1 – Zwei Monitore gleichzeitig', icon: LayoutGrid },
  { id: 'radio-app', label: 'Radio-App (DSI Radio)', icon: Radio },
  { id: 'picture-frame-app', label: 'Bilderrahmen', icon: Image },
  { id: 'troubleshooting', label: 'FAQ – Häufige Fragen & Lösungen', icon: HelpCircle },
  { id: 'versionen', label: 'Versionen & Changelog', icon: BookOpen },
]

/** Screenshot-Bild oder Platzhalter. src optional – ohne src nur Platzhalter. */
function ScreenshotImg({ src, alt, title, hint }: { src?: string; alt: string; title?: string; hint?: string }) {
  const [error, setError] = React.useState(false)
  const usePlaceholder = !src || error
  if (usePlaceholder) {
    return (
      <div className="my-4 p-4 border-2 border-dashed border-slate-500 rounded-lg bg-slate-900/30">
        <p className="text-sm font-medium text-slate-400 mb-1">📷 Screenshot: {title || alt}</p>
        <p className="text-xs text-slate-500">{hint || 'Bild nicht geladen.'}</p>
      </div>
    )
  }
  return (
    <figure className="my-4">
      <img
        src={src}
        alt={alt}
        className="max-w-full rounded-lg border border-slate-600 shadow-lg"
        onError={() => setError(true)}
      />
      {title && <figcaption className="text-xs text-slate-500 mt-1">{title}</figcaption>}
    </figure>
  )
}

/** Ausschnitt eines Screenshots – zoomt auf einen Bereich (object-position: x% y%). */
function ScreenshotDetail({ src, alt, title, position = '50% 50%', height = 220 }: {
  src?: string; alt: string; title: string; position?: string; height?: number
}) {
  const [error, setError] = React.useState(false)
  if (!src || error) return null
  return (
    <figure className="my-3">
      <div className="rounded-lg border border-slate-600 overflow-hidden bg-slate-900" style={{ height }}>
        <img
          src={src}
          alt={alt}
          className="w-full h-full object-cover"
          style={{ objectPosition: position }}
          onError={() => setError(true)}
        />
      </div>
      <figcaption className="text-xs text-slate-500 mt-1">{title}</figcaption>
    </figure>
  )
}

const Documentation: React.FC = () => {
  const [activeChapter, setActiveChapter] = useState<SectionId>('dashboard')
  const { systemLabel, systemLabelPossessive } = usePlatform()

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col sm:flex-row gap-6 min-h-0"
    >
      {/* Menü links */}
      <aside
        className="w-full sm:w-56 flex-shrink-0 sm:sticky sm:top-8 sm:self-start rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-4"
        aria-label="Kapitel"
      >
        <h2 className="text-sm font-semibold text-slate-400 dark:text-slate-400 uppercase tracking-wider mb-3 px-2">
          Dokumentation
        </h2>
        <nav className="flex flex-col gap-1">
          {SECTIONS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setActiveChapter(id)}
              className={`flex items-center gap-2 w-full text-left px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeChapter === id
                  ? 'bg-sky-600 text-white dark:bg-sky-600 dark:text-white'
                  : 'text-slate-300 hover:bg-slate-700/60 hover:text-white dark:text-slate-300 dark:hover:bg-slate-700/60 dark:hover:text-white'
              }`}
            >
              <Icon size={16} className="shrink-0 opacity-80" />
              {label}
            </button>
          ))}
        </nav>
      </aside>

      {/* Inhalt: nur aktives Kapitel */}
      <div className="flex-1 min-w-0">
        <div className="mb-4 p-3 bg-sky-900/20 border border-sky-700/40 rounded-lg">
          <p className="text-sm text-slate-300">
            <strong className="text-sky-300">PI-Installer Handbuch</strong> – Nutze die Kapitel links für Anleitungen, Screenshots und Schritt-für-Schritt-Anweisungen zu jedem Bereich.
          </p>
        </div>
        <AnimatePresence mode="wait">
          {activeChapter === 'dashboard' && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <LayoutDashboard className="text-sky-500" />
                Dashboard
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">
                  Das Dashboard ist die Startseite des PI-Installers und gibt einen Überblick über den Zustand deines {systemLabel}.
                </p>
                <div className="p-3 bg-slate-900/40 border border-slate-600 rounded-lg">
                  <h4 className="text-sm font-semibold text-sky-300 mb-1">📖 Handbuch: Erste Schritte</h4>
                  <ol className="list-decimal list-inside text-xs space-y-1 text-slate-300">
                    <li>Öffne den PI-Installer im Browser (http://localhost:3001) oder als Desktop-App</li>
                    <li>Das Dashboard zeigt sofort Systeminfos, CPU, RAM und Sensoren</li>
                    <li>Nutze die Quick-Links für schnellen Sprung zu Assistent, Sicherheit, Backup</li>
                    <li>Bei „Backend nicht erreichbar“: Backend automatisch starten mit <code className="bg-slate-700 px-1 rounded">./scripts/install-backend-service.sh</code> (richtet systemd-Service ein) oder einmalig <code className="bg-slate-700 px-1 rounded">./start-backend.sh</code></li>
                  </ol>
                </div>
                <ScreenshotImg src="/docs/screenshots/screenshot-dashboard.png" alt="Dashboard" title="Dashboard mit Systeminfos und Karten" hint="Zeigt Karten Systeminformationen, CPU & Grafik, Sensoren." />
                <h4 className="text-base font-semibold text-white">Ausschnitt: Quick-Links</h4>
                <ScreenshotDetail src="/docs/screenshots/screenshot-dashboard.png" alt="Quick-Links" title="Quick-Links für schnelle Navigation" position="50% 85%" height={140} />
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Funktionen</h3>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li><strong>Systeminformationen:</strong> CPU, Hauptspeicher gesamt, Arbeitsspeicher (RAM) mit Typ (DDR4/DDR5), Kapazität und Takt; Motherboard; Grafik getrennt als Integriert (iGPU) und Grafikkarte (diskret) mit Handelsbezeichnung und Grafikspeicher (z. B. NVIDIA RTX 4070 Laptop · 8 GB GDDR6); Betriebssystem</li>
                    <li><strong>CPU & Grafik:</strong> Auslastung pro physikalischem Kern, Temperatur; Grafik getrennt Integrierte Grafik (iGPU) und Grafikkarte (diskret) mit Kurzname und Speicher; Link „Treiber beim Hersteller suchen“ (Intel/AMD)</li>
                    <li><strong>Sensoren & Schnittstellen:</strong> Alle Temperatursensoren (thermal_zone, hwmon), Laufwerke (inkl. NVMe), Lüfter, angeschlossene Displays</li>
                    <li><strong>Systembezogene Treiber:</strong> Alle PCI-Geräte mit Treiber-Status (geladen oder „—“)</li>
                    <li><strong>Quick-Links:</strong> Sprung zu Assistent, Sicherheit, Musikbox, Backup, Einstellungen usw.</li>
                  </ul>
                </div>
                <ScreenshotImg src="/docs/screenshots/screenshot-dashboard.png" alt="Dashboard" title="Dashboard mit Systeminfos und Karten" hint="Zeigt Karten Systeminformationen, CPU & Grafik, Sensoren." />
                <div className="card-info">
                  <h4 className="text-sm font-semibold  mb-1">💡 Tipp</h4>
                  <p className="text-xs opacity-95">
                    Wenn „Backend nicht erreichbar“ erscheint: Backend als Service einrichten mit <code className="bg-slate-700 px-1 rounded">./scripts/install-backend-service.sh</code> oder mit <code className="bg-slate-700 px-1 rounded">./start-backend.sh</code> starten, dann Seite neu laden. <strong>System-Update:</strong> Über „System-Update (apt update & upgrade)“ → „Im Terminal ausführen“ ein Terminal öffnen; Passwort dort eingeben. Nutze die Quick-Links, um schnell zu den häufig genutzten Bereichen zu wechseln.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'wizard' && (
            <motion.div
              key="wizard"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <Zap className="text-amber-500" />
                Assistent
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">
                  Der Assistent führt dich Schritt für Schritt durch die Erstinstallation bzw. Konfiguration des {systemLabel}.
                </p>
                <div className="p-3 bg-slate-900/40 border border-slate-600 rounded-lg">
                  <h4 className="text-sm font-semibold text-amber-300 mb-1">📖 Handbuch: Assistent nutzen</h4>
                  <ol className="list-decimal list-inside text-xs space-y-1 text-slate-300">
                    <li>Menü → Assistent öffnen</li>
                    <li>Bereiche auswählen (Sicherheit, Benutzer, Webserver, NAS …)</li>
                    <li>„Installation starten“ – Sudo-Passwort eingeben, falls abgefragt</li>
                    <li>Fortschrittsanzeige abwarten; danach Bereiche einzeln nachjustieren</li>
                  </ol>
                </div>
                <ScreenshotImg src="/docs/screenshots/screenshot-wizard.png" alt="Assistent – Auswahl der Komponenten" title="Assistent – Auswahl der Komponenten" />
                <h4 className="text-base font-semibold text-white">Ausschnitt: Bereichsauswahl</h4>
                <ScreenshotDetail src="/docs/screenshots/screenshot-wizard.png" alt="Assistent Checkboxen" title="Checkboxen für Sicherheit, Benutzer, Webserver usw." position="50% 35%" height={200} />
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Funktionen</h3>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li>Auswahl der zu installierenden Bereiche (z. B. Sicherheit, Benutzer, Webserver, NAS, Musikbox)</li>
                    <li>Fortschrittsanzeige während der Installation</li>
                    <li>Bei Bedarf Abfrage des Sudo-Passworts für Administrator-Aktionen</li>
                  </ul>
                </div>
                <ScreenshotImg src="/docs/screenshots/screenshot-wizard.png" alt="Assistent – Auswahl der Komponenten" title="Assistent – Auswahl der Komponenten" />
                <div className="card-info">
                  <h4 className="text-sm font-semibold  mb-1">💡 Tipp</h4>
                  <p className="text-xs opacity-95">
                    Starte den Assistenten direkt nach der ersten Einrichtung. Halte dein Sudo-Passwort bereit; bei „Sudo-Passwort erforderlich“ öffnet sich ein Dialog – dort eingeben und bestätigen.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'presets' && (
            <motion.div
              key="presets"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <Settings className="text-purple-500" />
                Voreinstellungen
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">
                  Voreinstellungen erlauben es, mehrere Bereiche (NAS, Webserver, Hausautomatisierung, Musikbox, Lerncomputer) in einem Schritt zu konfigurieren.
                </p>
                <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Funktionen</h3>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li>Auswahl eines Presets (z. B. „Medienserver“, „Entwicklung“) oder freie Auswahl der Module</li>
                  <li>Ein Klick startet die Konfiguration für alle ausgewählten Bereiche</li>
                  <li>Sudo-Passwort wird bei Bedarf abgefragt</li>
                </ul>
                <ScreenshotImg src="/docs/screenshots/screenshot-presets.png" alt="Voreinstellungen" title="Voreinstellungen – Presets und Module" />
                <div className="card-info">
                  <h4 className="text-sm font-semibold  mb-1">💡 Tipp</h4>
                  <p className="text-xs opacity-95">
                    Ideal, wenn du das System in einem Rutsch einrichten willst. Danach kannst du jeden Bereich einzeln unter der jeweiligen Menüseite nachjustieren.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'security' && (
            <motion.div key="security" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.15 }} className="rounded-xl bg-slate-800/60 border border-slate-600 p-6">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><Shield className="text-red-500" /> Sicherheit</h2>
              <div className="space-y-4 text-slate-300 text-sm">
                <p>Konfiguration von Firewall, Benutzer-Sicherheit und optional Sicherheits-Scans.</p>
                <h3 className="text-lg font-semibold text-white">Kapitel 1: Überblick</h3>
                <ScreenshotImg src="/docs/screenshots/screenshot-security.png" alt="Sicherheit" title="Sicherheit – Firewall und Konfiguration" />
                <h3 className="text-lg font-semibold text-white mt-4">Funktionen</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li><strong>Firewall:</strong> Regeln anzeigen, hinzufügen, löschen; Firewall aktivieren/deaktivieren (sudo erforderlich)</li>
                  <li><strong>Sicherheitskonfiguration:</strong> Anzeige und Anpassung sicherheitsrelevanter Einstellungen</li>
                  <li><strong>Installierte Pakete / Laufende Prozesse:</strong> Übersicht für Sicherheitsbewertung</li>
                  <li><strong>Sicherheits-Scan:</strong> Optionaler Scan (z. B. offene Ports, Dienste)</li>
                </ul>
                <h4 className="text-base font-semibold text-white mt-3">Ausschnitt: Firewall-Bereich</h4>
                <ScreenshotDetail src="/docs/screenshots/screenshot-security.png" alt="Firewall-Regeln" title="Firewall-Status und Regeln" position="50% 20%" height={180} />
                <div className="card-info">
                  <h4 className="text-sm font-semibold text-emerald-300 mb-1">💡 Tipp</h4>
                  <p className="text-xs">Beim ersten Aktivieren der Firewall wird das Sudo-Passwort abgefragt (Modal). „Ohne Prüfung speichern“ speichert es für die Session – danach funktionieren weitere sudo-Aktionen ohne erneute Eingabe.</p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'users' && (
            <motion.div key="users" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.15 }} className="rounded-xl bg-slate-800/60 border border-slate-600 p-6">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><Users className="text-sky-500" /> Benutzer</h2>
              <div className="space-y-4 text-slate-300 text-sm">
                <p>Benutzerkonten werden in zwei Bereiche getrennt: <strong>Systembenutzer/Dienste</strong> (UID &lt; 1000) und <strong>Benutzer (Personen)</strong> (UID ≥ 1000). Nur letztere können hier angelegt oder gelöscht werden.</p>
                <ScreenshotImg src="/docs/screenshots/screenshot-users.png" alt="Benutzer" title="Benutzer – Systembenutzer und Personen" />
                <h3 className="text-lg font-semibold text-white">Funktionen</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li><strong>Systembenutzer / Dienste:</strong> Nur Anzeige (z. B. root, www-data, _apt). UID &lt; 1000 – nicht löschen oder ändern.</li>
                  <li><strong>Benutzer (Personen):</strong> Anlegen (Name, E-Mail, Rolle, Passwort, optional SSH-Schlüssel), Löschen. UID ≥ 1000.</li>
                  <li><strong>Rollen:</strong> Administrator (sudo), Entwickler (Dev-Tools), Benutzer (normal), Gast (eingeschränkt). Weitere Rollen bei Bedarf manuell.</li>
                </ul>
                <h4 className="text-base font-semibold text-white mt-3">Ausschnitt: Benutzer anlegen</h4>
                <ScreenshotDetail src="/docs/screenshots/screenshot-users.png" alt="Benutzer anlegen" title="Formular zum Anlegen neuer Benutzer" position="50% 70%" height={180} />
                <div className="card-info">
                  <h4 className="text-sm font-semibold text-emerald-300 mb-1">💡 Tipp</h4>
                  <p className="text-xs">Vor dem Anlegen eines Benutzers Sudo-Passwort eingeben (wird bei Bedarf abgefragt). Rolle „Gast“ für eingeschränkte Zugriffe (z. B. nur Lesezugriff) nutzen.</p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'devenv' && (
            <motion.div key="devenv" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.15 }} className="rounded-xl bg-slate-800/60 border border-slate-600 p-6">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><Code className="text-emerald-500" /> Dev-Umgebung</h2>
              <div className="space-y-4 text-slate-300 text-sm">
                <p>Installation von Entwicklungsumgebungen und Sprachen (z. B. Python, Node, Rust, Tauri, C/C++, QT/QML).</p>
                <ScreenshotImg src="/docs/screenshots/screenshot-devenv.png" alt="Dev-Umgebung" title="Dev-Umgebung – Sprachen und Tools" />
                <h3 className="text-lg font-semibold text-white">Funktionen</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Status-Anzeige: welche Tools installiert sind</li>
                  <li>Auswahl der zu installierenden Komponenten und Start der Installation (sudo erforderlich)</li>
                </ul>
                <h4 className="text-base font-semibold text-white mt-3">Ausschnitt: Auswahl der Komponenten</h4>
                <ScreenshotDetail src="/docs/screenshots/screenshot-devenv.png" alt="Dev-Komponenten" title="Checkboxen für Python, Node, Rust, Tauri usw." position="50% 40%" height={160} />
                <div className="card-info">
                  <h4 className="text-sm font-semibold text-emerald-300 mb-1">💡 Tipp</h4>
                  <p className="text-xs">Für PI-Installer-Entwicklung: Rust und Tauri installieren, dann im frontend-Ordner <code className="bg-slate-700 px-1 rounded">npm run tauri:dev</code> ausführen.</p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'webserver' && (
            <motion.div key="webserver" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.15 }} className="rounded-xl bg-slate-800/60 border border-slate-600 p-6">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><Globe className="text-green-500" /> Webserver</h2>
              <div className="space-y-4 text-slate-300 text-sm">
                <p>Webserver (z. B. nginx, Apache) einrichten und konfigurieren.</p>
                <ScreenshotImg src="/docs/screenshots/screenshot-webserver.png" alt="Webserver" title="Webserver – Status und Konfiguration" />
                <h3 className="text-lg font-semibold text-white">Funktionen</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Status: ob Webserver installiert/läuft</li>
                  <li>Konfiguration speichern und ggf. Installation starten (sudo)</li>
                </ul>
                <div className="card-info">
                  <h4 className="text-sm font-semibold text-emerald-300 mb-1">💡 Tipp</h4>
                  <p className="text-xs">Nach der Konfiguration prüfen: Im Browser die IP des {systemLabel} und Port 80/443 aufrufen (falls Firewall Zugriff erlaubt).</p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'mailserver' && (
            <motion.div key="mailserver" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.15 }} className="rounded-xl bg-slate-800/60 border border-slate-600 p-6">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><Mail className="text-amber-500" /> Mailserver</h2>
              <div className="space-y-4 text-slate-300 text-sm">
                <p>E-Mail-Server konfigurieren (z. B. für lokale Mails oder Relay).</p>
                <ScreenshotImg src="/docs/screenshots/screenshot-mailserver.png" alt="Mailserver" title="Mailserver – Konfiguration" />
                <h3 className="text-lg font-semibold text-white">Funktionen</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Konfiguration eingeben und speichern</li>
                  <li>Für Installation/Änderung am System wird sudo benötigt</li>
                </ul>
                <div className="card-info">
                  <h4 className="text-sm font-semibold text-emerald-300 mb-1">💡 Tipp</h4>
                  <p className="text-xs">Domain und MX-Einträge beim Provider prüfen, bevor du den Mailserver produktiv nutzt.</p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'nas' && (
            <motion.div key="nas" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.15 }} className="rounded-xl bg-slate-800/60 border border-slate-600 p-6">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><HardDrive className="text-blue-500" /> NAS</h2>
              <div className="space-y-4 text-slate-300 text-sm">
                <p>Network Attached Storage einrichten – Freigaben und Speicher für das Netzwerk.</p>
                <ScreenshotImg src="/docs/screenshots/screenshot-nas.png" alt="NAS" title="NAS – Freigaben und Duplikate" />
                <h3 className="text-lg font-semibold text-white">Funktionen</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Status: ob NAS-Dienste (z. B. Samba) installiert/laufen</li>
                  <li>Konfiguration (Freigaben, Optionen) und Installation (sudo)</li>
                  <li><strong>Duplikate & Aufräumen:</strong> fdupes/jdupes installieren, Verzeichnis nach Duplikaten scannen, Duplikate in einen Backup-Ordner verschieben (statt zu löschen). Option: System-/Cache-Verzeichnisse (.cache, mesa_shader, __pycache__, node_modules, .git) ausschließen.</li>
                </ul>
                <h4 className="text-base font-semibold text-white mt-3">Ausschnitt: Duplikate & Aufräumen</h4>
                <ScreenshotDetail src="/docs/screenshots/screenshot-nas.png" alt="NAS Duplikate" title="Duplikat-Finder: Scan-Pfad, Backup-Ziel, Optionen" position="50% 75%" height={180} />
                <div className="card-info">
                  <h4 className="text-sm font-semibold text-emerald-300 mb-1">💡 Tipp</h4>
                  <p className="text-xs">Von anderen Rechnern im Netz: \\IP-des-Pi\Freigabe (Windows) bzw. smb://IP/Freigabe (Linux/macOS) nutzen.</p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'homeautomation' && (
            <motion.div key="homeautomation" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.15 }} className="rounded-xl bg-slate-800/60 border border-slate-600 p-6">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><Home className="text-orange-500" /> Hausautomatisierung</h2>
              <div className="space-y-4 text-slate-300 text-sm">
                <p>Systeme für Hausautomatisierung einrichten (z. B. Home Assistant, openHAB, FHEM).</p>
                <ScreenshotImg src="/docs/screenshots/screenshot-homeautomation.png" alt="Hausautomatisierung" title="Hausautomatisierung – Home Assistant, openHAB, FHEM" />
                <h3 className="text-lg font-semibold text-white">Funktionen</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Status und Konfiguration</li>
                  <li>Installation starten (sudo); je nach System werden Pakete oder Container eingerichtet</li>
                </ul>
                <div className="card-info">
                  <h4 className="text-sm font-semibold text-emerald-300 mb-1">💡 Tipp</h4>
                  <p className="text-xs">Vor der Auswahl: Dokumentation des gewünschten Systems prüfen (Ports, Hardware wie Zigbee-Stick).</p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'musicbox' && (
            <motion.div key="musicbox" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.15 }} className="rounded-xl bg-slate-800/60 border border-slate-600 p-6">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><Music className="text-purple-500" /> Musikbox</h2>
              <div className="space-y-4 text-slate-300 text-sm">
                <p>Music-Server einrichten: Mopidy, Volumio oder Plex Media Server. Zusätzliche Features: Internetradio, Streaming (Spotify Connect), AirPlay.</p>
                <h3 className="text-lg font-semibold text-white">Funktionen</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li><strong>Music Server:</strong> Mopidy (Port 6680), Volumio (3000), Plex (32400) – einer auswählen</li>
                  <li><strong>Zusätzliche Features:</strong> Internetradio (mopidy-internetarchive), Streaming-Dienste, AirPlay (Shairport-sync), Spotify Connect</li>
                  <li>Installation starten – bei Bedarf erscheint das Sudo-Passwort-Modal für Paketinstallation</li>
                </ul>
                <h3 className="text-lg font-semibold text-white mt-4">Ausgabequelle, Mixer & Dolby</h3>
                <ul className="list-disc list-inside space-y-1 ml-4 text-slate-300 text-sm">
                  <li><strong>Ausgabequelle wählen:</strong> Unter Linux steuert PulseAudio bzw. PipeWire die Wiedergabe. Ausgabegerät (Headset, Lautsprecher, HDMI) wählst du in den Systemeinstellungen (Sound) oder über <code className="bg-slate-700 px-1 rounded">pavucontrol</code> (Mixer).</li>
                  <li><strong>Headset / Notebook-Lautsprecher:</strong> Treiber liefert ALSA/PulseAudio; nach Installation der Musikbox das gewünschte Gerät in Sound-Einstellungen oder pavucontrol als Ausgabe wählen.</li>
                  <li><strong>Mixer:</strong> <code className="bg-slate-700 px-1 rounded">pavucontrol</code> (PulseAudio) oder <code className="bg-slate-700 px-1 rounded">qpwgraph</code> (PipeWire) für Kanäle und Lautstärke.</li>
                  <li><strong>Dolby Atmos:</strong> Unter Linux herstellerspezifisch (z. B. Dolby Access für bestimmte Geräte); oft über externe Software oder Hardware. Für Mehrkanal/Atmos die jeweilige Herstellerdokumentation prüfen.</li>
                </ul>
                <ScreenshotImg src="/docs/screenshots/screenshot-musicbox.png" alt="Musikbox – Auswahl Server und Zusatzfeatures" title="Musikbox – Auswahl Server und Zusatzfeatures" />
                <h4 className="text-base font-semibold text-white mt-3">Ausschnitt: Music-Server Auswahl</h4>
                <ScreenshotDetail src="/docs/screenshots/screenshot-musicbox.png" alt="Music-Server" title="Mopidy, Volumio, Plex – einer auswählen" position="50% 25%" height={160} />
                <div className="card-info">
                  <h4 className="text-sm font-semibold text-emerald-300 mb-1">💡 Tipp</h4>
                  <p className="text-xs">Wenn „Sudo-Passwort erforderlich“ erscheint: Modal öffnet sich – Passwort eingeben und „Installation starten“ bestätigen. Spotify/Tidal benötigen eigenes Konto/Abo. Ausgabequelle (Headset/Lautsprecher) in den System-Sound-Einstellungen oder mit pavucontrol wählen.</p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'kino-streaming' && (
            <motion.div key="kino-streaming" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.15 }} className="rounded-xl bg-slate-800/60 border border-slate-600 p-6">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><Film className="text-amber-500" /> Kino / Streaming</h2>
              <div className="space-y-4 text-slate-300 text-sm">
                <p>Video-Streaming-Dienste (Amazon Prime, Netflix, Disney+, Sky, Paramount+, ARD/ZDF), Player starten, Video- und Soundausgabe wählen.</p>
                <h3 className="text-lg font-semibold text-white">Funktionen</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li><strong>Video- & Soundausgabe:</strong> TV, Beamer, Monitor 1/2, Surround / DTS / Dolby Digital wählbar</li>
                  <li><strong>Streaming-Dienste:</strong> Links zu Prime Video, Netflix, Disney+, Sky, Paramount+, ARD/ZDF Mediathek – im Browser öffnen</li>
                  <li><strong>Zugangsdaten:</strong> Werden im jeweiligen Dienst bzw. in der App verwaltet; zentrale Speicherung aus Sicherheitsgründen nicht vorgesehen</li>
                  <li><strong>Surround/Dolby:</strong> Mehrkanal-Audio über System-Sound (PulseAudio/PipeWire) und Ausgabegerät (z. B. HDMI für AV-Receiver)</li>
                </ul>
                <ScreenshotImg src="/docs/screenshots/screenshot-kino-streaming.png" alt="Kino / Streaming" title="Kino / Streaming – Video und Soundausgabe" />
                <div className="card-hint">
                  <h4 className="text-sm font-semibold text-amber-300 mb-1">Kino/Video</h4>
                  <p className="text-xs">Bereich speziell auf Kino und Video-Streaming ausgerichtet – Dienste, Player, Ausgabeoptionen.</p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'learning' && (
            <motion.div key="learning" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.15 }} className="rounded-xl bg-slate-800/60 border border-slate-600 p-6">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><BookOpen className="text-sky-500" /> Lerncomputer</h2>
              <div className="space-y-4 text-slate-300 text-sm">
                <p>Umgebung für Lernsoftware und Bildung (z. B. Programme für Kinder/Schule) einrichten.</p>
                <ScreenshotImg src="/docs/screenshots/screenshot-learning.png" alt="Lerncomputer" title="Lerncomputer – Lernsoftware und Bildung" />
                <h3 className="text-lg font-semibold text-white">Funktionen</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li>Status und Konfiguration</li>
                  <li>Installation starten (sudo)</li>
                </ul>
                <div className="p-3 bg-sky-900/30 border border-sky-600/50 rounded-lg">
                  <h4 className="text-sm font-semibold text-sky-300 mb-1">Touchscreen am DSI0-Port nutzen</h4>
                  <p className="text-xs text-slate-300 mb-2">Displays wie das Freenove 4,3″ TFT werden am DSI-Port (intern) angeschlossen. Touch-Eingabe funktioniert unter Wayland automatisch mit libinput.</p>
                  <ul className="list-disc list-inside text-xs space-y-1 ml-4">
                    <li><strong>Rotation:</strong> <code className="bg-slate-700 px-1 rounded">scripts/freenove-dsi-rotate-portrait.sh</code> dreht nur das DSI-Display (Wayland)</li>
                    <li><strong>Test:</strong> <code className="bg-slate-700 px-1 rounded">libinput debug-events</code> zeigt Touch-Events</li>
                  </ul>
                </div>
                <div className="card-info">
                  <h4 className="text-sm font-semibold text-emerald-300 mb-1">💡 Tipp</h4>
                  <p className="text-xs">Nach der Installation die angebotenen Programme prüfen und ggf. kindersichere Einstellungen (Benutzer, Filter) setzen.</p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'monitoring' && (
            <motion.div key="monitoring" initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -8 }} transition={{ duration: 0.15 }} className="rounded-xl bg-slate-800/60 border border-slate-600 p-6">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2"><Activity className="text-green-500" /> Monitoring</h2>
              <div className="space-y-4 text-slate-300 text-sm">
                <p>Überwachung mit Node Exporter, Prometheus und optional Grafana. Metriken und Dashboards für CPU, Speicher, Disk.</p>
                <h3 className="text-lg font-semibold text-white">Funktionen</h3>
                <ul className="list-disc list-inside space-y-1 ml-4">
                  <li><strong>Auswahl:</strong> Node Exporter, Prometheus, Grafana einzeln per Checkbox auswählbar</li>
                  <li>Installation nur der gewählten Komponenten (sudo über SudoPasswordModal)</li>
                  <li>Live-Metriken (CPU, RAM, Disk, Temperatur) und Verlauf in der Oberfläche</li>
                </ul>
                <ScreenshotImg src="/docs/screenshots/screenshot-monitoring.png" alt="Monitoring – Auswahl und Metriken" title="Monitoring – Auswahl und Metriken" />
                <div className="card-info">
                  <h4 className="text-sm font-semibold text-emerald-300 mb-1">💡 Tipp</h4>
                  <p className="text-xs">Wenn das Sudo-Modal erscheint: Passwort eingeben und bestätigen. Grafana ist optional – für einfache Metriken reichen Node Exporter und Prometheus.</p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'backup-restore' && (
            <motion.div
              key="backup-restore"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <HardDrive className="text-blue-500" />
                Backup & Restore
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">Backup & Restore ermöglicht vollständige, inkrementelle oder Daten-Backups – lokal oder in die Cloud.</p>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Funktionen</h3>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li><strong>Backup erstellen:</strong> Vollständig (ganzes System), Inkrementell (nur Änderungen), Daten (z. B. /home, /var/www, /opt)</li>
                    <li><strong>Ziel:</strong> Lokales Verzeichnis oder USB-Stick; optional Cloud-Upload (Einstellungen → Cloud konfigurieren)</li>
                    <li><strong>Verschlüsselung:</strong> GPG (AES-256, Passphrase optional) oder OpenSSL (AES-256-CBC, Passphrase erforderlich)</li>
                    <li><strong>Backup-Jobs:</strong> Laufende Jobs anzeigen, abbrechen; Backups auflisten, verifizieren, löschen</li>
                    <li><strong>Wiederherstellung:</strong> Backup auswählen, Restore starten; verschlüsselte Backups werden entschlüsselt</li>
                    <li><strong>USB:</strong> USB-Stick als Ziel auswählen, vorbereiten (formatieren), mounten/ejecten</li>
                    <li><strong>Laufwerk klonen:</strong> System von SD-Karte auf NVMe/USB-SSD klonen (Hybrid-Boot: Boot auf SD, Root auf NVMe). NVMe, USB- und SATA-Laufwerke werden automatisch erkannt. Bei Problemen siehe FAQ.</li>
                  </ul>
                </div>
                <ScreenshotImg src="/docs/screenshots/screenshot-backup.png" alt="Backup & Restore" title="Backup & Restore – Ziel und Optionen" hint="Zeigt Auswahl Backup-Typ, Ziel, Verschlüsselung." />
                <h4 className="text-base font-semibold text-white mt-3">Ausschnitt: Backup-Typ und Ziel</h4>
                <ScreenshotDetail src="/docs/screenshots/screenshot-backup.png" alt="Backup-Optionen" title="Vollständig, Inkrementell, Daten – Ziel wählen" position="50% 30%" height={180} />
                <div className="card-info">
                  <h4 className="text-sm font-semibold  mb-1">💡 Tipp</h4>
                  <p className="text-xs opacity-95">
                    Erste Sicherung immer als <strong>Vollständig</strong>. Danach Inkrementell spart Platz und Zeit. Für Cloud: zuerst Einstellungen → Cloud-Backup Einstellungen ausfüllen und „Verbindung testen“.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'cloud' && (
            <motion.div
              key="cloud"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <Cloud className="text-sky-500" />
                Cloud-Einstellungen
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">Cloud-Backup wird unter Einstellungen konfiguriert. Hier die Übersicht.</p>
                <ScreenshotImg src="/docs/screenshots/screenshot-settings.png" alt="Cloud-Einstellungen" title="Einstellungen – Cloud-Tab" />
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Funktionen</h3>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li><strong>Cloud-Anbieter:</strong> Einstellungen → Cloud-Backup Einstellungen – Zugangsdaten und Verbindungsparameter (WebDAV, S3, Google, Azure)</li>
                    <li><strong>Verbindung testen:</strong> Nach dem Speichern „Verbindung testen“ ausführen, um Zugriff zu prüfen</li>
                    <li><strong>Quota:</strong> Anzeige verwendeter/verfügbarer Speicherplatz, prozentuale Auslastung (wird nach Speichern/Manuell aktualisiert)</li>
                  </ul>
                </div>
                <div className="card-info">
                  <h4 className="text-sm font-semibold  mb-1">💡 Tipp</h4>
                  <p className="text-xs opacity-95">
                    Zuerst Cloud-Einstellungen speichern und testen. Danach unter Backup & Restore beim Erstellen eines Backups „In Cloud hochladen“ wählen.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'control-center' && (
            <motion.div
              key="control-center"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <Settings className="text-purple-500" />
                Control Center
              </h2>
              <div className="space-y-4 opacity-95">
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">System-Einstellungen</h3>
                  <p className="text-sm mb-3">
                    Das Control Center bietet eine zentrale Verwaltung für alle System-Einstellungen des {' '}{systemLabel}.
                    Die Einstellungen sind in Bereiche unterteilt und über ein Menü erreichbar.
                  </p>
                  <div className="p-3 bg-slate-900/40 dark:bg-slate-900/40 border border-slate-700 dark:border-slate-700 rounded-lg">
                    <h4 className="text-sm font-semibold text-white dark:text-white mb-2">Verfügbare Bereiche</h4>
                    <ul className="list-disc list-inside text-xs space-y-1 ml-2">
                      <li><strong>WLAN:</strong> WiFi-Netzwerke hinzufügen und verwalten</li>
                      <li><strong>SSH:</strong> SSH-Zugriff aktivieren/deaktivieren</li>
                      <li><strong>VNC:</strong> VNC Remote-Desktop konfigurieren</li>
                      <li><strong>Tastatur:</strong> Tastatur-Layout und Varianten einstellen</li>
                      <li><strong>Lokalisierung:</strong> Sprache, Locale und Zeitzone konfigurieren</li>
                      <li><strong>Desktop:</strong> Boot-Ziel (Desktop vs. Kommandozeile) einstellen</li>
                      <li><strong>Display:</strong> Auflösung, Bildwiederholrate, Rotation (xrandr)</li>
                      <li><strong>Drucker:</strong> USB- und Netzwerkdrucker (CUPS) verwalten</li>
                      <li><strong>Scanner:</strong> USB- und Netzwerkscanner (SANE, eSCL/airscan) erkennen; SANE-Installationsstatus prüfen</li>
                      <li><strong>Performance:</strong> CPU-Governor (sofort wirksam), GPU-Memory, Overclocking, Swap-Größe (dphys-swapfile)</li>
                      <li><strong>Maus, Taskleiste, Theme:</strong> in Entwicklung</li>
                    </ul>
                  </div>
                </div>
                <ScreenshotImg src="/docs/screenshots/screenshot-control-center.png" alt="Control Center" title="Control Center – Menü mit WLAN, SSH, Display usw." />
                <div className="card-info">
                  <h4 className="text-sm font-semibold  mb-1">💡 Tipp</h4>
                  <p className="text-xs opacity-95">
                    WLAN: Netzwerk hinzufügen, dann bei Bedarf „Verbinden“ wählen. SSH/VNC: erst aktivieren, bei Bedarf „SSH starten“ bzw. „VNC starten“ nutzen. Display: Auflösung und Bildwiederholrate übernehmen – Änderung ist sofort sichtbar.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'periphery-scan' && (
            <motion.div
              key="periphery-scan"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <Scan className="text-emerald-500" />
                Peripherie-Scan (Assimilation)
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">
                  Der Peripherie-Scan erkennt Grafikkarten, Tastaturen, Mäuse, Headsets, Webcams und prüft, ob Treiber geladen sind.
                </p>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Funktionen</h3>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li><strong>Assimilation starten:</strong> Scan nach GPUs (lspci -k), USB-Geräten (lsusb), Eingabegeräten (/proc/bus/input/devices)</li>
                    <li><strong>Übersicht:</strong> Kamera(s), Tastatur („Welche:“ mit Name), Maus („Welche:“ mit Name), Grafik/Treiber (Grafikkartenname + Treiber-Status: installiert oder „Hersteller-Treiber prüfen“), Touchpad, Headset/Audio</li>
                    <li><strong>Grafikkarte:</strong> Es werden nur echte VGA/Display/3D-Controller angezeigt (keine Shader-Einheiten); pro GPU: Name und ob Kernel-/Hersteller-Treiber geladen ist</li>
                    <li><strong>Tastatur/Maus:</strong> Konkrete Bezeichnung (z. B. Logitech K380). Maus: Hinweis zu Belegung aller Tasten (xinput, imwheel, Hersteller-Software z. B. Logitech Options)</li>
                    <li><strong>Touchpad & Headset:</strong> Touchpad aus Eingabegeräten, Headset/Audio aus USB; Hinweise zu Ausgabequelle (Musikbox/Einstellungen)</li>
                    <li><strong>Gespeicherte Daten:</strong> Scan-Ergebnis bleibt beim Verlassen der Seite erhalten (localStorage). Beim erneuten Scan: Sektion „Neu bei diesem Scan“ zeigt nur neu hinzugekommene Komponenten</li>
                    <li><strong>Hersteller:</strong> Hersteller prüfen, ob Treiber für erkannte Komponenten existieren; Herstellerlisten/Anbieter identifizieren (Corsair, ASUS, Angetube, Logitech, NVIDIA, AMD …)</li>
                    <li><strong>Sonstige Treiber:</strong> Eigene Anzeige (PCI/Kernel-Module), getrennt von Grafik; Kameras nur bei Kameras, Maus nur bei Maus (inkl. Touchpad); Eingabegeräte einzeln mit Namen</li>
                    <li><strong>Ergebnis:</strong> Konsole; Karten GPUs, Kamera(s), Maus/Touchpad, Eingabegeräte (einzeln), weitere USB-Geräte, Sonstige Treiber</li>
                    <li><strong>Zum Dashboard:</strong> Button springt ins Dashboard – dort siehst du die gefundenen Komponenten in den Karten „CPU & Grafik“ und „Systembezogene Treiber“</li>
                  </ul>
                </div>
                <div className="p-3 bg-sky-900/20 border border-sky-700/40 rounded-lg">
                  <h4 className="text-sm font-semibold text-sky-300 dark:text-sky-300 mb-1">Hersteller-Treiber</h4>
                  <p className="text-xs opacity-95">
                    Die angezeigte Herstellerliste wird aus der erkannten Hardware (GPUs, PCI-Geräte) abgeleitet. Wenn passende Hersteller erkannt wurden, werden deren Links hervorgehoben; sonst siehst du eine Auswahl gängiger Hersteller mit Linux-Treiber-Seiten.
                  </p>
                </div>
                <ScreenshotImg src="/docs/screenshots/screenshot-periphery-scan.png" alt="Peripherie-Scan" title="Peripherie-Scan – Konsole nach Assimilation" hint="Zeigt animierte Konsolenausgabe und Treiber-Liste." />
                <div className="card-info">
                  <h4 className="text-sm font-semibold  mb-1">💡 Tipp</h4>
                  <p className="text-xs opacity-95">
                    Wenn „Endpoint nicht gefunden“ oder „Backend neu starten“ erscheint: Backend mit <code className="bg-slate-700 px-1 rounded">./start-backend.sh</code> aus dem Projektordner starten (alter Backend-Prozess ggf. beenden). Danach erneut „Assimilation starten“. Nutze die Hersteller-Links, um offizielle Linux-Treiber zu installieren und alle Hardware-Features zu nutzen.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'raspberry-pi-config' && (
            <motion.div
              key="raspberry-pi-config"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <Cpu className="text-purple-500" />
                Raspberry Pi Konfiguration
              </h2>
              <div className="space-y-4 opacity-95">
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Hardware-Einstellungen</h3>
                  <p className="text-sm mb-2">
                    Ändere Hardware-Einstellungen deines Raspberry Pi direkt über die Weboberfläche.
                    Alle Änderungen werden in der config.txt gespeichert.
                  </p>
                  <p className="text-sm mb-3">
                    Die Einstellungen sind nach Bereichen gruppiert und werden automatisch nach dem aktuellen Raspberry Pi Modell gefiltert.
                  </p>
                  <div className="p-3 bg-slate-900/40 dark:bg-slate-900/40 border border-slate-700 dark:border-slate-700 rounded-lg">
                    <h4 className="text-sm font-semibold text-white dark:text-white mb-2">Verfügbare Bereiche</h4>
                    <ul className="list-disc list-inside text-xs space-y-1 ml-2">
                      <li><strong>GPU & Video:</strong> GPU-Speicher, Video-Treiber</li>
                      <li><strong>Overclocking & Performance:</strong> CPU-Frequenz, Spannungserhöhung</li>
                      <li><strong>HDMI:</strong> HDMI-Gruppe, Modus, Hotplug</li>
                      <li><strong>Display & Framebuffer:</strong> Bildschirmrotation, Framebuffer</li>
                      <li><strong>GPIO & Schnittstellen:</strong> I2C, SPI, I2S, UART</li>
                      <li><strong>Kamera:</strong> Kamera-Aktivierung, LED-Steuerung</li>
                      <li><strong>WiFi & Bluetooth:</strong> Drahtlose Schnittstellen</li>
                    </ul>
                  </div>
                  <p className="text-sm mt-3">Für jede Einstellung gibt es eine Info-Schaltfläche mit Erklärungen und Quellenangaben.</p>
                  <div className="mt-3 p-3 bg-blue-900/20 dark:bg-blue-900/20 border border-blue-700/40 dark:border-blue-700/40 rounded-lg">
                    <h4 className="text-sm font-semibold text-blue-300 dark:text-blue-300 mb-1">Modell-Erkennung</h4>
                    <p className="text-xs opacity-95">
                      Das System erkennt automatisch dein Raspberry Pi Modell und zeigt nur kompatible Einstellungen an.
                    </p>
                  </div>
                </div>
                <ScreenshotImg src="/docs/screenshots/screenshot-raspberry-pi-config.png" alt="Raspberry Pi Config" title="Raspberry Pi Config – Optionen und config.txt" />
                <div className="card-info">
                  <h4 className="text-sm font-semibold  mb-1">💡 Tipp</h4>
                  <p className="text-xs opacity-95">
                    Änderungen an Overclocking oder GPU-Speicher erfordern einen Neustart. Nutze die Info-Buttons bei jeder Option für Erklärungen. Speicheraufteilung und over_voltage: Details siehe Dashboard → CPU & Grafik.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'desktop-app' && (
            <motion.div
              key="desktop-app"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <Monitor className="text-emerald-500" />
                Desktop-App (Tauri)
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">
                  Die PI-Installer-Oberfläche kann als <strong>eigenständige Desktop-Anwendung</strong> laufen –
                  ohne Browserfenster. Dafür wird <strong>Tauri 2</strong> verwendet (WebView-basiert, ressourcenschonend).
                </p>
                <ScreenshotImg src="/docs/screenshots/screenshot-documentation.png" alt="Desktop-App" title="PI-Installer als Desktop-Anwendung (Tauri)" />
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Vorteile</h3>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li>Kein separates Browser-Fenster, eigenes Anwendungsfenster</li>
                    <li>Typischerweise schnellerer Start und geringerer Speicherbedarf als im Browser</li>
                    <li>Gleiches React-UI wie in der Web-Version</li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Voraussetzungen</h3>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li><strong>Rust</strong> (z. B. via <code className="text-slate-400">curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh</code>)</li>
                    <li>Node.js und <code className="text-slate-400">npm install</code> im <code className="text-slate-400">frontend</code>-Ordner</li>
                    <li>Backend läuft (z. B. <code className="text-slate-400">./start.sh</code> oder nur Backend auf Port 8000)</li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Entwicklung & Build</h3>
                  <p className="text-sm mb-2">Im Projektroot bzw. <code className="text-slate-400">frontend</code>:</p>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li><strong>Entwicklung:</strong> <code className="text-slate-400">npm run tauri:dev</code> – startet Vite auf 5173 und öffnet die Desktop-App</li>
                    <li><strong>Produktions-Build:</strong> <code className="text-slate-400">npm run tauri:build</code> – erzeugt ausführbare Dateien im <code className="text-slate-400">src-tauri/target/release</code>-Bereich</li>
                  </ul>
                  <p className="text-sm mt-3">
                    Die App spricht standardmäßig mit dem Backend unter <code className="text-slate-400">http://localhost:8000</code>.
                    Bei Remote-Pi (Backend auf anderem Rechner) kann <code className="text-slate-400">VITE_API_BASE</code> beim Build gesetzt werden
                    (z. B. <code className="text-slate-400">VITE_API_BASE=http://192.168.1.10:8000 npm run build</code> vor <code className="text-slate-400">tauri build</code>).
                  </p>
                </div>
                <div className="card-info">
                  <h4 className="text-sm font-semibold  mb-1">💡 Tipp</h4>
                  <p className="text-xs opacity-95">
                    Backend muss laufen (z. B. <code className="bg-slate-700 px-1 rounded">./start-backend.sh</code> auf dem Pi). Dann <code className="bg-slate-700 px-1 rounded">npm run tauri:dev</code> im frontend-Ordner – die Desktop-App öffnet sich und nutzt das Backend unter localhost:8000 (bzw. die gesetzte API-Basis-URL).
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'freenove-case' && (
            <motion.div
              key="freenove-case"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <Package className="text-emerald-500" />
                Freenove Pro – 4,3″ Touchscreen im Gehäuse
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">Das <strong>Freenove Computer Case Kit Pro</strong> für Raspberry Pi 5 bietet ein 4,3″ TFT-Touchscreen-Display am DSI-Port sowie SSD-Slots und eine Erweiterungsplatine.</p>
                <h3 className="text-lg font-semibold text-white">Zusammenbau – Erfahrungen &amp; Hinweise</h3>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li><strong>Abstandshalter:</strong> Nicht zu fest anziehen – Gewinde kann abbrechen, dann bleibt alles dunkel</li>
                  <li><strong>Flachbandkabel (FPC):</strong> Kontaktseite vs. Isolationsseite (schwarz). Pi 5 PCIe: Kontakte zum aktiven Cooler. Audio-Video-Board PCIe IN: Kontakte nach unten. Bei verdrehtem Kabel bleibt alles dunkel → NVMe-Board ausbauen, FPC korrekt einstecken</li>
                  <li><strong>2-/3-/4-adrige Kabel:</strong> Glatte Rückseite, ausgewölbte Kontakte vorne. Wenn ein 4-adriges nicht passt – das andere probieren</li>
                </ul>
                <h3 className="text-lg font-semibold text-white">Software &amp; Tips &amp; Tricks</h3>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li><strong>Freenove-Software:</strong> Installation von GitHub, mögliche Probleme → siehe <strong>FAQ</strong></li>
                  <li><strong>Python vs. python3:</strong> Reparatur-Skript <code className="bg-slate-700 px-1 rounded">scripts/fix-freenove-computer-case.sh</code></li>
                  <li><strong>Display-Rotation:</strong> <code className="bg-slate-700 px-1 rounded">scripts/freenove-set-display-rotate.sh</code> oder <code className="bg-slate-700 px-1 rounded">scripts/freenove-dsi-rotate-portrait.sh</code> (Wayland)</li>
                  <li><strong>I2C:</strong> Benutzer in Gruppe <code className="bg-slate-700 px-1 rounded">i2c</code> aufnehmen, App ohne sudo starten</li>
                </ul>
                <div className="p-3 bg-sky-900/30 border border-sky-600/50 rounded-lg">
                  <p className="text-sm font-semibold text-sky-300 mb-1">Boot: SD + NVMe oder nur NVMe</p>
                  <p className="text-xs text-slate-300">Hybrid (Boot von SD, Root von NVMe): siehe <code className="bg-slate-700 px-1 rounded">docs/PATHS_NVME.md</code>. Boot nur von NVMe – noch zu ergänzen.</p>
                </div>
                <div className="p-3 bg-amber-900/20 border border-amber-700/40 rounded-lg">
                  <p className="text-sm font-semibold text-amber-300 mb-1">DSI-Radio: Anzeige und Ton</p>
                  <p className="text-xs text-slate-300">Läuft das DSI-Radio auf <strong>HDMI-1-2 / HDMI-A-2</strong>, geht der Sound über HDMI (Monitor). Startest du es auf <strong>DSI-1</strong> (Gehäuse-Display), läuft der Ton über die Gehäuselautsprecher – und nur dann ist in der Mixer-Anzeige der richtige interne HDMI-Sink sichtbar.</p>
                </div>
                <p className="text-sm">Ausführliche Doku: <code className="bg-slate-700 px-1 rounded">docs/FREENOVE_COMPUTER_CASE.md</code> · Skripte in <code className="bg-slate-700 px-1 rounded">scripts/</code></p>
              </div>
            </motion.div>
          )}

          {activeChapter === 'dualdisplay' && (
            <motion.div
              key="dualdisplay"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <LayoutGrid className="text-blue-400" />
                Dualdisplay DSI0 + HDMI1 – Zwei Monitore gleichzeitig
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">Gleichzeitige Ausgabe auf <strong>DSI</strong> (internes Display, z. B. Freenove 4,3″) und <strong>HDMI</strong> (externer Monitor). Voraussetzung: Wayland (Pix/Wayfire), Raspberry Pi 5.</p>
                <h3 className="text-lg font-semibold text-white">Erkannte Probleme</h3>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li><strong>HDMI bleibt aus:</strong> Wayfire priorisiert oft nur DSI; HDMI per <code className="bg-slate-700 px-1 rounded">wlr-randr --output HDMI-A-2 --on</code> nach Session-Start einschalten</li>
                  <li><strong>display_rotate betrifft alle:</strong> Unter Wayland dreht config.txt alle Ausgaben; nur DSI drehen: <code className="bg-slate-700 px-1 rounded">scripts/freenove-dsi-rotate-portrait.sh</code></li>
                </ul>
                <h3 className="text-lg font-semibold text-white">Tips & Tricks</h3>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li>Skript <code className="bg-slate-700 px-1 rounded">scripts/setup-pi5-dual-display-dsi-hdmi0.sh</code> (mit sudo) konfiguriert config.txt, cmdline.txt und Wayfire automatisch</li>
                  <li>HDMI1 (Port 2) oft stabiler als HDMI0 bei DSI+HDMI</li>
                </ul>
                <div className="p-3 bg-amber-900/20 border border-amber-700/40 rounded-lg">
                  <p className="text-sm font-semibold text-amber-300 mb-1">Zusammenbau-Probleme?</p>
                  <p className="text-xs text-slate-300">Gab es beim Anschluss von DSI und HDMI Probleme? Schreib uns, welche Fehler auftraten – wir ergänzen die Troubleshooting-FAQ.</p>
                </div>
                <p className="text-sm">Details: <code className="bg-slate-700 px-1 rounded">scripts/fix-gabriel-dual-display-wayland.sh</code>, <code className="bg-slate-700 px-1 rounded">docs/FREENOVE_COMPUTER_CASE.md</code></p>
              </div>
            </motion.div>
          )}

          {activeChapter === 'radio-app' && (
            <motion.div
              key="radio-app"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <Radio className="text-emerald-500" />
                Radio-App (DSI Radio)
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">Eigener Bereich für die <strong>PI-Installer DSI Radio</strong>-Standalone-App: Internetradio auf dem Freenove 4,3″ DSI-Display mit Favoriten, Senderliste und Klavierlack-Design.</p>
                <h3 className="text-lg font-semibold text-white">Versionen</h3>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li><strong>1.x:</strong> Wiedergabe über VLC, mpv oder mpg123 (externe Player)</li>
                  <li><strong>2.0:</strong> GStreamer-Wiedergabe (playbin), weniger Ressourcen, Metadaten aus dem Stream</li>
                </ul>
                <h3 className="text-lg font-semibold text-white">Voraussetzungen</h3>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li>Python 3.9+, PyQt6</li>
                  <li>GStreamer 1.0: <code className="bg-slate-700 px-1 rounded">python3-gi</code>, <code className="bg-slate-700 px-1 rounded">gstreamer1.0-plugins-good</code>, <code className="bg-slate-700 px-1 rounded">gstreamer1.0-pulseaudio</code></li>
                  <li>Optional: PI-Installer-Backend für Metadaten und Radio-Browser-API</li>
                </ul>
                <h3 className="text-lg font-semibold text-white">Start</h3>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li>Skript: <code className="bg-slate-700 px-1 rounded">./scripts/start-dsi-radio.sh</code></li>
                  <li>Direkt: <code className="bg-slate-700 px-1 rounded">python3 apps/dsi_radio/dsi_radio.py</code></li>
                  <li>Wayfire: Fenstertitel „PI-Installer DSI Radio“ → Fensterregel für DSI-1</li>
                </ul>
                <h3 className="text-lg font-semibold text-white">Konfiguration</h3>
                <p className="text-sm">Verzeichnis: <code className="bg-slate-700 px-1 rounded">~/.config/pi-installer-dsi-radio/</code> (Favoriten, Theme, Logs).</p>
                <p className="text-sm">Ausführliche Doku: <code className="bg-slate-700 px-1 rounded">docs/DSI_RADIO_APP.md</code></p>
              </div>
            </motion.div>
          )}

          {activeChapter === 'picture-frame-app' && (
            <motion.div
              key="picture-frame-app"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <Image className="text-amber-500" />
                Bilderrahmen
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">Standalone-App für das <strong>Picture</strong>-Verzeichnis: Bilder-Slideshow mit Datumsanzeige, themenbezogenem Text und animierten Symbolen (Weihnachten, Ostern, Geburtstag, Valentinstag, Hochzeitstag).</p>
                <h3 className="text-lg font-semibold text-white">Funktionen</h3>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li>Verzeichnisauswahl: <code className="bg-slate-700 px-1 rounded">~/Pictures</code> oder Unterordner</li>
                  <li>Datums- und optionale Uhrzeitanzeige</li>
                  <li>Einstellungen: Thema, eigener Text, Wechselintervall, Symbolgröße</li>
                  <li>Symbole fliegen durchs Bild oder fallen wie Regen (themenabhängig)</li>
                  <li>Vollbild: F11</li>
                </ul>
                <h3 className="text-lg font-semibold text-white">Start</h3>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li>Skript: <code className="bg-slate-700 px-1 rounded">./scripts/start-picture-frame.sh</code></li>
                  <li>Musterbilder anlegen: <code className="bg-slate-700 px-1 rounded">./scripts/setup-picture-frame-samples.sh</code></li>
                </ul>
                <p className="text-sm">Konfiguration: <code className="bg-slate-700 px-1 rounded">~/.config/pi-installer-picture-frame/</code>. Ausführlich: <code className="bg-slate-700 px-1 rounded">docs/PICTURE_FRAME_APP.md</code></p>
              </div>
            </motion.div>
          )}

          {activeChapter === 'troubleshooting' && (
            <motion.div
              key="troubleshooting"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <HelpCircle className="text-amber-500" />
                FAQ – Häufige Fragen &amp; Lösungen
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">Aus den Troubleshooting-Seiten zusammengestellte FAQ. Jeder Eintrag: Fehlername, Beschreibung, Lösungen. Logs: Einstellungen → Logs.</p>
                <div className="space-y-3">
                  {/* FAQ: Mixer */}
                  <div className="rounded-lg border border-amber-600/50 bg-amber-950/30 overflow-hidden">
                    <div className="px-4 py-2 bg-amber-900/40 border-b border-amber-600/50">
                      <h4 className="font-semibold text-amber-200">Mixer-Installation fehlgeschlagen</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> „Mixer-Programme installieren“ (pavucontrol &amp; qpwgraph) in Musikbox/Kino schlägt fehl.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li>Sudo-Passwort eingeben (Modal erscheint)</li>
                          <li>Manuell: <code className="bg-slate-700 px-1 rounded">sudo apt update && sudo apt install -y pavucontrol qpwgraph</code></li>
                          <li>Backend setzt <code className="bg-slate-700 px-1 rounded">DISPLAY=:0</code> für GUI-Start</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: Pi 5 HDMI Audio */}
                  <div className="rounded-lg border border-amber-600/50 bg-amber-950/30 overflow-hidden">
                    <div className="px-4 py-2 bg-amber-900/40 border-b border-amber-600/50">
                      <h4 className="font-semibold text-amber-200">Raspberry Pi 5: Kein Ton über HDMI</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> <code className="bg-slate-700 px-1 rounded">cat /proc/asound/cards</code> → „no soundcards“; PipeWire nur „Dummy Output“.</p>
                      <p className="text-slate-300 mb-2"><strong>Ursache:</strong> Fehlender Overlay <code className="bg-slate-700 px-1 rounded">vc4-kms-v3d-pi5</code>.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ol className="list-decimal list-inside text-slate-300 space-y-1">
                          <li><code className="bg-slate-700 px-1 rounded">sudo apt update && sudo apt full-upgrade -y</code>, Neustart</li>
                          <li>In <code className="bg-slate-700 px-1 rounded">/boot/firmware/config.txt</code> Zeile <code className="bg-slate-700 px-1 rounded">dtoverlay=vc4-kms-v3d-pi5</code> ergänzen</li>
                          <li><code className="bg-slate-700 px-1 rounded">dtparam=audio=on</code> muss gesetzt sein</li>
                          <li><code className="bg-slate-700 px-1 rounded">sudo reboot</code></li>
                        </ol>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: Backend/Frontend */}
                  <div className="rounded-lg border border-sky-600/50 bg-sky-950/20 overflow-hidden">
                    <div className="px-4 py-2 bg-sky-900/40 border-b border-sky-600/50">
                      <h4 className="font-semibold text-sky-200">Backend &amp; Frontend starten</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Wie starte ich PI-Installer korrekt?</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li>Alles: <code className="bg-slate-700 px-1 rounded">./start.sh</code></li>
                          <li>Nur Backend: <code className="bg-slate-700 px-1 rounded">./start-backend.sh</code></li>
                          <li>Frontend: <code className="bg-slate-700 px-1 rounded">./start-frontend.sh</code> oder <code className="bg-slate-700 px-1 rounded">cd frontend && npm run dev</code></li>
                          <li>Desktop-App: <code className="bg-slate-700 px-1 rounded">cd frontend && npm run tauri:dev</code> (Backend separat)</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: Dashboard/Backend */}
                  <div className="rounded-lg border border-amber-600/50 bg-amber-950/30 overflow-hidden">
                    <div className="px-4 py-2 bg-amber-900/40 border-b border-amber-600/50">
                      <h4 className="font-semibold text-amber-200">Dashboard zeigt keine Daten / Sudo speichert nicht</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Beides benötigt erreichbares Backend (Port 8000).</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li>Backend starten: <code className="bg-slate-700 px-1 rounded">./scripts/install-backend-service.sh</code> (Service beim Boot) oder <code className="bg-slate-700 px-1 rounded">./start-backend.sh</code></li>
                          <li>Bei Vite-Proxy: API-Anfragen gehen an localhost:8000</li>
                          <li>Sudo: „Ohne Prüfung speichern“ – nur Session, nicht dauerhaft</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: Scanner */}
                  <div className="rounded-lg border border-amber-600/50 bg-amber-950/30 overflow-hidden">
                    <div className="px-4 py-2 bg-amber-900/40 border-b border-amber-600/50">
                      <h4 className="font-semibold text-amber-200">Scanner werden nicht erkannt</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> SANE findet keine Geräte.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li><code className="bg-slate-700 px-1 rounded">sudo apt install sane sane-utils</code></li>
                          <li>Netzwerk: <code className="bg-slate-700 px-1 rounded">sudo apt install sane-airscan</code></li>
                          <li>Test: <code className="bg-slate-700 px-1 rounded">scanimage -L</code> (Netzwerk bis 45s)</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: NVMe/Klonen */}
                  <div className="rounded-lg border border-sky-600/50 bg-sky-950/20 overflow-hidden">
                    <div className="px-4 py-2 bg-sky-900/40 border-b border-sky-600/50">
                      <h4 className="font-semibold text-sky-200">NVMe nach Klonen – Boot/Pfade</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Nach Clone auf NVMe: Root auf NVMe, Boot bleibt auf SD. Pfade siehe <code className="bg-slate-700 px-1 rounded">docs/PATHS_NVME.md</code>.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li><code className="bg-slate-700 px-1 rounded">lsblk</code> prüfen – Root sollte /dev/nvme0n1p1 sein</li>
                          <li>Bei Problemen: cmdline.txt zurücksetzen (Root wieder auf SD)</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: Freenove-Software Installation */}
                  <div className="rounded-lg border border-sky-600/50 bg-sky-950/20 overflow-hidden">
                    <div className="px-4 py-2 bg-sky-900/40 border-b border-sky-600/50">
                      <h4 className="font-semibold text-sky-200">Freenove-Software – Installation von GitHub</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Freenove Case Kit Pro – Software aus GitHub klonen und starten. App startet nicht oder crasht.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li><code className="bg-slate-700 px-1 rounded">git clone https://github.com/Freenove/Freenove_Computer_Case_Kit_Pro_for_Raspberry_Pi.git</code></li>
                          <li><code className="bg-slate-700 px-1 rounded">scripts/fix-freenove-computer-case.sh</code> – python3, Pfade, keine sudo</li>
                          <li><code className="bg-slate-700 px-1 rounded">sudo apt install python3-pyqt5 python3-smbus</code></li>
                          <li>Benutzer in Gruppe <code className="bg-slate-700 px-1 rounded">i2c</code> → Doku: <code className="bg-slate-700 px-1 rounded">docs/FREENOVE_COMPUTER_CASE.md</code></li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: DSI-Radio Lautstärke */}
                  <div className="rounded-lg border border-sky-600/50 bg-sky-950/20 overflow-hidden">
                    <div className="px-4 py-2 bg-sky-900/40 border-b border-sky-600/50">
                      <h4 className="font-semibold text-sky-200">DSI-Radio (Freenove): Lautstärkeregler funktioniert nicht</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Der Lautstärkeschieber in der nativen DSI-Radio-App ändert die Lautstärke nicht.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li>Ausgabegerät prüfen: Einstellungen → Sound → Ausgabegerät auf Gehäuse-Lautsprecher (Freenove) stellen</li>
                          <li>Mit PulseAudio: <code className="bg-slate-700 px-1 rounded">pactl set-sink-volume @DEFAULT_SINK@ 80%</code> testen</li>
                          <li>Ohne PulseAudio (ALSA): <code className="bg-slate-700 px-1 rounded">amixer set Master 80%</code> bzw. <code className="bg-slate-700 px-1 rounded">amixer -c 0 set PCM 80%</code></li>
                          <li>Doku: <code className="bg-slate-700 px-1 rounded">docs/FREENOVE_TFT_DISPLAY.md</code></li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: DSI-Radio – Sound HDMI vs. Gehäuselautsprecher / Mixer */}
                  <div className="rounded-lg border border-sky-600/50 bg-sky-950/20 overflow-hidden">
                    <div className="px-4 py-2 bg-sky-900/40 border-b border-sky-600/50">
                      <h4 className="font-semibold text-sky-200">DSI-Radio: Sound über HDMI vs. Gehäuselautsprecher / Mixer-Anzeige</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Je nachdem, auf welchem Display das DSI-Radio läuft, wechselt die Tonausgabe.</p>
                      <div className="rounded bg-sky-950/30 border border-sky-700/40 p-3 mt-2">
                        <p className="font-semibold text-sky-300 mb-1">Verhalten:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li><strong>DSI-Radio auf HDMI-1-2 / HDMI-A-2:</strong> Der Sound läuft über HDMI (Monitor).</li>
                          <li><strong>DSI-Radio auf DSI-1 (Gehäuse-Display):</strong> Der Sound läuft über die Gehäuselautsprecher – und nur dann erscheint in der Mixer-Anzeige (pavucontrol/qpwgraph) der richtige interne HDMI-Sink für die Gehäuselautsprecher.</li>
                        </ul>
                      </div>
                      <p className="text-slate-400 text-xs mt-2">Doku: <code className="bg-slate-700 px-1 rounded">docs/FREENOVE_TFT_DISPLAY.md</code></p>
                    </div>
                  </div>
                  {/* FAQ: NDR 1 / NDR 2 – Kein Ton */}
                  <div className="rounded-lg border border-sky-600/50 bg-sky-950/20 overflow-hidden">
                    <div className="px-4 py-2 bg-sky-900/40 border-b border-sky-600/50">
                      <h4 className="font-semibold text-sky-200">NDR 1 / NDR 2: Kein Ton (1Live spielt dagegen)</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Bei NDR 1 oder NDR 2 kommt kein Ton, bei anderen Sendern (z. B. 1Live) schon.</p>
                      <p className="text-slate-300 mb-2"><strong>Ursache:</strong> Die Sendersuche/API liefert oft Stream-URLs von addradio.de, die bei manchen Setups nicht zuverlässig abspielen. Die getesteten icecast.ndr.de-URLs funktionieren.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösung (ab Version 1.3.4.2 / DSI Radio v2.1):</p>
                        <p className="text-slate-300 mb-2">Die App bevorzugt automatisch die Stream-URLs aus der Senderliste (stations.py). NDR 1 und NDR 2 werden dann über icecast.ndr.de abgespielt – Ton und Metadaten sollten funktionieren. Einfach DSI Radio neu starten und NDR 1 bzw. NDR 2 erneut wählen.</p>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: Radio SAW – Kein Titel/Interpret */}
                  <div className="rounded-lg border border-sky-600/50 bg-sky-950/20 overflow-hidden">
                    <div className="px-4 py-2 bg-sky-900/40 border-b border-sky-600/50">
                      <h4 className="font-semibold text-sky-200">Radio SAW / SAW Musikwelt: Kein Titel oder Interpret angezeigt</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Bei allen Radio-SAW-Sendern (Hauptprogramm, 70er, 80er, Party, Rockland usw.) erscheinen keine Titel- oder Interpret-Infos, nur „Live“.</p>
                      <p className="text-slate-300 mb-2"><strong>Ursache:</strong> Die Stream-URLs leiten auf streamABC (vmg.streamabc.net) weiter. Dessen Server liefert keine ICY-Metadaten (kein <code className="bg-slate-700 px-1 rounded">icy-metaint</code>), daher kann die App keine Titel-Daten aus dem Stream lesen.</p>
                      <div className="rounded bg-sky-950/30 border border-sky-700/40 p-3 mt-2">
                        <p className="font-semibold text-sky-300 mb-1">Verhalten der App:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li>Es wird „Live“ bzw. der Sendername angezeigt.</li>
                          <li>Hinweis: „Titel/Interpret für diesen Sender derzeit nicht verfügbar.“ – das ist korrekt und kein Fehler.</li>
                        </ul>
                      </div>
                      <p className="text-slate-400 text-xs mt-2">Doku: <code className="bg-slate-700 px-1 rounded">docs/RADIO_SAW_MUSIKWELT_METADATA.md</code></p>
                    </div>
                  </div>
                  {/* FAQ: Radio-App Metadaten aus System */}
                  <div className="rounded-lg border border-sky-600/50 bg-sky-950/20 overflow-hidden">
                    <div className="px-4 py-2 bg-sky-900/40 border-b border-sky-600/50">
                      <h4 className="font-semibold text-sky-200">Radio-App: Titel/Interpret werden nicht angezeigt, aber der Lautstärkeregler zeigt sie</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Der System-Lautstärkeregler zeigt Titel und Interpret an, aber die Radio-App zeigt sie nicht.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösung:</p>
                        <p className="text-slate-300 mb-2">Ab Version 1.3.4.1 liest die Radio-App Metadaten auch direkt aus PulseAudio/PipeWire (dieselbe Quelle wie der Lautstärkeregler). Die App sollte jetzt automatisch Titel/Interpret anzeigen, auch wenn Backend/GStreamer keine Metadaten liefern.</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li>Die App nutzt einen Fallback: Wenn keine Metadaten von Backend/GStreamer kommen, werden sie aus dem Sound-System gelesen</li>
                          <li>"Es läuft:" bleibt immer sichtbar (auch ohne Sendungsname)</li>
                          <li>Sendungsnamen wie "Die Show" oder "1LIVE Liebesalarm" werden automatisch erkannt und erscheinen hinter "Es läuft:", nicht als Titel/Interpret</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: Dualdisplay/Freenove */}
                  <div className="rounded-lg border border-sky-600/50 bg-sky-950/20 overflow-hidden">
                    <div className="px-4 py-2 bg-sky-900/40 border-b border-sky-600/50">
                      <h4 className="font-semibold text-sky-200">Dualdisplay / Freenove – HDMI bleibt aus, Display falsch</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Wayfire nutzt oft nur DSI; HDMI oder Rotation falsch.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li>HDMI: <code className="bg-slate-700 px-1 rounded">scripts/setup-pi5-dual-display-dsi-hdmi0.sh</code></li>
                          <li>DSI-Rotation (nur DSI): <code className="bg-slate-700 px-1 rounded">scripts/freenove-dsi-rotate-portrait.sh</code></li>
                          <li>Freenove-Software: <code className="bg-slate-700 px-1 rounded">scripts/fix-freenove-computer-case.sh</code></li>
                          <li>Doku: <code className="bg-slate-700 px-1 rounded">docs/FREENOVE_COMPUTER_CASE.md</code></li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: DSI-Spiegelung auf HDMI (X11) */}
                  <div className="rounded-lg border border-amber-600/50 bg-amber-950/30 overflow-hidden">
                    <div className="px-4 py-2 bg-amber-900/40 border-b border-amber-600/50">
                      <h4 className="font-semibold text-amber-200">DSI-Desktop oben links auf HDMI gespiegelt (X11)</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Der komplette DSI-1-Desktop erscheint oben links auf dem HDMI-Bildschirm (gespiegelt). Nur unter X11 mit DSI + HDMI.</p>
                      <p className="text-slate-300 mb-2"><strong>Ursache:</strong> Pi-KMS/DRM-Treiber legt die HDMI-Scanout-Region nicht korrekt ab Offset (480,0).</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li>Dual-Display-Setup erneut anwenden: <code className="bg-slate-700 px-1 rounded">sudo scripts/fix-gabriel-dual-display-x11.sh</code> (setzt --fb 3920x2240, atomarer Befehl)</li>
                          <li>Schneller Fix: <code className="bg-slate-700 px-1 rounded">scripts/fix-dsi-position-x11.sh</code></li>
                          <li>Doku: <code className="bg-slate-700 px-1 rounded">docs/DSI_HDMI_SPIEGELUNG_X11.md</code></li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: Dual Display X11 – Desktop auf HDMI, stabil */}
                  <div className="rounded-lg border border-sky-600/50 bg-sky-950/20 overflow-hidden">
                    <div className="px-4 py-2 bg-sky-900/40 border-b border-sky-600/50">
                      <h4 className="font-semibold text-sky-200">Dual Display X11 (DSI + HDMI) – Desktop auf HDMI, stabil</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Unter X11 mit DSI (links unten) und HDMI (rechts oben) sollen Desktop-Icons, Hintergrund und Ordner auf HDMI (Primary) erscheinen, ohne ständiges Umschalten.</p>
                      <p className="text-slate-300 mb-2"><strong>Lösung (ab 1.3.3.0):</strong> .xprofile setzt nach 8 s das Layout und startet ~10 s nach Login PCManFM-Desktop neu (Trigger: Desktop → Primary/HDMI). Das delayed-Script wendet das Layout nach 8 s und 16 s erneut an.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Tipps:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li>Einmalig: <code className="bg-slate-700 px-1 rounded">sudo scripts/fix-gabriel-dual-display-x11.sh</code> (schreibt .xprofile und Autostart neu)</li>
                          <li>Falls Desktop wieder auf DSI erscheint: <code className="bg-slate-700 px-1 rounded">scripts/fix-desktop-on-hdmi-x11.sh</code> (PCManFM-Desktop neu starten)</li>
                          <li>Doku: <code className="bg-slate-700 px-1 rounded">docs/DSI_HDMI_SPIEGELUNG_X11.md</code></li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: AnyDesk Wayland */}
                  <div className="rounded-lg border border-amber-600/50 bg-amber-950/30 overflow-hidden">
                    <div className="px-4 py-2 bg-amber-900/40 border-b border-amber-600/50">
                      <h4 className="font-semibold text-amber-200">AnyDesk stürzt ab (Wayland)</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> AnyDesk crasht beim Start unter Wayland.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li>AnyDesk-Autostart deaktivieren, nur manuell starten</li>
                          <li>Eingehende Verbindungen: Xorg-Session beim Login wählen</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: AnyDesk zwei Icons / Flackern */}
                  <div className="rounded-lg border border-amber-600/50 bg-amber-950/30 overflow-hidden">
                    <div className="px-4 py-2 bg-amber-900/40 border-b border-amber-600/50">
                      <h4 className="font-semibold text-amber-200">AnyDesk zwei Icons / Flackern in der Taskleiste</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Zwei AnyDesk-Icons in der Taskleiste oder Flackern – oft durch zwei laufende AnyDesk-Instanzen (z. B. Autostart + manueller Start).</p>
                      <p className="text-slate-300 mb-2 text-xs"><strong>Hinweis:</strong> Die Meldung <code className="bg-slate-700 px-1 rounded">Gdk-CRITICAL gdk_window_thaw_toplevel_updates: assertion … failed</code> ist eine bekannte AnyDesk/GTK-Warnung und in der Regel harmlos – AnyDesk funktioniert weiter.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li><strong>Prüfen, ob doppelt gestartet:</strong> <code className="bg-slate-700 px-1 rounded">./scripts/fix-anydesk-double-icon.sh --check</code> – zeigt laufende AnyDesk-Prozesse und Autostart-Einträge.</li>
                          <li><strong>Eine Instanz beenden:</strong> <code className="bg-slate-700 px-1 rounded">./scripts/fix-anydesk-double-icon.sh</code> – beendet alle AnyDesk-Prozesse und startet genau eine Instanz neu (nur ein Icon).</li>
                          <li><strong>Falls das nicht hilft:</strong> AnyDesk deinstallieren: <code className="bg-slate-700 px-1 rounded">sudo ./scripts/fix-anydesk-double-icon.sh --uninstall</code></li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: Repository/Git */}
                  <div className="rounded-lg border border-sky-600/50 bg-sky-950/20 overflow-hidden">
                    <div className="px-4 py-2 bg-sky-900/40 border-b border-sky-600/50">
                      <h4 className="font-semibold text-sky-200">Repository aktualisieren (lokale Änderungen)</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> git pull überschreibt lokale Änderungen oder Konflikte.</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ol className="list-decimal list-inside text-slate-300 space-y-1">
                          <li><code className="bg-slate-700 px-1 rounded">git stash push -m "Lokale Änderungen"</code></li>
                          <li><code className="bg-slate-700 px-1 rounded">git pull</code></li>
                          <li><code className="bg-slate-700 px-1 rounded">git stash pop</code></li>
                          <li>Bei Merge-Konflikt: Markierungen lösen, Dokumentation oft Remote nehmen</li>
                        </ol>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: Installation */}
                  <div className="rounded-lg border border-sky-600/50 bg-sky-950/20 overflow-hidden">
                    <div className="px-4 py-2 bg-sky-900/40 border-b border-sky-600/50">
                      <h4 className="font-semibold text-sky-200">Welche Installationsmethode soll ich wählen?</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> Es gibt zwei Installationsoptionen – welche ist die richtige?</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li><strong>Systemweite Installation (empfohlen für Produktion):</strong> <code className="bg-slate-700 px-1 rounded">curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/install-system.sh | sudo bash</code> – installiert nach <code className="bg-slate-700 px-1 rounded">/opt/pi-installer/</code>, globale Befehle verfügbar</li>
                          <li><strong>Benutzer-Installation (für Entwicklung/Test):</strong> <code className="bg-slate-700 px-1 rounded">curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/create_installer.sh | bash</code> – installiert nach <code className="bg-slate-700 px-1 rounded">$HOME/PI-Installer/</code>, keine Root-Rechte nötig</li>
                          <li>Siehe <code className="bg-slate-700 px-1 rounded">docs/SYSTEM_INSTALLATION.md</code> für Details</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: Dual Display X11 frühe Konfiguration */}
                  <div className="rounded-lg border border-amber-600/50 bg-amber-950/30 overflow-hidden">
                    <div className="px-4 py-2 bg-amber-900/40 border-b border-amber-600/50">
                      <h4 className="font-semibold text-amber-200">Dual Display X11: Bildschirme schalten mehrfach um / Position falsch</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300 mb-2"><strong>Beschreibung:</strong> DSI-1 und HDMI-1-2 schalten mehrfach um, Position wird nicht korrekt übernommen (DSI sollte links unten sein).</p>
                      <div className="rounded bg-emerald-950/30 border border-emerald-700/40 p-3 mt-2">
                        <p className="font-semibold text-emerald-300 mb-1">Lösungen:</p>
                        <ul className="list-disc list-inside text-slate-300 space-y-1">
                          <li><strong>Frühe Konfiguration verwenden:</strong> <code className="bg-slate-700 px-1 rounded">sudo ./scripts/fix-gabriel-dual-display-x11-early.sh</code> – verwendet LightDM session-setup-script für frühe, einmalige Konfiguration</li>
                          <li><strong>Position korrekt:</strong> DSI-1 wird zuerst gesetzt (links unten 0x1440), dann HDMI-1-2 (rechts oben 480x0)</li>
                          <li><strong>Alte Skripte deaktivieren:</strong> Das Skript deaktiviert automatisch alte enable-hdmi.sh und verzögerte Autostart-Skripte</li>
                          <li>Nach Neustart sollte die Konfiguration sofort korrekt sein ohne mehrfache Umschaltungen</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                  {/* FAQ: Logs */}
                  <div className="rounded-lg border border-slate-600/50 bg-slate-900/30 overflow-hidden">
                    <div className="px-4 py-2 bg-slate-800/60 border-b border-slate-600/50">
                      <h4 className="font-semibold text-slate-200">Log-Datei</h4>
                    </div>
                    <div className="p-4 text-sm">
                      <p className="text-slate-300"><code className="bg-slate-700 px-1 rounded">…/logs/pi-installer.log</code> · Einstellungen → Logs laden · <code className="bg-slate-700 px-1 rounded">PI_INSTALLER_LOG_PATH</code></p>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'einstellungen' && (
            <motion.div
              key="einstellungen"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <Settings className="text-yellow-500" />
                Einstellungen
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">Zentrale Einstellungen für Sprache, Backup, Cloud, Logs und System.</p>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Funktionen</h3>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li><strong>Sprache:</strong> Deutsch oder Englisch für die Oberfläche</li>
                    <li><strong>Standard Backup-Ziel:</strong> Verzeichnis für lokale Backups (wird z. B. in Backup & Restore vorgeschlagen)</li>
                    <li><strong>Cloud-Backup Einstellungen:</strong> Anbieter (WebDAV, S3, Google, Azure), Zugangsdaten, Verbindung testen, Quota anzeigen</li>
                    <li><strong>Logging:</strong> Log-Level (DEBUG, INFO, WARNING, ERROR); Log-Pfad anzeigen; „Logs laden“ zeigt die letzten Zeilen im Browser</li>
                    <li><strong>Log-Rotation:</strong> Logs nach 30 Tagen (konfigurierbar) bzw. nach Größe rotiert</li>
                    <li><strong>Sudo-Passwort:</strong> Einmal eingeben und „Speichern“ (nur Session) – wird für Firewall, Benutzer, Installationen usw. genutzt</li>
                    <li><strong>Frontend-Netzwerk-Zugriff:</strong> Option „Remote-Zugriff deaktivieren“ – dann nur localhost erreichbar</li>
                    <li><strong>Neustart:</strong> System neu starten (sudo)</li>
                  </ul>
                </div>
                <ScreenshotImg src="/docs/screenshots/screenshot-settings.png" alt="Einstellungen" title="Einstellungen – Übersicht" hint="Zeigt Tabs Sprache, Backup, Cloud, Logs." />
                <div className="card-info">
                  <h4 className="text-sm font-semibold  mb-1">💡 Tipp</h4>
                  <p className="text-xs opacity-95">
                    Sudo-Passwort zu Beginn einmal speichern („Ohne Prüfung speichern“ ist Standard), dann funktionieren Firewall, Benutzer, Musikbox-Installation usw. ohne erneute Abfrage in derselben Sitzung. Bei Fehlern: Einstellungen → Logs laden und Backend-Log prüfen.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {activeChapter === 'versionen' && (
            <motion.div
              key="versionen"
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -8 }}
              transition={{ duration: 0.15 }}
              className="rounded-xl bg-slate-800/60 dark:bg-slate-800/60 border border-slate-600 dark:border-slate-600 p-6"
            >
              <h2 className="text-2xl font-bold text-white dark:text-white mb-4 flex items-center gap-2">
                <BookOpen className="text-sky-400" />
                Versionsnummern & Changelog
              </h2>
              <div className="space-y-4 opacity-95">
                <p className="text-sm">Die Versionsnummer folgt dem Schema <strong>X.Y.Z.W</strong>.</p>
                <ScreenshotImg src="/docs/screenshots/screenshot-documentation.png" alt="Versionen & Changelog" title="Dokumentation – Versionen & Changelog" />
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li><strong>X:</strong> Gravierende Änderungen</li>
                  <li><strong>Y:</strong> Größere Releases</li>
                  <li><strong>Z:</strong> Neue Features (wird erhöht, wenn ein neues Feature hinzukommt; W wird auf 0 gesetzt)</li>
                  <li><strong>W:</strong> Bugfixes, Ergänzungen (ohne neues Feature)</li>
                </ul>
                <p className="text-sm">
                  Die Version wird <strong>pro Bereich</strong> bei jeder Änderung/Fehlerbehebung erhöht; die Dokumentation wird dazu selbstständig ergänzt. Details: <code className="bg-slate-700 px-1 rounded">VERSIONING.md</code> im Projekt.
                </p>
                <div className="mt-4 p-3 bg-sky-900/20 dark:bg-sky-900/20 border border-sky-700/40 dark:border-sky-700/40 rounded-lg">
                  <p className="text-sm font-semibold text-white dark:text-white mb-2">Aktuelle Version: 1.3.8.0</p>
                  <div className="mb-3">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.3.8.0 (Remote Companion – Dokumentation)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Dokumentation:</strong> docs/REMOTE_COMPANION.md (Übersicht, API, Rollen, Events); docs/REMOTE_COMPANION_DEV.md (Entwicklerleitfaden: Modul registrieren, Widgets, Aktionen); Phase-2-Ausblick konzeptionell</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.3.7.6 (OLED-I2C-Erkennung präzisiert)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Control Center:</strong> OLED-Erkennung nutzt nun `i2cdetect -r`, um falsche Treffer auf ungeeigneten I2C-Bussen zu vermeiden</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.3.7.5 (OLED-Anzeige wieder funktionsfähig)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Backend:</strong> OLED-Telemetrie-API und Runner-Aktionen wieder aktiviert; Autostart beim Backend-Start wiederhergestellt</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.3.4.2 (DSI Radio NDR-Ton, Backend-Venv, Doku)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>DSI Radio v2.1:</strong> NDR 1/NDR 2 – getestete Stream-URLs (icecast.ndr.de) werden bevorzugt, Ton funktioniert; Audio-Ausgabe nur auf Freenove erzwungen, auf dem Laptop Standardgerät</li>
                      <li><strong>Backend:</strong> start-backend.sh und start.sh nutzen durchgängig Venv (kein „externally-managed-environment“ mehr)</li>
                      <li><strong>Doku/FAQ:</strong> Linux-Terminal-Anweisungen, „NDR 1 / NDR 2: Kein Ton“ in FAQ</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.3.4.1 (Radio-App Metadaten-Verbesserungen)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Radio-App:</strong> System-Metadaten aus PulseAudio/PipeWire (wie Lautstärkeregler); "Es läuft:" immer sichtbar; Logo/Sendername beim Wiederherstellen; Show-Metadaten-Erkennung; Interpret-Textgröße angepasst</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.3.4.0 (Systemweite Installation, Dual Display X11 frühe Konfiguration)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Installation:</strong> Systemweite Installation nach /opt/pi-installer/ gemäß Linux FHS; install-system.sh, update-system.sh; docs/SYSTEM_INSTALLATION.md</li>
                      <li><strong>Dual Display X11:</strong> LightDM session-setup-script für frühe Konfiguration; Position korrekt (DSI links unten, HDMI rechts oben); keine mehrfachen Umschaltungen</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.3.3.0 (Dual Display X11 stabil, Doku, FAQ)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Dual Display X11:</strong> Läuft stabil ohne ständiges Umschalten – Position (DSI links unten, HDMI rechts oben), Desktop/Hintergrund auf HDMI; .xprofile ~10 s + delayed-Script 8 s/16 s</li>
                      <li><strong>Dokumentation:</strong> docs/DSI_HDMI_SPIEGELUNG_X11.md – Spiegelung, Position, Desktop auf HDMI, Trigger; FAQ ergänzt</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.3.2.0 (DSI-Spiegelung X11, Doku, FAQ)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Dual Display X11:</strong> DSI-Spiegelung auf HDMI behoben – xrandr --fb 3920x2240; docs/DSI_HDMI_SPIEGELUNG_X11.md</li>
                      <li><strong>FAQ:</strong> Neuer Eintrag „DSI-Desktop oben links auf HDMI gespiegelt (X11)“</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.3.1.0 (Laufwerk klonen, NVMe, Freenove/Dualdisplay, FAQ)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Backup & Restore:</strong> Laufwerk klonen – System von SD auf NVMe/USB klonen (Hybrid-Boot); NVMe-Erkennung</li>
                      <li><strong>Dokumentation:</strong> Freenove Pro (4,3″ Touchscreen), Dualdisplay DSI0+HDMI1, Lernbereich Touchscreen DSI0</li>
                      <li><strong>FAQ:</strong> Vollständige FAQ aus Troubleshooting – Fehlername, Beschreibung, Lösungen; funktionales Design</li>
                      <li>Festgestellte Probleme siehe FAQ – Lösungswege dort dokumentiert</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.3.0.0 (Transformationsplan: Raspberry Discovery Box)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>App Store:</strong> 7 Apps (Home Assistant, Nextcloud, Pi-hole, Jellyfin, WordPress, VS Code Server, Node-RED); Kachel-Layout, Suche, Kategorien</li>
                      <li><strong>First-Run-Wizard:</strong> Willkommen → Optional (Netzwerk/Sicherheit/Backup) → „Was möchtest du tun?“ → Empfohlene Apps</li>
                      <li><strong>Dashboard:</strong> „Dein Pi läuft!“, Status-Ampel, Schnellaktionen, Ressourcen-Ampel</li>
                      <li><strong>Mobile:</strong> Hamburger-Menü, Sidebar als Overlay, responsive</li>
                      <li><strong>Hilfe:</strong> Kontextsensitive Tooltips (?); „Erfahrene Einstellungen“ in Einstellungen; fehlerfreundliche Texte</li>
                      <li><strong>Installer:</strong> Single-Script-Installer, systemd-Service, One-Click-Doku; Python 3.9+</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.2.0.6 (NAS Duplikat-Finder)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>NAS:</strong> Duplikate & Aufräumen – fdupes/jdupes installieren, scannen, Duplikate ins Backup verschieben; System-/Cache-Verzeichnisse ausschließen; vorgeschlagener Scan-Pfad</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.2.0.5 (Pi 5 HDMI-Audio Troubleshooting)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Raspberry Pi 5:</strong> Troubleshooting „Kein Ton über HDMI“ erweitert – Symptome, Ursache (vc4-kms-v3d-pi5 Overlay), Schritte in Doku, INSTALL.md, PI_OPTIMIZATION.md</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.2.0.4 (Pi-Optimierung, Erkennung, CPU-Reduktion)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Pi-Erkennung:</strong> Fallback über Device-Tree – Raspberry Pi wird zuverlässig erkannt; Raspberry Pi Config erscheint im Menü</li>
                      <li><strong>CPU-Reduktion:</strong> Light-Polling, Dashboard 30 s auf Pi; Monitoring ohne Live-Charts auf Pi; Auslastung nur im Dashboard</li>
                      <li><strong>UI:</strong> Card-Hover ohne Bewegung; Stats-Merge behält Hardware &amp; Sensoren beim Polling</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.2.0.3 (Mixer-Installation robuster, manueller Befehl bei Fehler)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Mixer-Installation:</strong> Update und Install in zwei Schritten; Dpkg-Optionen für nicht-interaktiv; bei Fehler wird „Manuell im Terminal ausführen“ mit Befehl und Kopieren-Button angezeigt (Musikbox &amp; Kino/Streaming)</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.2.0.2 (Hardware ohne Systeminfo, Treiber-Hinweise unter Grafikkarte)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Dashboard – Hardware &amp; Sensoren:</strong> Bereich „Systeminformationen“ entfernt (ist bereits in der Übersicht sichtbar)</li>
                      <li><strong>CPU &amp; Grafik:</strong> NVIDIA-/AMD-/Intel-Treiber-Hinweise nicht mehr unter der CPU, sondern unter der jeweiligen Grafikkarte (iGPU/diskret) angezeigt</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.2.0.1 (Dashboard Lesbarkeit, CPU-Anzeige, Mixer, Menü-Kontrast)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li>IP/Updates lesbar; Menü-Buttons kontrastreich; CPU nur eine Zusammenfassung (Kerne, Threads, Cache, Befehlssätze); Mixer-Installation robuster</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.2.0.0 (Musikbox fertig, Mixer, Dashboard)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Musikbox:</strong> Musikbox-Bereich abgeschlossen – Mixer-Buttons (pavucontrol/qpwgraph), Installation der Mixer-Programme per Knopfdruck (pavucontrol &amp; qpwgraph), Sudo-Modal für Mixer-Installation</li>
                      <li><strong>Mixer:</strong> Mixer in Musikbox und Kino/Streaming eingebaut – „Mixer öffnen (pavucontrol)“ / „Mixer öffnen (qpwgraph)“ starten die GUI-Mixer; „Mixer-Programme installieren“ installiert pavucontrol und qpwgraph per apt; Backend setzt DISPLAY=:0 für GUI-Start</li>
                      <li><strong>Dashboard:</strong> Dashboard-Erweiterungen und Quick-Links; Versionsnummer und Changelog auf 1.2.0.0 aktualisiert</li>
                      <li><strong>Dokumentation:</strong> Changelog 1.2.0.0, Troubleshooting Mixer-Installation (manueller Befehl), API install-mixer-packages/run-mixer ergänzt</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.4.0 (Sicherheit-Anzeige, Dokumentation &amp; Version)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Sicherheit:</strong> Unter „Sicherheit“ wird im Dashboard wieder korrekt „2/5 aktiviert“ angezeigt, wenn Firewall und Fail2Ban aktiv sind (UFW-Status wird wie auf der Sicherheits-Seite aus dem Status-String abgeleitet, falls das Backend <code className="bg-slate-700 px-1 rounded">active: false</code> liefert)</li>
                      <li><strong>Dokumentation:</strong> Changelog und Versionsnummer aktualisiert</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.3.0 (Systeminformationen: Grafik &amp; RAM übersichtlich)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Grafik:</strong> Kurze Handelsbezeichnung (z. B. NVIDIA RTX 4070 Laptop · 8 GB GDDR6); Integrierte Grafik (iGPU) und Grafikkarte (diskret) getrennt; NVIDIA-Audio nicht mehr bei Grafik; AMD Ryzen iGPU (z. B. Radeon 610M) als „Integriert“</li>
                      <li><strong>RAM:</strong> Arbeitsspeicher mit Typ (DDR4/DDR5), Kapazität und Takt (z. B. DDR5 · 32 GB @ 4800 MT/s)</li>
                      <li><strong>Dashboard:</strong> Systeminformationen und CPU &amp; Grafik mit klarer Trennung Integriert/Diskret</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.2.0 (Linux-System: Raspberry-Pi-Bereiche ausblenden, Assistent/Willkommen, Terminal-Update, Webmin, Hausautomation, Doku)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Redis Commander:</strong> Hinweis „optional“, Port 8081; Fehlermeldung „not found“ vermieden</li>
                      <li><strong>Raspberry Pi Config:</strong> Auf Nicht-Pi komplett ausgeblendet (Menü + Redirect); Assistent: „Willkommen bei [Hostname]!“ statt „PI-Installer“</li>
                      <li><strong>Control Center:</strong> Bereich „Performance“ nur auf Raspberry Pi sichtbar</li>
                      <li><strong>Update im Terminal:</strong> Weitere Terminals (Kitty, Alacritty, QTerminal, Tilix, urxvt); bei Fehler kopierbarer Befehl + „Kopieren“-Button</li>
                      <li><strong>Dashboard Schnellstart:</strong> Kontrast erhöht, Schrift Anthrazit (text-slate-700/800)</li>
                      <li><strong>Sicherheit:</strong> Firewall „Aktiv · Installiert“ wenn UFW aktiv</li>
                      <li><strong>Webserver:</strong> Webmin-Karte immer sichtbar; „Diese Anwendung“ statt „PI-Installer“; Hinweis Nachinstall/Webadmin</li>
                      <li><strong>Hausautomation:</strong> Empfehlung-Karte Kontrast (dunkle Schrift); Deinstallieren-Button + API <code className="bg-slate-700 px-1 rounded">/api/homeautomation/uninstall</code></li>
                      <li><strong>Prometheus:</strong> Bei installiertem Prometheus Beispiel „Was Prometheus kann“ (PromQL, Targets, Grafana)</li>
                      <li><strong>Dokumentation:</strong> Quellen für Linux-System (Ubuntu, Arch, Fedora, Manpages) ergänzt</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.19 (Dashboard-Status DEV/Webserver/Musikbox, Hausautomation Suche & Empfehlung, Dev QT/QML, Menü, Systeminfo)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>TODO 11 – Dashboard:</strong> Status für Dev-Umgebung (installierte Teile, Grundbetrieb), Webserver (läuft, Webseiten erreichbar), Musikbox (Installation, Grundbetrieb); API <code className="bg-slate-700 px-1 rounded">/api/dashboard/services-status</code></li>
                      <li><strong>TODO 12 – Hausautomation:</strong> Runder roter Button „Suche nach Elementen im Haus“; bei Suche Text „Das Haus wird assimiliert!“ / „Widerstand ist zwecklos!“; Empfehlung & Systembeschreibung (Home Assistant, OpenHAB, Node-RED) mit Kompatibilität/Anbietern; API <code className="bg-slate-700 px-1 rounded">/api/homeautomation/search</code></li>
                      <li><strong>TODO 13 – Dev-Umgebung:</strong> Installationsoption QT/QML (Qt5, QML – GUI-Entwicklung); Hinweis „Weitere Sprachen & Tools“ (Kotlin, Swift, Flutter, .NET)</li>
                      <li><strong>Menü:</strong> Übersichtlicher und logisch sortiert (Übersicht → Einstellungen/Sicherheit/Benutzer → Dienste → Wartung → Raspberry Pi Config)</li>
                      <li><strong>Systeminformationen:</strong> Hauptspeicher-Größe, Grafikkarte & Grafikspeicher; CPU: Threads gesamt, Auslastung physikalische Kerne horizontal; NVIDIA-GPU mit Spezifikationen</li>
                      <li><strong>Sonstiges:</strong> IP-Hinweistext dunkler/lesbarer; Grafana-Erkennung erweitert (Snap, systemctl list-units); GPU-Fallback für Nicht-Pi (lspci, nvidia-smi)</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.18 (Musikbox Iris, Hinweis-Karten, IP im Dashboard, Backend-Starter, Doku Frontend-Start)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Musikbox:</strong> Mopidy-Webclient Iris (Installation für User mopidy, Diagnose, manuelle Befehle); Apple Music / Amazon Music; AirPlay auf verbundenem Rechner (Pi oder Laptop); einheitliche Hinweis-/Info-/Warn-Karten</li>
                      <li><strong>Dashboard:</strong> Karte „Netzwerk – IP-Adressen“ (Hostname + IPs, z. B. für http://&lt;IP&gt;:6680/iris)</li>
                      <li><strong>Backend:</strong> Desktop-Starter „PI-Installer Backend starten“ (Skript + Anlegen auf Schreibtisch); Mopidy-Diagnose-Endpoint</li>
                      <li><strong>Dokumentation:</strong> Abschnitt „Backend & Frontend starten“ (Frontend: ./start-frontend.sh, npm run dev, tauri:dev)</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.17 (Musikbox: Kontrast, Bezahldienste, Buttons; Kino/Streaming; Peripherie: Treiber aus Grafik, Übersicht)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Musikbox:</strong> Kontrast erhöht (Music-Server & Bezahldienste, Ausgabequelle/Mixer – weiße/dunkelgraue Texte); Bezahldienste-Liste (Spotify, Tidal, Deezer, Plex Pass) mit Hinweis Zugangsdaten in Programmen; Buttons zu Mopidy/Volumio/Plex/Internetradio</li>
                      <li><strong>Kino / Streaming:</strong> Neuer Bereich – Video- und Soundausgabe (TV, Beamer, Monitor 1/2, Surround/DTS/Dolby); Streaming-Dienste (Amazon Prime, Netflix, Disney+, Sky, Paramount+, ARD/ZDF) mit Links; Zugangsdaten-Hinweis</li>
                      <li><strong>Peripherie-Scan:</strong> Treiber aus Grafik-Karte entfernt (nur noch GPU-Name + Treiber-Status); „Sonstige Treiber“ eigene Anzeige (PCI/Kernel-Module); Hersteller prüfen Treiber für erkannte Komponenten, Herstellerlisten/Anbieter identifizieren; Kameras nur bei Kameras, Maus nur bei Maus (inkl. Touchpad); Eingabegeräte einzeln mit Namen, Hinweis Corsair/ASUS/Angetube; Übersicht übersichtlicher</li>
                      <li><strong>Dokumentation:</strong> Kino/Streaming, Musikbox und Peripherie-Scan ergänzt</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.16 (Peripherie-Scan: GPU-Name, Tastatur/Maus/Touchpad/Headset, Lesbarkeit; Musikbox: Ausgabequelle/Mixer/Dolby)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Peripherie-Scan:</strong> Grafikkarte(n) mit vollem Namen und Treiber-Status („Treiber: xy“ oder „Hersteller-Treiber prüfen“); Backend dedupliziert GPU-Einträge (keine 34 Shader-Einheiten mehr, nur echte VGA/Display/3D-Controller)</li>
                      <li><strong>Tastatur/Maus:</strong> Anzeige „Welche:“ mit konkreter Bezeichnung (z. B. Logitech K380); Maus-Hinweis: Belegung aller Tasten über xinput, imwheel oder Hersteller-Software (z. B. Logitech Options)</li>
                      <li><strong>Touchpad & Headset:</strong> Eigene Zeile in der Übersicht – Touchpad aus Eingabegeräten, Headset/Audio aus USB; Hinweise zu Ausgabequelle (Musikbox/Einstellungen, PulseAudio/PipeWire), Dolby Atmos herstellerspezifisch</li>
                      <li><strong>Lesbarkeit:</strong> „Neu bei diesem Scan“-Liste und „Temperatursensoren – Normalbereich“ in Dunkelgrau/Weiß für bessere Lesbarkeit (nicht mehr hellgrau auf hellgrün/grau)</li>
                      <li><strong>Musikbox (Doku):</strong> Abschnitt Ausgabequelle, Mixer (pavucontrol/qpwgraph), Headset/Lautsprecher-Treiber, Dolby Atmos ergänzt</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.15 (Peripherie: Hersteller & Treiber für Linux)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Peripherie-Scan:</strong> Liste der Hersteller, bei denen Treiber für die erkannte Hardware unter Linux erhältlich sind (NVIDIA, AMD, Intel, Realtek, Broadcom, Qualcomm, Logitech, Lenovo, Dell, HP) mit Links zu Treiber-/Support-Seiten</li>
                      <li><strong>Hinweis:</strong> Diese Treiber existieren; der Hersteller empfiehlt ggf. deren Nutzung, um alle Features der Hardware zu nutzen</li>
                      <li>Erkannte Hersteller werden aus GPUs und PCI-Geräten abgeleitet und hervorgehoben; Doku Peripherie-Scan ergänzt</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.14 (Benutzer: System vs. Personen, Rolle Gast)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Benutzer:</strong> Zwei Bereiche – „Systembenutzer / Dienste“ (UID &lt; 1000, nur Anzeige) und „Benutzer (Personen)“ (UID ≥ 1000, anlegen/löschen)</li>
                      <li><strong>Rollen:</strong> Rolle „Gast“ ergänzt (eingeschränkte Rechte); Administrator, Entwickler, Benutzer, Gast; weitere Rollen bei Bedarf manuell</li>
                      <li>Backend <code className="bg-slate-700 px-1 rounded">/api/users</code> liefert <code className="bg-slate-700 px-1 rounded">system_users</code> und <code className="bg-slate-700 px-1 rounded">human_users</code> (mit UID)</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.13 (Peripherie-Scan, Musikbox Sudo, Versions-Sync)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Peripherie-Scan:</strong> Bei 404 klarer Hinweis „Backend neu starten“; Debug-Endpoint <code className="bg-slate-700 px-1 rounded">/api/debug/routes</code> zum Prüfen der registrierten Routen</li>
                      <li><strong>Musikbox:</strong> SudoPasswordModal statt Browser-Prompt; zusätzliche Features (Internetradio, AirPlay, Spotify Connect) werden mit Sudo-Passwort installiert; <code className="bg-slate-700 px-1 rounded">requires_sudo_password</code> wird ausgewertet</li>
                      <li><strong>Versionsführung:</strong> Einzige Quelle <code className="bg-slate-700 px-1 rounded">VERSION</code>; <code className="bg-slate-700 px-1 rounded">npm run prebuild</code> synchronisiert package.json und tauri.conf.json automatisch</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.12 (TODO 7–10, Dashboard, Peripherie, Systeminfos)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Monitoring (TODO 7):</strong> SudoPasswordModal statt Browser-Prompt; Einzelauswahl Node Exporter, Prometheus, Grafana (Checkboxen); nur ausgewählte Komponenten installieren</li>
                      <li><strong>Musikbox (TODO 8):</strong> Optionen Internetradio (mopidy-internetarchive), Streaming; Info-Box zu Music-Servern und Bezahldiensten; Backend <code className="bg-slate-700 px-1 rounded">enable_internetradio</code>, <code className="bg-slate-700 px-1 rounded">enable_streaming</code></li>
                      <li><strong>Systemdaten (TODO 9):</strong> <code className="bg-slate-700 px-1 rounded">/api/system-info</code> liefert alle Temperatursensoren (thermal_zone + hwmon), alle Laufwerke inkl. NVMe/Block-Geräte, Lüfter, Displays; Dashboard-Karte „Sensoren & Schnittstellen“; Motherboard (DMI), RAM-Typ/Geschwindigkeit (dmidecode), CPU-Name in Systeminformationen</li>
                      <li><strong>Peripherie-Scan (TODO 10):</strong> Konsole mit animierter Ausgabe der gefundenen Komponenten; Button „Zum Dashboard“; <code className="bg-slate-700 px-1 rounded">lspci -k</code> für alle GPUs (inkl. zweite NVIDIA) und Treiber; Vollpfad /usr/bin/lspci, /usr/bin/lsusb; Sektion „Systembezogene Treiber“ (Kernel-Module)</li>
                      <li><strong>Dashboard:</strong> Karte „Systeminformationen“ (CPU-Name, Motherboard, OS, RAM Typ/Geschwindigkeit); Karte „Systembezogene Treiber“ (alle PCI-Geräte mit/ohne Treiber); CPU & Grafik: Auslastung pro <strong>physikalischem Kern</strong> (aus /proc/cpuinfo core id), Fallback auf log. CPUs; Link „Treiber beim Hersteller suchen“ (Intel/AMD) bei CPU</li>
                      <li><strong>Backend:</strong> <code className="bg-slate-700 px-1 rounded">get_per_core_usage()</code>, <code className="bg-slate-700 px-1 rounded">get_motherboard_info()</code>, <code className="bg-slate-700 px-1 rounded">get_ram_info()</code>, <code className="bg-slate-700 px-1 rounded">get_cpu_name()</code>; <code className="bg-slate-700 px-1 rounded">per_core_usage</code>, <code className="bg-slate-700 px-1 rounded">physical_cores</code>, <code className="bg-slate-700 px-1 rounded">drivers</code> in system-info</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.11 (Plattform / Linux-System)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Menü:</strong> Punkt „Raspberry Pi Config“ wird deaktiviert, wenn kein Raspberry Pi erkannt wird</li>
                      <li><strong>Bezeichnungen:</strong> Überall wo „Raspberry Pi System“ stand, wird bei Nicht-Pi nun „Linux-System“ angezeigt, inkl. Hinweis ob Desktop oder Laptop</li>
                      <li>Backend: <code className="bg-slate-700 px-1 rounded">/api/system-info</code> liefert <code className="bg-slate-700 px-1 rounded">is_raspberry_pi</code> und <code className="bg-slate-700 px-1 rounded">device_type</code> (desktop/laptop); Frontend: PlatformContext mit <code className="bg-slate-700 px-1 rounded">systemLabel</code> / <code className="bg-slate-700 px-1 rounded">systemLabelPossessive</code></li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.10 (Dashboard)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>CPU & Grafik im Dashboard:</strong> Karte „CPU & Grafik“ zeigt <strong>jede CPU</strong> (Modell, aktuelle/empfohlene MHz) und <strong>jede gefundene GPU</strong> (Name, Speicher)</li>
                      <li>Daten kommen aus <code className="bg-slate-700 px-1 rounded">/api/system-info</code> (hardware.cpus, hardware.gpus); Backend parst /proc/cpuinfo (alle Prozessoren), vcgencmd (Pi) bzw. lspci (GPUs)</li>
                      <li>Raspberry Pi Config: CPU/GPU-Details ins Dashboard verschoben; dort nur noch Hinweis auf Dashboard sowie Speicheraufteilung und Spannungserhöhung (over_voltage)</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.9 (Raspberry Pi Config)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>CPU & Grafik – Systeminfos:</strong> API <code className="bg-slate-700 px-1 rounded">/api/raspberry-pi/system-info</code> (vcgencmd, /proc/cpuinfo); Hinweise Speicheraufteilung und over_voltage</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.8 (Display)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Bildwiederholfrequenz:</strong> Geänderte Bildwiederholfrequenz wird zuverlässig übernommen (Rate immer mitsenden: gewählter Wert oder Standard des Modus)</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.7 (Control Center – Services)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>SSH starten:</strong> Button „SSH starten“, wenn SSH aktiviert aber gestoppt</li>
                      <li><strong>VNC starten:</strong> Button „VNC starten“, wenn VNC gestoppt</li>
                      <li>APIs <code className="bg-slate-700 px-1 rounded">/api/control-center/ssh/start</code>, <code className="bg-slate-700 px-1 rounded">/api/control-center/vnc/start</code></li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.6 (WLAN)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Verbindung zu konfigurierten Netzwerken:</strong> Bei konfigurierten WLAN-Netzwerken Button „Verbinden“ (wpa_cli select_network)</li>
                      <li>API <code className="bg-slate-700 px-1 rounded">/api/control-center/wifi/connect</code></li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.5</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Dokumentation:</strong> Auf aktuellen Stand gebracht; Repository-Workflow (git stash, pull, stash pop) in Troubleshooting; Versionsführung pro Bereich in VERSIONING.md</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.4 (28./29. Januar 2026)</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li><strong>Control Center – Scanner:</strong> SANE-Scanner (USB + Netzwerk/eSCL/airscan), SANE-Installationsprüfung</li>
                      <li><strong>Control Center – Performance:</strong> CPU-Governor, GPU-Memory, Overclocking (arm_freq, over_voltage, force_turbo), Swap-Größe</li>
                      <li><strong>Control Center – Drucker:</strong> Deutsche Locale-Unterstützung für lpstat</li>
                      <li><strong>Dev-Umgebung:</strong> Rust und Tauri als Programmiersprachen hinzugefügt</li>
                      <li><strong>Sudo-Passwort:</strong> Nur in Session gespeichert (sessionStorage), „Ohne Prüfung speichern" standardmäßig aktiv</li>
                      <li><strong>Dashboard:</strong> Zeigt klaren Hinweis wenn Backend nicht erreichbar</li>
                      <li><strong>Logging:</strong> Log-Pfad-API, verbessertes Logging-Setup (NameError behoben)</li>
                      <li><strong>Dokumentation:</strong> Troubleshooting-Sektion, GitHub-Setup-Anleitungen</li>
                      <li>Bugfix: Scanner-Timeout auf 45s erhöht (Netzwerkscanner)</li>
                      <li>Bugfix: scanimage-Output mit 404-Prefixes korrekt geparst</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.3</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li>Control Center – Desktop: Boot-Ziel (Desktop vs. Kommandozeile)</li>
                      <li>Control Center – Display: Auflösung, Bildwiederholrate, Rotation (xrandr)</li>
                      <li>Desktop-App (Tauri): eigenständiges Fenster ohne Browser, gleiches UI</li>
                      <li>Dokumentation: Display-, Desktop- und Desktop-App-Bereich</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.2</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li>Bugfix: Verschlüsselte Backups korrekt erkannt</li>
                      <li>Bugfix: Cloud-Upload nutzt Cloud-Einstellungen aus Thread</li>
                      <li>Verbesserung: Cloud-Upload-Logging</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.1</p>
                    <ul className="list-disc list-inside text-xs opacity-95 mt-1 ml-4 space-y-1">
                      <li>Control Center: WLAN, SSH, VNC, Tastatur, Lokalisierung</li>
                      <li>Raspberry Pi Config: Neustart, Reset</li>
                    </ul>
                  </div>
                  <div className="pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.0, 1.0.0.1</p>
                    <p className="text-xs text-slate-400 dark:text-slate-400">Raspberry Pi Config Modell-Erkennung, UI-Verbesserungen, Backup/Cloud.</p>
                  </div>
                </div>
                <div className="mt-4 p-3 bg-purple-900/20 dark:bg-purple-900/20 border border-purple-700/40 dark:border-purple-700/40 rounded-lg">
                  <h3 className="text-sm font-semibold text-purple-300 dark:text-purple-300 mb-2">Quellen (Raspberry Pi)</h3>
                  <ul className="list-disc list-inside text-xs opacity-95 space-y-1 ml-2">
                    <li><a href="https://www.raspberrypi.com/documentation/computers/config_txt.html" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">Raspberry Pi config.txt</a></li>
                    <li>Device Tree Overlays, GPIO, Overclocking</li>
                  </ul>
                  <h3 className="text-sm font-semibold text-purple-300 dark:text-purple-300 mt-3 mb-2">Quellen (Linux-System)</h3>
                  <ul className="list-disc list-inside text-xs opacity-95 space-y-1 ml-2">
                    <li><a href="https://wiki.ubuntuusers.de/" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">Ubuntu Users Wiki</a></li>
                    <li><a href="https://www.archlinux.org/docs/" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">Arch Linux Dokumentation</a></li>
                    <li><a href="https://docs.fedoraproject.org/" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">Fedora Documentation</a></li>
                    <li><a href="https://help.ubuntu.com/" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">Ubuntu Help</a></li>
                    <li>systemd, UFW, apt/dpkg – Manpages (<code className="bg-slate-700 px-1 rounded">man &lt;befehl&gt;</code>)</li>
                  </ul>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  )
}

export default Documentation
