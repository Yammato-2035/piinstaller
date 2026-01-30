import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, Cloud, HardDrive, Settings, Cpu, Monitor, HelpCircle } from 'lucide-react'

type SectionId = 'backup-restore' | 'cloud' | 'control-center' | 'raspberry-pi-config' | 'einstellungen' | 'desktop-app' | 'troubleshooting' | 'versionen'

const SECTIONS: { id: SectionId; label: string; icon: React.ElementType }[] = [
  { id: 'backup-restore', label: 'Backup & Restore', icon: HardDrive },
  { id: 'cloud', label: 'Cloud-Einstellungen', icon: Cloud },
  { id: 'control-center', label: 'Control Center', icon: Settings },
  { id: 'raspberry-pi-config', label: 'Raspberry Pi Config', icon: Cpu },
  { id: 'einstellungen', label: 'Einstellungen', icon: Settings },
  { id: 'desktop-app', label: 'Desktop-App (Tauri)', icon: Monitor },
  { id: 'troubleshooting', label: 'Troubleshooting', icon: HelpCircle },
  { id: 'versionen', label: 'Versionen & Changelog', icon: BookOpen },
]

const Documentation: React.FC = () => {
  const [activeChapter, setActiveChapter] = useState<SectionId>('backup-restore')

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
        <AnimatePresence mode="wait">
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
              <div className="space-y-4 text-slate-300 dark:text-slate-300">
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Backup erstellen</h3>
                  <p className="text-sm mb-2">
                    Erstelle vollständige, inkrementelle oder Daten-Backups deines Raspberry Pi Systems.
                    Backups können lokal gespeichert oder direkt in die Cloud hochgeladen werden.
                  </p>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li><strong>Vollständig:</strong> Komplettes System-Backup (empfohlen für erste Sicherung)</li>
                    <li><strong>Inkrementell:</strong> Nur Änderungen seit dem letzten Voll-Backup</li>
                    <li><strong>Daten:</strong> Nur Benutzerdaten (/home, /var/www, /opt)</li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Verschlüsselung</h3>
                  <p className="text-sm mb-2">
                    Backups können mit GPG oder OpenSSL verschlüsselt werden, um sensible Daten zu schützen.
                  </p>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li><strong>GPG:</strong> AES-256 Verschlüsselung, Passphrase optional</li>
                    <li><strong>OpenSSL:</strong> AES-256-CBC Verschlüsselung, Passphrase erforderlich</li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Cloud-Backups</h3>
                  <p className="text-sm mb-2">
                    Wähle den Cloud-Anbieter für Backups aus. Die Konfiguration erfolgt unter Einstellungen.
                  </p>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li>WebDAV (Seafile, Nextcloud, allgemein)</li>
                    <li>Amazon S3 & S3-kompatibel (MinIO, etc.)</li>
                    <li>Google Cloud Storage</li>
                    <li>Azure Blob Storage</li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Backup-Wiederherstellung</h3>
                  <p className="text-sm">
                    Stelle Backups wieder her, indem du ein Backup auswählst und den Restore-Prozess startest.
                    Verschlüsselte Backups werden automatisch entschlüsselt.
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
              <div className="space-y-4 text-slate-300 dark:text-slate-300">
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Cloud-Anbieter konfigurieren</h3>
                  <p className="text-sm mb-2">
                    Unter Einstellungen → Cloud-Backup Einstellungen kannst du deinen Cloud-Anbieter konfigurieren.
                    Hier werden Zugangsdaten und Verbindungsparameter eingegeben.
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Speicherplatz-Anzeige (Quota)</h3>
                  <p className="text-sm mb-2">
                    Die Quota-Anzeige zeigt dir den verfügbaren Speicherplatz in deinem Cloud-Speicher an.
                    Sie wird automatisch aktualisiert, wenn du die Cloud-Einstellungen speicherst oder manuell aktualisierst.
                  </p>
                  <p className="text-sm mb-2">Die Anzeige zeigt:</p>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li>Verwendeter Speicherplatz</li>
                    <li>Verfügbarer Speicherplatz</li>
                    <li>Gesamter Speicherplatz</li>
                    <li>Prozentuale Auslastung mit Farbcodierung</li>
                  </ul>
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
              <div className="space-y-4 text-slate-300 dark:text-slate-300">
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">System-Einstellungen</h3>
                  <p className="text-sm mb-3">
                    Das Control Center bietet eine zentrale Verwaltung für alle System-Einstellungen des Raspberry Pi.
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
              <div className="space-y-4 text-slate-300 dark:text-slate-300">
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
                    <p className="text-xs text-slate-300 dark:text-slate-300">
                      Das System erkennt automatisch dein Raspberry Pi Modell und zeigt nur kompatible Einstellungen an.
                    </p>
                  </div>
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
              <div className="space-y-4 text-slate-300 dark:text-slate-300">
                <p className="text-sm">
                  Die PI-Installer-Oberfläche kann als <strong>eigenständige Desktop-Anwendung</strong> laufen –
                  ohne Browserfenster. Dafür wird <strong>Tauri 2</strong> verwendet (WebView-basiert, ressourcenschonend).
                </p>
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
                Troubleshooting
              </h2>
              <div className="space-y-4 text-slate-300 dark:text-slate-300">
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Log-Datei</h3>
                  <p className="text-sm mb-2">
                    Standardpfad: <code className="bg-slate-700 px-1.5 py-0.5 rounded text-slate-200">&lt;Projektordner&gt;/logs/pi-installer.log</code> (z. B. <code className="bg-slate-700 px-1.5 py-0.5 rounded text-slate-200">…/PI-Installer/logs/pi-installer.log</code>).
                    Über Umgebungsvariable <code className="bg-slate-700 px-1.5 py-0.5 rounded text-slate-200">PI_INSTALLER_LOG_PATH</code> änderbar.
                  </p>
                  <p className="text-sm">
                    In der App: <strong>Einstellungen → Logs</strong> → „Logs laden“. Der genaue Pfad wird dort angezeigt.
                    Im Terminal: <code className="bg-slate-700 px-1.5 py-0.5 rounded text-slate-200">tail -f …/logs/pi-installer.log</code>.
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Backend neu starten</h3>
                  <p className="text-sm mb-2">
                    Kein Kompilieren nötig. Im Projektordner:
                  </p>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li><strong>Alles:</strong> <code className="text-slate-400">./start.sh</code> (Backend + Frontend). Vorher <code className="text-slate-400">Ctrl+C</code> zum Beenden.</li>
                    <li><strong>Nur Backend:</strong> <code className="text-slate-400">./start-backend.sh</code>. Vorher laufenden Backend-Prozess beenden.</li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Dashboard zeigt keine Daten / Sudo-Passwort speichert nicht</h3>
                  <p className="text-sm mb-2">
                    Beides funktioniert nur, wenn das <strong>Backend erreichbar</strong> ist (Port 8000). Typische Ursachen:
                  </p>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li>Backend läuft nicht → <code className="text-slate-400">./start.sh</code> oder <code className="text-slate-400">./start-backend.sh</code> ausführen.</li>
                    <li>Frontend wird ohne Vite-Proxy genutzt (z. B. statische Dateien, anderer Port) → API-Anfragen gehen nicht an localhost:8000.</li>
                    <li>Bei „Backend nicht erreichbar“-Hinweis im Dashboard: Einstellungen → Logs prüfen, Backend starten, Seite neu laden.</li>
                  </ul>
                  <p className="text-sm mt-2">
                    Sudo-Passwort: „Ohne Prüfung speichern“ ist standardmäßig aktiv. Nach Speichern beim ersten Einsatz (z. B. Firewall) wird es genutzt; nur in der Session, nicht dauerhaft.
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Scanner werden nicht erkannt</h3>
                  <p className="text-sm mb-2">
                    Scanner-Erkennung nutzt <strong>SANE</strong>. Bei Problemen:
                  </p>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li><strong>SANE installieren:</strong> <code className="text-slate-400">sudo apt install sane sane-utils</code></li>
                    <li><strong>Netzwerkscanner (eSCL/airscan):</strong> <code className="text-slate-400">sudo apt install sane-airscan</code></li>
                    <li>Gerät im gleichen Netzwerk und eingeschaltet?</li>
                    <li>Test im Terminal: <code className="text-slate-400">scanimage -L</code> (kann bei Netzwerkscannern bis zu 45s dauern)</li>
                  </ul>
                  <p className="text-sm mt-2">
                    Die App zeigt unter Control Center → Scanner den SANE-Installationsstatus an.
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Performance-Einstellungen</h3>
                  <p className="text-sm mb-2">
                    <strong>CPU-Governor</strong> wird sofort wirksam. <strong>GPU-Memory, Overclocking</strong> und <strong>Swap-Größe</strong> erfordern einen Neustart.
                  </p>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li>Governor nicht verfügbar? → Kernel unterstützt cpufreq nicht oder läuft als VM.</li>
                    <li>Swap-Größe nicht änderbar? → dphys-swapfile nicht installiert (<code className="text-slate-400">sudo apt install dphys-swapfile</code>).</li>
                    <li>Overclocking: Werte für arm_freq, over_voltage je nach Pi-Modell unterschiedlich.</li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Repository von GitHub aktualisieren (mit lokalen Änderungen)</h3>
                  <p className="text-sm mb-2">
                    Wenn du lokale, uncommittete Änderungen hast und <code className="text-slate-400">git pull</code> Konflikte meldet oder überschreiben würde:
                  </p>
                  <ol className="list-decimal list-inside text-sm space-y-1 ml-4">
                    <li><code className="text-slate-400">git stash push -m "Lokale Änderungen vor pull"</code> – lokale Änderungen zwischenspeichern</li>
                    <li><code className="text-slate-400">git pull</code> – neuesten Stand von GitHub holen</li>
                    <li><code className="text-slate-400">git stash pop</code> – lokale Änderungen wieder anwenden</li>
                  </ol>
                  <p className="text-sm mt-2 mb-2">
                    Bei <strong>Merge-Konflikt</strong> (z. B. in <code className="text-slate-400">Documentation.tsx</code>): Konfliktmarker (<code className="text-slate-400">&lt;&lt;&lt;&lt;&lt;&lt;&lt;</code>, <code className="text-slate-400">=======</code>, <code className="text-slate-400">&gt;&gt;&gt;&gt;&gt;&gt;&gt;</code>) entfernen und entscheiden: Dokumentation oft mit <strong>Remote</strong>-Version (GitHub), andere Dateien mit <strong>lokaler</strong> Version (deine neueren Änderungen). Danach <code className="text-slate-400">git add &lt;Datei&gt;</code> und ggf. <code className="text-slate-400">git stash drop</code>, wenn der Stash nicht mehr gebraucht wird.
                  </p>
                  <p className="text-sm">
                    Details und Workflow für mehrere Entwickler: <code className="bg-slate-700 px-1 rounded">VERSIONING.md</code> im Projekt.
                  </p>
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
              <div className="space-y-4 text-slate-300 dark:text-slate-300">
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Grundlegende Einstellungen</h3>
                  <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                    <li><strong>Sprache:</strong> Deutsch oder Englisch</li>
                    <li><strong>Standard Backup-Ziel:</strong> Verzeichnis für lokale Backups</li>
                    <li><strong>Logging Level:</strong> DEBUG, INFO, WARNING, ERROR</li>
                  </ul>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-white dark:text-white mb-2">Log-Rotation</h3>
                  <p className="text-sm">
                    Logs werden automatisch nach 30 Tagen gelöscht (konfigurierbar). Zusätzlich Rotation nach Größe (2MB pro Tag).
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
              <div className="space-y-4 text-slate-300 dark:text-slate-300">
                <p className="text-sm">Die Versionsnummer folgt dem Schema <strong>X.Y.Z.W</strong>.</p>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li><strong>X:</strong> Gravierende Änderungen</li>
                  <li><strong>Y:</strong> Neue Funktionen</li>
                  <li><strong>Z:</strong> Bereich/Modul fertig</li>
                  <li><strong>W:</strong> Bugfixes, Ergänzungen</li>
                </ul>
                <p className="text-sm">
                  Die Version wird bei <strong>jeder Änderung</strong> angepasst: Bugfix, Ergänzung, Feature-Änderung oder -Ergänzung, relevante Dokumentationsanpassung. Details stehen in <code className="bg-slate-700 px-1 rounded">VERSIONING.md</code> im Projekt.
                </p>
                <div className="mt-4 p-3 bg-sky-900/20 dark:bg-sky-900/20 border border-sky-700/40 dark:border-sky-700/40 rounded-lg">
                  <p className="text-sm font-semibold text-white dark:text-white mb-2">Aktuelle Version: 1.0.1.5</p>
                  <div className="mb-3">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.5</p>
                    <ul className="list-disc list-inside text-xs text-slate-300 dark:text-slate-300 mt-1 ml-4 space-y-1">
                      <li><strong>Dokumentation:</strong> Auf aktuellen Stand gebracht; alle in dieser Session durchgeführten Fehlerbehebungen und Änderungen übernommen</li>
                      <li><strong>Repository aktualisieren:</strong> Workflow bei lokalen Änderungen (git stash, pull, stash pop) in Troubleshooting ergänzt</li>
                      <li><strong>Merge-Konflikt:</strong> Bei Konflikt in Documentation.tsx Remote-Version übernommen; übrige Dateien lokale (neuere) Versionen beibehalten</li>
                      <li><strong>Versionsführung:</strong> VERSIONING.md um Empfehlung „eine Version pro logischer Änderung“ ergänzt</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.4 (28./29. Januar 2026)</p>
                    <ul className="list-disc list-inside text-xs text-slate-300 dark:text-slate-300 mt-1 ml-4 space-y-1">
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
                    <ul className="list-disc list-inside text-xs text-slate-300 dark:text-slate-300 mt-1 ml-4 space-y-1">
                      <li>Control Center – Desktop: Boot-Ziel (Desktop vs. Kommandozeile)</li>
                      <li>Control Center – Display: Auflösung, Bildwiederholrate, Rotation (xrandr)</li>
                      <li>Desktop-App (Tauri): eigenständiges Fenster ohne Browser, gleiches UI</li>
                      <li>Dokumentation: Display-, Desktop- und Desktop-App-Bereich</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.2</p>
                    <ul className="list-disc list-inside text-xs text-slate-300 dark:text-slate-300 mt-1 ml-4 space-y-1">
                      <li>Bugfix: Verschlüsselte Backups korrekt erkannt</li>
                      <li>Bugfix: Cloud-Upload nutzt Cloud-Einstellungen aus Thread</li>
                      <li>Verbesserung: Cloud-Upload-Logging</li>
                    </ul>
                  </div>
                  <div className="mb-3 pt-3 border-t border-sky-700/40 dark:border-sky-700/40">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.1</p>
                    <ul className="list-disc list-inside text-xs text-slate-300 dark:text-slate-300 mt-1 ml-4 space-y-1">
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
                  <h3 className="text-sm font-semibold text-purple-300 dark:text-purple-300 mb-2">Quellen</h3>
                  <ul className="list-disc list-inside text-xs text-slate-300 dark:text-slate-300 space-y-1 ml-2">
                    <li><a href="https://www.raspberrypi.com/documentation/computers/config_txt.html" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">Raspberry Pi config.txt</a></li>
                    <li>Device Tree Overlays, GPIO, Overclocking</li>
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
