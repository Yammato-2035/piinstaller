# PI-Installer - Installationsanleitung

## Voraussetzungen

- Raspberry Pi 4 oder besser (empfohlen: 8GB RAM)
- Raspberry Pi OS (Debian-basiert) - aktuell installiert
- SSH-Zugriff auf den Pi
- Internetzugang
- Root/Sudo-Zugriff

## Schnellstart

### 1. Repository klonen

```bash
cd ~
git clone <repository-url>
cd PI-Installer
```

### 2. Backend starten

```bash
# Python virtuelle Umgebung
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
http://localhost:3000
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

## Lizenz

MIT License - siehe LICENSE Datei

---

**Version:** 1.0.0  
**Letztes Update:** 2026-01-24
