# PI-Installer – Systemweite Installation

Diese Anleitung beschreibt die systemweite Installation des PI-Installers gemäß Linux Filesystem Hierarchy Standard (FHS).

## Übersicht

Nach der Installation werden folgende Verzeichnisse verwendet:

| Verzeichnis | Zweck | Inhalt |
|------------|-------|--------|
| `/opt/pi-installer/` | Hauptprogramm | Alle Programmdateien, Backend, Frontend |
| `/etc/pi-installer/` | Konfiguration | Konfigurationsdateien |
| `/var/log/pi-installer/` | Logs | Log-Dateien |
| `/usr/local/bin/` | Symlinks | Befehle wie `pi-installer`, `pi-installer-backend` |
| `/etc/systemd/system/` | Service | systemd Service-Datei |

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
curl -sSL https://raw.githubusercontent.com/IHR-USERNAME/PI-Installer/main/scripts/install-system.sh | sudo bash
```

**Hinweis:** Ersetzen Sie `IHR-USERNAME` durch den tatsächlichen GitHub-Benutzernamen.

## Was wird installiert?

1. **System-Abhängigkeiten**
   - Python 3.9+ mit venv und pip
   - Node.js und npm
   - Git, curl, wget, build-essential

2. **Programmdateien**
   - Alle Dateien nach `/opt/pi-installer/`
   - Backend mit Python Virtual Environment
   - Frontend mit npm Dependencies

3. **Konfiguration**
   - Konfigurationsverzeichnis `/etc/pi-installer/`
   - Standard-Konfigurationsdatei

4. **Symlinks**
   - `pi-installer` → Startet PI-Installer (Backend + Frontend)
   - `pi-installer-backend` → Startet nur Backend
   - `pi-installer-frontend` → Startet nur Frontend
   - `pi-installer-start` → Startet beide Services

5. **Umgebungsvariablen**
   - Automatisch in `/etc/profile.d/pi-installer.sh`
   - Werden beim nächsten Login geladen

6. **systemd Service**
   - Service-Datei: `/etc/systemd/system/pi-installer.service`
   - Optional: Automatischer Start beim Booten

## Verwendung

### Befehle

Nach der Installation können Sie PI-Installer von überall starten:

```bash
# Hauptbefehl (startet Backend + Frontend)
pi-installer

# Nur Backend
pi-installer-backend

# Nur Frontend
pi-installer-frontend

# Beide Services
pi-installer-start
```

### Service-Verwaltung

```bash
# Status prüfen
sudo systemctl status pi-installer

# Starten
sudo systemctl start pi-installer

# Stoppen
sudo systemctl stop pi-installer

# Aktivieren (startet beim Booten)
sudo systemctl enable pi-installer

# Deaktivieren
sudo systemctl disable pi-installer

# Logs anzeigen
sudo journalctl -u pi-installer -f
```

### Zugriff

- **Web-Interface:** http://localhost:3001
- **API:** http://localhost:8000
- **API-Dokumentation:** http://localhost:8000/docs

## Update

Um eine bestehende Installation zu aktualisieren:

```bash
cd /path/to/PI-Installer
sudo ./scripts/update-system.sh
```

Das Update-Skript:
- Stoppt den Service (falls aktiv)
- Erstellt ein Backup
- Aktualisiert alle Dateien
- Aktualisiert Dependencies
- Startet den Service wieder (falls er vorher lief)

## Deinstallation

Um PI-Installer zu deinstallieren:

```bash
# Service stoppen und deaktivieren
sudo systemctl stop pi-installer
sudo systemctl disable pi-installer

# Dateien entfernen
sudo rm -rf /opt/pi-installer
sudo rm -rf /etc/pi-installer
sudo rm -rf /var/log/pi-installer

# Symlinks entfernen
sudo rm -f /usr/local/bin/pi-installer
sudo rm -f /usr/local/bin/pi-installer-backend
sudo rm -f /usr/local/bin/pi-installer-frontend
sudo rm -f /usr/local/bin/pi-installer-start
sudo rm -f /usr/local/bin/pi-installer-scripts

# Service-Datei entfernen
sudo rm -f /etc/systemd/system/pi-installer.service
sudo systemctl daemon-reload

# Umgebungsvariablen entfernen
sudo rm -f /etc/profile.d/pi-installer.sh
```

## Umgebungsvariablen

Die folgenden Umgebungsvariablen werden automatisch gesetzt:

```bash
export PI_INSTALLER_DIR="/opt/pi-installer"
export PI_INSTALLER_CONFIG_DIR="/etc/pi-installer"
export PI_INSTALLER_LOG_DIR="/var/log/pi-installer"
export PATH="$PI_INSTALLER_DIR/scripts:$PATH"
```

Diese werden in `/etc/profile.d/pi-installer.sh` gesetzt und beim nächsten Login automatisch geladen.

Um sie sofort zu laden (ohne Neuanmeldung):

```bash
source /etc/profile.d/pi-installer.sh
```

## Konfiguration

Die Konfigurationsdatei befindet sich in `/etc/pi-installer/config.yaml`.

Standard-Konfiguration:

```yaml
install_dir: /opt/pi-installer
config_dir: /etc/pi-installer
log_dir: /var/log/pi-installer

backend:
  host: 0.0.0.0
  port: 8000

frontend:
  port: 3001
```

## Logs

Logs werden in `/var/log/pi-installer/` gespeichert.

Zusätzlich können Sie systemd-Logs verwenden:

```bash
# Alle Logs
sudo journalctl -u pi-installer

# Letzte 100 Zeilen
sudo journalctl -u pi-installer -n 100

# Live-Logs
sudo journalctl -u pi-installer -f
```

## Fehlerbehebung

### Service startet nicht

```bash
# Prüfe Status
sudo systemctl status pi-installer

# Prüfe Logs
sudo journalctl -u pi-installer -n 50

# Prüfe ob Ports belegt sind
sudo lsof -i :8000
sudo lsof -i :3001
```

### Umgebungsvariablen werden nicht geladen

```bash
# Manuell laden
source /etc/profile.d/pi-installer.sh

# Oder neu anmelden
```

### Backend startet nicht

```bash
# Prüfe Python-Version
python3 --version

# Prüfe venv
ls -la /opt/pi-installer/backend/venv

# Manuell testen
cd /opt/pi-installer/backend
source venv/bin/activate
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
```

### Frontend startet nicht

```bash
# Prüfe Node.js-Version
node --version
npm --version

# Prüfe Dependencies
ls -la /opt/pi-installer/frontend/node_modules

# Manuell testen
cd /opt/pi-installer/frontend
npm run dev
```

## Sicherheit

Der systemd Service verwendet folgende Sicherheitseinstellungen:

- `NoNewPrivileges=true` - Verhindert Privilege-Escalation
- `PrivateTmp=true` - Isolierte temporäre Dateien
- `ProtectSystem=strict` - Schreibschutz für System-Verzeichnisse
- `ProtectHome=read-only` - Schreibschutz für Home-Verzeichnisse
- `ReadWritePaths` - Nur spezifische Pfade sind beschreibbar

## Weitere Informationen

- [Haupt-README](../README.md)
- [Schnellstart-Anleitung](../QUICKSTART.md)
- [Installationsanleitung](../INSTALL.md)
- [Startoptionen](START_APPS.md)
