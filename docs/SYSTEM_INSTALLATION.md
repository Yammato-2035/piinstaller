# Setuphelfer – Systemweite Installation

Diese Anleitung beschreibt die systemweite Installation des **Setuphelfer** (Konfigurations-Assistent) gemäß Linux Filesystem Hierarchy Standard (FHS). Das Git-Repository heißt weiterhin *piinstaller*; Laufzeitpfade und Paketname lauten **setuphelfer** (ab Version 1.4.0).

## Übersicht

Nach der Installation werden typischerweise folgende Verzeichnisse verwendet:

| Verzeichnis | Zweck | Inhalt |
|------------|-------|--------|
| `/opt/setuphelfer/` | Hauptprogramm | Alle Programmdateien, Backend, Frontend |
| `/etc/setuphelfer/` | Konfiguration | Konfigurationsdateien |
| `/var/log/setuphelfer/` | Logs | Log-Dateien |
| `/var/lib/setuphelfer/` | Zustand | Laufzeitdaten |
| `/usr/local/bin/` | Symlinks | Befehle wie `setuphelfer`, `setuphelfer-backend` |
| `/etc/systemd/system/` | Service | systemd-Unit-Dateien |

**Legacy (Migration vor 1.4.0):** `/opt/pi-installer`, `/etc/pi-installer` usw. – siehe Changelog und DEB-Feld `Replaces:`.

### Repo vs. Installationsverzeichnis

- **Entwicklungsverzeichnis (Repo):** z. B. `/home/…/PI-Installer` – Quelle, Git, Builds
- **Installationsverzeichnis:** `/opt/setuphelfer` – installierte Laufzeit

Umgebungsvariablen **`SETUPHELFER_*`** und (kompatibel) **`PI_INSTALLER_*`** zeigen auf die Installation. Das Backend nutzt sie für Version (`VERSION`) und Pfade.

## Voraussetzungen

- Raspberry Pi OS oder Debian-basiertes System
- Root/Sudo-Zugriff
- Internetverbindung
- Python 3.9+ (wird automatisch installiert)
- Node.js/npm (wird automatisch installiert)

## Installation

### Option 1: Aus dem Repository (empfohlen)

```bash
cd /path/to/PI-Installer
sudo ./scripts/install-system.sh
```

### Option 2: Direkt von GitHub

```bash
curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/install-system.sh | sudo bash
```

**Hinweis:** Das offizielle Repository ist `Yammato-2035/piinstaller`. Bei einem Fork passen Sie die URL entsprechend an.

### Dedizierter Service-User (empfohlen für Produktion)

```bash
PI_INSTALLER_USE_SERVICE_USER=1 sudo ./scripts/install-system.sh
```

Das Skript legt den System-User **`setuphelfer`** an (falls noch nicht vorhanden): ohne Login-Shell, ohne Home unter `/home` im Standard-DEB-Setup.

### Service unter bestimmtem Benutzer

```bash
PI_INSTALLER_USER=meinuser sudo ./scripts/install-system.sh
```

Ohne diese Variablen wird der Benutzer verwendet, der `sudo` ausführt (`SUDO_USER`).

### Update aus der App (Deploy nach /opt)

1. Im Menü **Setuphelfer Update** (bzw. Repo-Modus: entsprechender Eintrag) öffnen.
2. **„Jetzt nach /opt installieren“** / **„Jetzt aktualisieren“** – Quelle und Ziel `/opt/setuphelfer` prüfen.

**Sudo ohne Passwort (optional):** siehe Hinweise in der App oder `sudo visudo` nur für `scripts/deploy-to-opt.sh`.

## Was wird installiert?

1. **System-Abhängigkeiten** – Python venv, Node, Git, curl, …
2. **Programmdateien** nach `/opt/setuphelfer/`
3. **Konfiguration** unter `/etc/setuphelfer/`
4. **Symlinks** in `/usr/local/bin/`:
   - `setuphelfer` → Starter (Tauri/Browser-Auswahl)
   - `setuphelfer-backend` → nur Backend
   - `setuphelfer-frontend` → nur Frontend-Skript
   - `setuphelfer-start` → `start.sh`
   - `setuphelfer-scripts` → `scripts/`
5. **Umgebungsvariablen** in `/etc/profile.d/setuphelfer.sh` (und Legacy-Kompatibilität)
6. **systemd:** `setuphelfer-backend.service`, `setuphelfer.service`
7. **Startmenü:** **SetupHelfer** und **SetupHelfer (Browser)** unter `/usr/share/applications/`

## Verwendung

### Startmenü

- **SetupHelfer** – Starter mit Backend-Prüfung, Auswahl Tauri/Browser/Backend
- **SetupHelfer (Browser)** – öffnet die Weboberfläche (Port 3001; Backend muss laufen)

