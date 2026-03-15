# Modulinventur – PI-Installer Security Review

_Stand: Vollständiges modulares Security-Review. Repository-basiert._

---

## 1. Hauptmodule (fachlich)

Aus **frontend/src/App.tsx** und **Sidebar**:

| Modul | Seite (Page) | Menü | Bereich (basic/advanced/developer) |
|-------|--------------|------|-----------------------------------|
| Dashboard | dashboard | Start | basic |
| SecuritySetup | security | Sicherheit | advanced |
| UserManagement | users | Benutzer | advanced |
| DevelopmentEnv | devenv | Dev-Umgebung | advanced, developerOnly |
| WebServerSetup | webserver | Webserver | advanced |
| MailServerSetup | mailserver | Mailserver | advanced, developerOnly |
| NASSetup | nas | NAS | advanced |
| HomeAutomationSetup | homeautomation | Hausautomatisierung | advanced |
| MusicBoxSetup | musicbox | Musikbox | advanced |
| KinoStreaming | kino-streaming | Kino/Streaming | advanced |
| InstallationWizard | wizard | Setup-Assistent | basic |
| PresetsSetup | presets | Voreinstellungen | advanced |
| LearningComputerSetup | learning | Lerncomputer | advanced |
| MonitoringDashboard | monitoring | Systemstatus | basic |
| BackupRestore | backup | Backup | basic |
| RaspberryPiConfig | raspberry-pi-config | Raspberry Pi Config | advanced (nur wenn Pi) |
| ControlCenter | control-center | Control Center | advanced |
| PeripheryScan | periphery-scan | Peripherie-Scan | advanced |
| SettingsPage | settings | Einstellungen | advanced/diagnose |
| Documentation | documentation | Hilfe | basic |
| AppStore | app-store | Apps | basic |
| PiInstallerUpdate | pi-installer-update | PI-Installer Update | advanced |
| TFTPage | tft | (TFT) | – |
| DsiRadioSettings | dsi-radio-settings | DSI-Radio Einstellungen | basic/advanced (wenn Freenove) |
| RemoteView | remote | Linux Companion | advanced |
| FirstRunWizard | – | (Onboarding) | – |
| SudoPasswordDialog | – | (global) | – |
| RunningBackupModal | – | (global) | – |

**Erfahrungsstufen (experienceLevel):** beginner | advanced | developer.  
**UIMode (Sidebar):** basic | advanced | diagnose. developerOnly-Einträge nur bei experienceLevel === 'developer'.

---

## 2. Backend – Endpunkte nach Bereich

