# Sicherheits-Matrix – PI-Installer

_Pro Modul: Eingaben, kritische Aktionen, Rechte, Exponierung, Schutz, Härtung, Ampel, Release-Blocker._

| Modul | Bereich | Eingaben | Kritische Aktionen | Rechtebedarf | Exponierung | Aktueller Schutz | Mögliche Härtung | Ampel | Release-Blocker |
|-------|---------|----------|--------------------|--------------|-------------|------------------|------------------|-------|-----------------|
| Dashboard | Frontend/Backend | API-Aufrufe (read) | Keine | lesend | LAN/localhost | CORS, TrustedHost | – | GRÜN | nein |
| SecuritySetup | Frontend/Backend | Firewall-Regeln, Konfiguration | UFW enable/install, Regeln add/delete | sudo | API | run_command, Validierung | Striktere Regel-Validierung, Audit-Log | GELB | nein |
| UserManagement | Frontend/Backend | Username, Passwort, Löschen | useradd, userdel, chpasswd | sudo | API | Sudo-Store, Validierung | Passwortstärke, Rate-Limit create/delete | GELB | nein |
| DevelopmentEnv | Frontend/Backend | Paket-/Tool-Wünsche | apt, pip, npm | sudo | API, developerOnly | experienceLevel developer | Nur für developer sichtbar | GRÜN | nein |
| WebServerSetup | Frontend/Backend | Nginx/Apache-Konfiguration | systemctl, apt install | sudo | API | run_command | Konfig-Validierung vor Schreiben | GELB | nein |
| MailServerSetup | Frontend/Backend | Mail-Konfiguration | Paketinstallation, Konfiguration | sudo | API, developerOnly | developerOnly | – | GRÜN | nein |
| NASSetup | Frontend/Backend | Pfade, Duplikate-Aktionen | mount, move, scan | sudo/User | API | Pfadprüfung | Striktere Pfad-Whitelist, no traversal | GELB | nein |
| HomeAutomationSetup | Frontend/Backend | Suche, Uninstall, Konfiguration | apt, systemctl | sudo | API | – | Eingabe-Validierung | GELB | nein |
| MusicBoxSetup | Frontend/Backend | Mopidy-Konfiguration | apt, systemctl | sudo | API | – | Konfig-Validierung | GELB | nein |
| InstallationWizard | Frontend/Backend | Auswahl, Bestätigung | Umfangreiche Install-Schritte | sudo | API | Bestätigung | Keine zusätzlichen Befehle ohne UI-Schritt | GELB | nein |
| PresetsSetup | Frontend/Backend | Preset-Auswahl | Systemänderungen je Preset | sudo | API | – | Preset-Whitelist, Audit | GELB | nein |
| LearningComputerSetup | Frontend/Backend | Konfiguration | Paketinstallation | sudo | API | – | Validierung | GELB | nein |
| MonitoringDashboard | Frontend/Backend | Konfiguration, Uninstall | Pakete, systemctl | sudo | API | – | – | GRÜN | nein |
| BackupRestore | Frontend/Backend | Ziele, Cloud-Credentials, USB | rsync, tar, mount, Cloud-API | sudo/Netzwerk | API | Pfad-/URL-Validierung | Keine Credentials im Log, Pfad-Sanitization | GELB | nein |
| RaspberryPiConfig | Frontend/Backend | raspi-config-Äquivalente | systemctl, Konfig-Dateien | sudo | API | nur auf Pi | – | GRÜN | nein |
| ControlCenter | Frontend/Backend | WLAN/Display/Bluetooth | wpa_cli, ddccontrol, rfkill | sudo | API | – | Befehls-Whitelist | GELB | nein |
| PeripheryScan | Frontend/Backend | Scan-Auslösung | Hardware-Scan, evtl. USB | User/sudo | API | – | – | GRÜN | nein |
| Documentation | Frontend | – | Keine | – | – | – | – | GRÜN | nein |
| AppStore | Frontend/Backend | App-Installation | apt/Install pro App | sudo | API | App-Whitelist | – | GRÜN | nein |
| PiInstallerUpdate | Frontend/Backend | Install-Trigger | deploy-to-opt, ggf. apt | sudo | API | can_run_deploy Prüfung | Kompatibilitäts-Gate, nur bei Freigabe Build | GELB→GRÜN | nein (nach Gate) |
| RemoteView / Remote | Frontend/Backend | Pairing, Sessions, Aktionen | Remote-Ausführung, QR, Tokens | User/API | API, WebSocket | Pairing, Permissions-Modell | Token-Rotation, Audit | GELB | nein |
| DSI/Radio | Frontend/Backend | Stream-URLs, Favoriten, Theme | Datei-/Konfig-Schreibzugriff | User | API | – | URL-Validierung, Pfad-Whitelist | GELB | nein |
| Backend Core / API | Backend | Alle Request-Bodies, Query, Headers | run_command, sudo, Datei-IO | variabel | Netzwerk (localhost/LAN) | TrustedHost, CORS, CSP, HSTS | Host-Validierung, weniger shell=True | GELB | nein |
| Self-Update (API) | Backend | POST install | deploy-to-opt.sh | sudo | API | can_run_deploy | Gate: Kompatibilität vor Build/Deploy | GELB | nein |
| Deploy-/Install-Skripte | Scripts | ENV, Argumente | sudo, apt, dpkg, rsync | root/sudo | CLI/Backend-Aufruf | Keine Netzwerk-Exposition | Keine unsicheren Parameter von außen | GELB | nein |
| Debian Packaging | debian/ | control, rules, postinst | dpkg-buildpackage, apt install | root | Build-Umgebung | Reproduzierbar | Changelog/Versions-Gate | GRÜN | nein |
| Services / systemd | systemd | Unit-Dateien | Daemon-Start | root | System | ProtectHome, RestrictAddressFamilies, etc. | ReadOnlyPaths wo möglich | GRÜN | nein |
| SudoPasswordDialog | Frontend/Backend | Passwort | POST /api/users/sudo-password | – | API | Verschlüsselung, Store | Rate-Limit (vorhanden), kein Log | GRÜN | nein |
| Logs (API) | Backend | Pfad, Zeilen | Datei lesen | User | API | Pfad aus Konfig | Kein User-Pfad, nur fester Log-Pfad | GELB | nein |

---

## Legende

- **Ampel:** ROT = kritisch/Release-Blocker, GELB = relevant/vor Release beheben, GRÜN = ausreichend/Restverbesserungen.
- **Release-Blocker:** ja = muss vor Release behoben sein; aktuell kein Modul als ROT/Blockierend eingestuft, sofern Kompatibilitäts-Gate für Update-Modul umgesetzt wird.