Falls Einträge fehlen:

```bash
sudo /opt/setuphelfer/scripts/install-desktop-entries.sh /opt/setuphelfer
```

### Befehle (nach Installation)

```bash
setuphelfer              # Kombi-Starter (wie oben)
setuphelfer-backend      # Nur Backend
setuphelfer-frontend     # Nur Frontend-Skript
setuphelfer-start        # start.sh
```

### Service-Verwaltung

```bash
sudo systemctl status setuphelfer-backend setuphelfer
sudo systemctl restart setuphelfer-backend setuphelfer
sudo journalctl -u setuphelfer -u setuphelfer-backend -f
```

Die **Web-UI** (`setuphelfer.service`) benötigt das **Backend** (`setuphelfer-backend.service`) auf Port **8000**.

## Zugriff

- **Web-Interface:** http://localhost:3001  
- **API:** http://localhost:8000  
- **API-Dokumentation:** http://localhost:8000/docs  

## Update

```bash
cd /path/to/PI-Installer
sudo ./scripts/update-system.sh
```

Das Skript aktualisiert `/opt/setuphelfer` (oder Legacy `/opt/pi-installer`, falls nur diese Installation existiert), legt ein Backup an und startet die passenden Services neu.

## Deinstallation

### Installation per .deb-Paket

```bash
sudo apt purge setuphelfer
```

*(Legacy-Paketname: `pi-installer` &lt; 1.4.0.)*

### Manuelle Installation (`install-system.sh` / `deploy-to-opt.sh`)

```bash
sudo /pfad/zum/piinstaller/scripts/uninstall-system.sh
```

Entfernt u. a. Units, Symlinks **`setuphelfer*`**, Desktop-Dateien **`setuphelfer*.desktop`**, Verzeichnisse unter `/opt/setuphelfer`, `/etc/setuphelfer`, `/var/log/setuphelfer`, `/var/lib/setuphelfer`, optional den User **`setuphelfer`**.

## Umgebungsvariablen

In `/etc/profile.d/setuphelfer.sh` gesetzt, u. a.:

```bash
export SETUPHELFER_DIR="/opt/setuphelfer"
export PI_INSTALLER_DIR="/opt/setuphelfer"
export SETUPHELFER_CONFIG_DIR="/etc/setuphelfer"
export SETUPHELFER_LOG_DIR="/var/log/setuphelfer"
```

Sofort laden: `source /etc/profile.d/setuphelfer.sh`

## Konfiguration

Hauptkonfiguration: `/etc/setuphelfer/config.json` (Runtime liest JSON).

Beispielstruktur (Auszug):

```json
{
  "install_dir": "/opt/setuphelfer",
  "config_dir": "/etc/setuphelfer",
  "log_dir": "/var/log/setuphelfer",
  "backend": {"host": "0.0.0.0", "port": 8000},
  "frontend": {"port": 3001}
}
```

## Logs

- Verzeichnis: `/var/log/setuphelfer/`
- systemd: `journalctl -u setuphelfer-backend -u setuphelfer`

## Fehlerbehebung

### Service startet nicht

```bash
sudo systemctl status setuphelfer-backend setuphelfer
sudo journalctl -u setuphelfer-backend -n 80 --no-pager
sudo lsof -i :8000
sudo lsof -i :3001
```

### Backend / Venv unter `/opt/setuphelfer`

Venv liegt unter `/opt/setuphelfer/backend/venv`. Bei dediziertem User **`setuphelfer`**:

```bash
sudo -u setuphelfer bash -c 'cd /opt/setuphelfer/backend && ./venv/bin/pip install -r requirements.txt'
sudo systemctl restart setuphelfer-backend
```

### Frontend / Produktiv vs. Dev

Wenn Journal **EACCES** unter `node_modules/.vite` zeigt: keine **`npm run dev`**-Unit unter `/opt` – siehe `docs/BETRIEB_REPO_VS_SERVICE.md` und `scripts/start-browser-production.sh`.

### Frontend manuell testen

```bash
cd /opt/setuphelfer/frontend
npm run dev
```

## Sicherheit

Der systemd-Service kann u. a. folgende Optionen nutzen (je nach Unit-Datei):

- `NoNewPrivileges=true`
- `PrivateTmp=true`
- `ProtectSystem=strict`
- `ProtectHome=…`
- `ReadWritePaths=…`

## Zielsystem prüfen (Phase F)

Nach der Installation: **`./scripts/verify-setuphelfer-install.sh`** (systemd, API, optional Journal) – siehe **`docs/VERIFY_TARGET_SYSTEM.md`**.

## Weitere Informationen

- [Haupt-README](../README.md)
- [Schnellstart-Anleitung](./user/QUICKSTART.md)
- [Startoptionen](START_APPS.md)
