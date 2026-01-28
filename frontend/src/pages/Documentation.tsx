import React, { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BookOpen, Cloud, HardDrive, Settings, Cpu } from 'lucide-react'

type SectionId = 'backup-restore' | 'cloud' | 'control-center' | 'raspberry-pi-config' | 'einstellungen' | 'versionen'

const SECTIONS: { id: SectionId; label: string; icon: React.ElementType }[] = [
  { id: 'backup-restore', label: 'Backup & Restore', icon: HardDrive },
  { id: 'cloud', label: 'Cloud-Einstellungen', icon: Cloud },
  { id: 'control-center', label: 'Control Center', icon: Settings },
  { id: 'raspberry-pi-config', label: 'Raspberry Pi Config', icon: Cpu },
  { id: 'einstellungen', label: 'Einstellungen', icon: Settings },
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
                      <li><strong>Drucker:</strong> Drucker verwalten (in Entwicklung)</li>
                      <li><strong>Performance, Maus, Taskleiste, Theme:</strong> in Entwicklung</li>
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
                Versionsnummern-Schema
              </h2>
              <div className="space-y-4 text-slate-300 dark:text-slate-300">
                <p className="text-sm">Die Versionsnummer folgt dem Schema <strong>X.Y.Z.W</strong>.</p>
                <ul className="list-disc list-inside text-sm space-y-1 ml-4">
                  <li><strong>X:</strong> Gravierende Änderungen</li>
                  <li><strong>Y:</strong> Neue Funktionen</li>
                  <li><strong>Z:</strong> Bereich/Modul fertig</li>
                  <li><strong>W:</strong> Bugfixes, Ergänzungen</li>
                </ul>
                <div className="mt-4 p-3 bg-sky-900/20 dark:bg-sky-900/20 border border-sky-700/40 dark:border-sky-700/40 rounded-lg">
                  <p className="text-sm font-semibold text-white dark:text-white mb-2">Aktuelle Version: 1.0.1.3</p>
                  <div className="mb-3">
                    <p className="text-xs font-semibold text-sky-300 dark:text-sky-300 mb-1">1.0.1.3</p>
                    <ul className="list-disc list-inside text-xs text-slate-300 dark:text-slate-300 mt-1 ml-4 space-y-1">
                      <li>Control Center – Desktop: Boot-Ziel (Desktop vs. Kommandozeile)</li>
                      <li>Control Center – Display: Auflösung, Bildwiederholrate, Rotation (xrandr)</li>
                      <li>Dokumentation: Display- und Desktop-Bereiche aktualisiert</li>
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
