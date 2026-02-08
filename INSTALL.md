# PI-Installer - Installationsanleitung

## Voraussetzungen

- Raspberry Pi 4 oder besser (empfohlen: 8GB RAM)
- Raspberry Pi OS (Debian-basiert) - aktuell installiert
- SSH-Zugriff auf den Pi
- Internetzugang
- Root/Sudo-Zugriff

## Schnellstart

### One-Click Installation (empfohlen)

```bash
curl -sSL https://raw.githubusercontent.com/IHR-USERNAME/PI-Installer/main/scripts/create_installer.sh | bash
```

Ersetzen Sie `IHR-USERNAME` durch den GitHub-Repository-Besitzer. Alternativ (wenn eingerichtet): `curl -sSL https://get.pi-installer.io | bash`

Das Skript prüft Python/Node, klont das Repo (falls nötig), richtet Backend und Frontend ein und aktiviert den systemd-Service. Am Ende wird die Zugangs-URL angezeigt (z. B. `http://<IP>:3001`).

---

### Manuelle Installation

### 1. Repository klonen

```bash
cd ~
git clone <repository-url>
cd PI-Installer
```

### 2. Backend starten

```bash
# Python 3.9+ virtuelle Umgebung
cd backend
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt

# Server starten (Port 8000)
python3 app.py
```

### 3. Frontend starten (in neuem Terminal)

```bash
cd frontend

# Node.js dependencies
npm install

# Development Server (Port 3000)
npm run dev
```

### 4. GUI öffnen

Öffnen Sie im Browser:
```
http://localhost:3001
```

## Features & Verwendung

### Dashboard
- System-Informationen (CPU, RAM, Speicher)
- Installation Status
- Schnelllinks zu Modulen

### Installationsassistent
- Schritt-für-Schritt Konfiguration
- Automatische Installation aller Komponenten
- Fortschrittsanzeige

![Assistent](docs/screenshots/screenshot-wizard.png)

### Module

#### 🔒 Sicherheit
- Firewall-Konfiguration (UFW)
- Fail2Ban für SSH-Brute-Force Schutz
- Automatische Sicherheitsupdates
- SSH-Härtung
- Audit-Logging

#### 👥 Benutzer
- Neue Benutzer erstellen
- Rollenbasierte Zugriffe (Admin, Developer, User)
- SSH-Key Management
- Passwort-Verwaltung

#### 💻 Entwicklungsumgebung
- Sprachen: Python, Node.js, Go, Rust
- Datenbanken: PostgreSQL, MySQL, MongoDB, Redis
- Tools: Docker, Git, VS Code Server
- GitHub Integration

#### 🌐 Webserver
- Nginx/Apache Auswahl
- SSL/TLS mit Let's Encrypt
- PHP-Support
- CMS Installation (WordPress, Drupal, Nextcloud)
- Webadmin Panels (Cockpit, Webmin)

#### 📧 Mailserver (Optional)
- Postfix (SMTP)
- Dovecot (IMAP/POP3)
- SpamAssassin
- TLS/SSL Verschlüsselung
- Automatische Zertifikate

## API Endpoints

### System
- `GET /api/status` - System Status
- `GET /api/system-info` - Detaillierte System-Info

### Sicherheit
- `POST /api/security/scan` - Sicherheits-Scan
- `POST /api/security/configure` - Sicherheit konfigurieren
- `GET /api/security/status` - Sicherheits-Status

### Benutzer
- `GET /api/users` - Alle Benutzer auflisten
- `POST /api/users/create` - Neuen Benutzer erstellen
- `DELETE /api/users/{username}` - Benutzer löschen

### Entwicklungsumgebung
- `POST /api/devenv/configure` - Dev-Umgebung einrichten
- `GET /api/devenv/status` - Dev-Status

### Webserver
- `POST /api/webserver/configure` - Webserver konfigurieren
- `GET /api/webserver/status` - Webserver-Status

### Mailserver
- `POST /api/mail/configure` - Mailserver konfigurieren
- `GET /api/mail/status` - Mail-Status

### Installation
- `POST /api/install/start` - Installation starten
- `GET /api/install/progress` - Installationsfortschritt

### Mixer (Audio)
- `POST /api/system/run-mixer` - Grafischen Mixer starten (Body: `{"app": "pavucontrol"}` oder `{"app": "qpwgraph"}`)
- `POST /api/system/install-mixer-packages` - pavucontrol und qpwgraph installieren (Body optional: `{"sudo_password": "..."}`)

### NAS Duplikate
- `POST /api/nas/duplicates/install` - fdupes installieren (Body: `{"sudo_password": "..."}`)
- `POST /api/nas/duplicates/scan` - Duplikate scannen (Body: `{"path": "/mnt/nas"}`)
- `POST /api/nas/duplicates/move-to-backup` - Duplikate ins Backup verschieben (Body: `{"groups": [...], "backup_path": "/mnt/nas/duplicate_backup", "sudo_password": "..."}`)

## Production Deployment

### Mit Docker

```bash
# Docker-Image bauen
docker build -t pi-installer .

# Container starten
docker run -it --net=host -v /proc:/proc -v /sys:/sys \
  pi-installer
```

### Mit systemd

```bash
# Backend Service erstellen
sudo cp pi-installer.service /etc/systemd/system/

# Aktivieren und starten
sudo systemctl daemon-reload
sudo systemctl enable pi-installer
sudo systemctl start pi-installer
```

## Sicherheitshinweise

1. **HTTPS verwenden** - In Production sollte HTTPS aktiviert sein
2. **Authentifizierung** - JWT-Token sollten implementiert werden
3. **Rate Limiting** - API sollte Rate-Limits haben
4. **Backups** - Regelmäßige Backups erstellen
5. **Updates** - Regelmäßig Sicherheitsupdates spielen