Aus **backend/app.py** (und api/routes/*):

- **System/Init:** /api/system-info, /api/version, /api/init/status, /api/settings (get/post), /api/system/paths, /api/system/network, /api/system/freenove-detection, /api/system/resources, /api/system/installed-packages, /api/system/running-processes, /api/system/security-config, /api/system/updates, /api/system/run-update-in-terminal, /api/system/run-mixer, /api/system/install-mixer-packages, /api/system/asus-rog/*, /health, /api/status.
- **Logs:** /api/logs/path, /api/logs/tail.
- **Self-Update:** /api/self-update/status, /api/self-update/install (POST).
- **Users:** /api/users, /api/user-profile, /api/users/sudo-password/check, /api/users/sudo-password (POST), /api/users/create (POST), /api/users/{username} (DELETE).
- **Security:** /api/security/scan, /api/security/status, /api/security/firewall/* (enable, install, rules, add, delete), /api/security/configure.
- **Dashboard:** /api/dashboard/services-status.
- **Webserver:** /api/webserver/status, /api/webserver/configure.
- **NAS:** /api/nas/status, /api/nas/configure, /api/nas/duplicates/*.
- **HomeAutomation:** /api/homeautomation/status, search, uninstall, configure.
- **MusicBox:** /api/musicbox/status, mopidy-diagnose, configure.
- **Devenv:** /api/devenv/status.
- **Install:** /api/install/start, /api/install/progress.
- **Learning:** /api/learning/status, configure.
- **Monitoring:** /api/monitoring/status, configure, uninstall.
- **Peripherals:** /api/peripherals/scan.
- **Backup:** /api/backup/jobs, status, settings, schedule/run-now, cloud/*, targets, target-check, clone, usb/*.
- **Apps:** /api/apps, /api/apps/{id}/status, /api/apps/{id}/install.
- **Radio/DSI:** /api/radio/* (stream-metadata, logo, stream, stations/search, dsi-theme, dsi-config/*).
- **Debug:** /api/debug/routes.
- **Remote (API):** api/routes/pairing, sessions, devices, modules, actions, ws.

---

## 3. Module mit Systembefehlen / Shell / Paketinstallation / Dateischreibvorgänge

| Modul/Bereich | Art | Beispiele (Dateien/Stellen) |
|---------------|-----|------------------------------|
| Backend app.py | subprocess.run/Popen, run_command | run_command(..., sudo=True), apt-get, ufw, systemctl, useradd, chpasswd, hostname, curl, git |
| modules/backup.py | run_command, Datei-/Cloud-IO | rsync, tar, mount, Cloud-Upload |
| modules/security.py | Firewall, Konfiguration | ufw enable/rules, configure |
| modules/users.py | Benutzer anlegen/löschen | useradd, userdel, chpasswd |
| modules/control_center.py | WLAN, Display, Bluetooth | wpa_cli, ddccontrol, rfkill |
| modules/webserver.py | Nginx/Apache | systemctl, apt |
| modules/devenv.py | Paketinstallation | apt, pip, npm |
| Install/InstallationWizard | /api/install/start | umfangreiche Befehle über run_command |
| Self-Update | deploy-to-opt.sh | sudo, rsync/copy nach /opt |
| Scripts | viele .sh | create_installer.sh, deploy-to-opt.sh, install-system.sh, build-deb.sh, release-service.sh mit sudo/apt/dpkg |

---

## 4. Module mit sudo / root-nahen Rechten

- **Backend:** run_command(..., sudo=True) nutzt sudo_password (aus Request oder verschlüsseltem Store). Betroffen: Firewall, Benutzer, Paketinstallation, Mixer, UFW, systemctl, deploy.
- **Scripts:** create_installer.sh, install-system.sh, install-backend-service.sh, deploy-to-opt.sh, build-deb.sh (dpkg-buildpackage), release-service.sh (apt install .deb) – teilweise mit sudo.
- **debian/postinst:** legt User an, systemd aktivieren, Verzeichnisse anlegen – läuft bei apt install als root.

---

## 5. Angriffsfläche (Netzwerk, Dateien, externe Prozesse, Benutzereingaben)

| Quelle | Risiko |
|--------|--------|
| **Netzwerk** | Backend standardmäßig 127.0.0.1; CORS eingeschränkt; TrustedHost; bei ALLOW_REMOTE_ACCESS Host-Erweiterung. API ohne Authentifizierung (LAN/VPN-Modell). |
| **Dateien** | Pfade aus Request (Backup-Ziele, Cloud-Pfade, NAS-Pfade). Teilweise Validierung/sanitization; Risiko Path-Traversal wo Pfade direkt genutzt werden. |
| **Externe Prozesse** | subprocess mit Nutzerdaten (z. B. Befehle, Paketnamen). Einige Stellen mit shell=True (dokumentiert); Listen-Aufrufe wo umgesetzt. |
| **Benutzereingaben** | JSON Body (Passwörter, Usernames, Regeln, URLs). Sudo-Passwort verschlüsselt im Store; Rate-Limit auf sudo-Password-Endpoint. Validierung je Endpoint unterschiedlich. |

---

## 6. Weitere Strukturen

- **scripts/:** 132+ Shell-Skripte (Install, Deploy, Audio/DSI/HDMI, Diagnose, Backup). Kritisch für Release/Deploy: create_installer.sh, deploy-to-opt.sh, install-system.sh, build-deb.sh, release-service.sh.
- **debian/:** control, changelog, rules, postinst, postrm, prerm, Service-Datei, Desktop-Dateien, pi-installer.sh (ENV).
- **Dockerfile:** Backend-Image; docker-compose: Backend expose, Frontend ports 3001.
- **systemd:** pi-installer-backend.service, pi-installer.service (kombiniert); Härtung bereits ergänzt.
- **config/:** version.json (einzige Versionsquelle); ggf. weitere Konfiguration unter /etc/pi-installer.
- **.github/workflows/:** ci.yml, security.yml, build-image.yml, release-deb.yml.

---

## 7. Zählung Hauptmodule (für Lagemeldung)

- **Frontend-Seiten (fachliche Module):** 24 (inkl. TFTPage, DsiRadioSettings, RemoteView).
- **Backend-API-Bereiche:** System, Logs, Self-Update, Users, Security, Dashboard, Webserver, NAS, HomeAutomation, MusicBox, Devenv, Install, Learning, Monitoring, Peripherals, Backup, Apps, Radio/DSI, Debug, Remote-Routes.
- **Kritische Scripts (Deploy/Install/Packaging):** create_installer.sh, deploy-to-opt.sh, install-system.sh, build-deb.sh, release-service.sh, uninstall-system.sh, install-backend-service.sh.
- **Systemd-Units:** 2 (Backend, kombiniert).
- **Packaging:** debian/* (11 Dateien), Dockerfile, docker-compose.yml.
