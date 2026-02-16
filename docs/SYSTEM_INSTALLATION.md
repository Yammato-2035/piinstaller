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
curl -sSL https://raw.githubusercontent.com/Yammato-2035/piinstaller/main/scripts/install-system.sh | sudo bash
```

**Hinweis:** Das offizielle Repository ist `Yammato-2035/piinstaller`. Bei einem Fork passen Sie die URL entsprechend an.

### Dedizierter Service-User (empfohlen für Produktion)

Die App unter einem **eigenen System-User** zu betreiben, ist sicherer (Least Privilege) und üblich für Dienste:

- Kein Zugriff auf Home-Verzeichnisse oder andere User-Daten
- Bei Kompromittierung ist der Schaden begrenzt
- Klare Trennung: Dienst ≠ Ihr Login

```bash
PI_INSTALLER_USE_SERVICE_USER=1 sudo ./scripts/install-system.sh
```

Das Skript legt dabei den User `pi-installer` an (falls noch nicht vorhanden): system-User ohne Login-Shell, ohne Home. Der Service und alle zugehörigen Dateien laufen unter diesem User.

### Service unter bestimmtem Benutzer (z. B. volker)

Wenn der Service unter Ihrem normalen Benutzer laufen soll (z. B. `volker`):

```bash
PI_INSTALLER_USER=volker sudo ./scripts/install-system.sh
```

Ohne diese Variablen wird der Benutzer verwendet, der `sudo` ausführt (`SUDO_USER`).

### Update aus der App (Deploy nach /opt)

Wenn Sie aus einem **Entwicklungsverzeichnis** (z. B. `/home/volker/piinstaller`) arbeiten, können Sie die aktuelle Version direkt aus dem PI-Installer heraus nach `/opt/pi-installer` installieren bzw. aktualisieren:

1. Im Menü **PI-Installer Update** öffnen.
2. Dort werden Quelle (aktuelles Repo) und Installation unter `/opt` angezeigt.
3. **„Jetzt nach /opt installieren“** bzw. **„Jetzt aktualisieren“** klicken.

Das Deploy-Skript `scripts/deploy-to-opt.sh` kopiert die Dateien nach `/opt`, legt den Service-User `pi-installer` an (falls nötig), setzt die Berechtigungen und startet den systemd-Service neu.

**Sudo ohne Passwort (optional):** Wenn der Klick „Jetzt installieren“ ohne weitere Eingabe funktionieren soll, können Sie dem Benutzer, unter dem das Backend läuft, erlauben, nur dieses Skript mit sudo auszuführen:

```bash
# Ersetzen Sie /home/volker/piinstaller durch Ihr Entwicklungsverzeichnis und volker durch Ihren Benutzer.
sudo visudo -f /etc/sudoers.d/pi-installer-deploy
```

Inhalt (eine Zeile):

```
volker ALL=(ALL) NOPASSWD: /home/volker/piinstaller/scripts/deploy-to-opt.sh *
```

Ohne diese Regel zeigt die App nach Klick auf „Jetzt installieren“ den auszuführenden Befehl an; Sie können ihn im Terminal ausführen.

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

7. **Startmenü / Anwendungen**
   - Einträge in `/usr/share/applications/`: **PI-Installer** und **PI-Installer (im Browser)** erscheinen im Anwendungsmenü aller Benutzer.

## Verwendung

### Startmenü

Nach der Installation erscheinen im **Anwendungsmenü** (Startmenü) aller Benutzer:

- **PI-Installer** – startet das Startskript (Backend prüfen, dann Auswahl Tauri/Browser/Frontend)
- **PI-Installer (im Browser)** – öffnet das Frontend im Standard-Browser (Backend muss laufen)

Falls die Einträge fehlen (z. B. bei älteren Installationen), einmal ausführen – **aus dem Repo** (damit das Skript existiert):

```bash
# Ersetzen Sie /pfad/zum/piinstaller durch Ihr Projektverzeichnis (z. B. /home/volker/piinstaller)
sudo /pfad/zum/piinstaller/scripts/install-desktop-entries.sh /opt/pi-installer
```

Wenn das Skript bereits unter /opt liegt (nach neuer Installation oder Deploy):

```bash
sudo /opt/pi-installer/scripts/install-desktop-entries.sh
```

### Befehle

Nach der Installation können Sie PI-Installer zusätzlich von der Kommandozeile starten:

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

### Backend startet nicht (obwohl Service installiert ist)

1. **Service-Status und Logs prüfen** (häufigste Ursachen stehen in den Logs):
   ```bash
   sudo systemctl status pi-installer
   sudo journalctl -u pi-installer -n 80 --no-pager
   ```

2. **Typische Ursachen:**
   - **Venv/Pip:** Beim ersten Start erstellt der Service die Venv unter `/opt/pi-installer/backend/venv`. Mit `ProtectHome=read-only` darf Pip nicht in `~/.cache` schreiben. Falls die Venv fehlt oder defekt ist, als Service-Benutzer einmal manuell anlegen (bei dediziertem Service-User: `pi-installer`, sonst der gewählte User, z. B. `volker`):
     ```bash
     sudo -u pi-installer bash -c 'cd /opt/pi-installer/backend && python3 -m venv venv && ./venv/bin/pip install -r requirements.txt'
     ```
     Danach: `sudo systemctl restart pi-installer`
   - **Falscher Installationspfad:** Prüfen, ob die Service-Datei den richtigen Pfad hat: `grep -E "WorkingDirectory|ExecStart" /etc/systemd/system/pi-installer.service` (sollte z. B. `/opt/pi-installer` und `…/start.sh` zeigen).
   - **Port 8000 belegt:** `ss -tlnp | grep 8000` oder `lsof -iTCP:8000 -sTCP:LISTEN`. Ein anderer Prozess muss ggf. beendet werden.

3. **Backend manuell testen** (ohne Service):
   ```bash
   # Python-Version
   python3 --version

   # Venv prüfen
   ls -la /opt/pi-installer/backend/venv

   # Manuell starten (als gleicher User wie der Service)
   cd /opt/pi-installer/backend
   ./venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
   ```
   Wenn das manuell funktioniert, der Service aber nicht, liegen die Ursachen meist bei systemd (Pfade, Rechte, ProtectHome/ReadWritePaths).

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