## Troubleshooting

### Duplikat-Finder (fdupes/jdupes) Installation fehlgeschlagen?
Wenn „Installieren“ unter NAS → Duplikate & Aufräumen fehlschlägt:

1. **Fehlermeldung prüfen:** Die App zeigt nun die genaue Fehlermeldung von apt (bis 600 Zeichen).
2. **Manuell installieren:**
   ```bash
   sudo apt update
   sudo apt install -y fdupes   # oder: sudo apt install -y jdupes
   ```
3. **Paket nicht gefunden?** Versuche `jdupes` als Alternative: `sudo apt install -y jdupes`. Beide Tools werden vom Duplikat-Finder unterstützt.
4. **Netzwerk/Repository-Probleme:** Bei „Could not resolve“ oder GPG-Fehlern zuerst `sudo apt update` im Terminal ausführen und ggf. die Netzwerkverbindung prüfen.

### Mixer-Installation fehlgeschlagen?
Wenn „Mixer-Programme installieren“ (pavucontrol & qpwgraph) in der App fehlschlägt:

1. **Sudo-Passwort:** Beim Klick auf „Mixer-Programme installieren“ das Sudo-Passwort eingeben (Modal erscheint, falls noch nicht gespeichert).
2. **Manuell im Terminal installieren:**
   ```bash
   sudo apt update
   sudo apt install -y pavucontrol qpwgraph
   ```
3. **Mixer starten:** Danach in der Musikbox oder unter Kino/Streaming „Mixer öffnen (pavucontrol)“ bzw. „Mixer öffnen (qpwgraph)“ nutzen. Läuft das Backend als Dienst ohne Grafikumgebung, wird `DISPLAY=:0` gesetzt – der Mixer öffnet sich auf der ersten X-Session.

4. **Installation schlägt weiterhin fehl (ab 1.2.0.1):** Die App führt nun `apt-get update` vor der Installation aus und trimmt das Sudo-Passwort. Prüfe die angezeigte Fehlermeldung (bis 600 Zeichen) und ggf. die Backend-Logdatei (`Einstellungen → Logs` oder `logs/pi-installer.log`). Bei Berechtigungsfehlern: Nutzer muss in `sudoers` sein und das Passwort korrekt eingegeben werden.

### Raspberry Pi 5: Kein Ton über HDMI?
Wenn am angeschlossenen Monitor kein Ton ausgegeben wird, typische Symptome: `cat /proc/asound/cards` → „no soundcards“; `amixer sget Master` → „cannot find card 0“; `ls /dev/snd/` → nur seq und timer, keine controlC0.

**Ursache:** Ohne den Overlay `vc4-kms-v3d-pi5` wird die HDMI-Audio-Hardware des Pi 5 nicht initialisiert.

1. **System aktualisieren:** `sudo apt update && sudo apt full-upgrade -y`, danach Neustart.
2. **config.txt bearbeiten:** `sudo nano /boot/firmware/config.txt` – Zeile `dtoverlay=vc4-kms-v3d-pi5` hinzufügen (unter `dtparam=audio=on`). Beide Einträge müssen vorhanden sein.
3. Speichern und `sudo reboot`.
4. Danach HDMI-Gerät in den Sound-Einstellungen oder mit pavucontrol als Ausgabe wählen.

### Port bereits in Benutzung?
```bash
# Port freigeben
lsof -i :8000
kill -9 <PID>
```

### Permissions Problem?
```bash
# Entsprechende Rechte geben
sudo chown -R $USER:$USER ~/PI-Installer
```

### Module starten nicht?
```bash
# Logs prüfen
journalctl -u pi-installer -f
```

## Unterstützung

- GitHub Issues für Bug-Reports
- Diskussionen für Feature-Requests
- Email Support: <support@pi-installer.local>

## Dokumentations-Screenshots (Tauri-App)

In der Tauri-Desktop-App können Screenshots aller Menüpunkte für die Dokumentation erstellt werden – ohne echte IP-Adressen, Benutzernamen oder Passwörter (Platzhalterdaten).

1. PI-Installer starten, Sudo-Passwort eingeben
2. **Einstellungen** → **Allgemein** → **Dokumentations-Screenshots**
3. Auf **Screenshots erstellen** klicken
4. Die App navigiert automatisch durch alle Menüpunkte und speichert Screenshots in  
   `~/Dokumente/PI-Installer/docs/screenshots/` (bzw. `~/Documents/PI-Installer/docs/screenshots/`)

5. **Damit die Screenshots in der In-App-Dokumentation angezeigt werden**, muss eine Kopie im Frontend liegen:
   ```bash
   mkdir -p frontend/public/docs/screenshots
   cp docs/screenshots/*.png frontend/public/docs/screenshots/
   ```
   Danach Frontend/App neu starten.

## Dokumentation als PDF

Die Dokumentation kann als PDF erstellt werden:

```bash
./scripts/create-documentation-pdf.sh
```

**Voraussetzungen (eine der Optionen):**
- `pandoc` + `texlive-xetex`: `sudo apt install pandoc texlive-xetex`
- oder Node.js/npm: Das Skript verwendet dann `npx md-to-pdf` (beim ersten Lauf kann der Chromium-Download einige Minuten dauern)

**Ausgabe:** `docs/PI-Installer-Dokumentation.pdf` (und `docs/PI-Installer-Dokumentation.md` als kombinierte Markdown-Quelle)

## Lizenz

MIT License - siehe LICENSE Datei

---

**Version:** 1.3.1.0  
**Letztes Update:** 2026-02
