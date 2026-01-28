# 🚀 Erste Schritte mit PI-Installer

Willkommen zu PI-Installer! Diese Anleitung hilft Ihnen, schnell zu starten.

## ⚡ 5-Minuten Quickstart

### Schritt 1: Repository vorbereiten
```bash
cd ~/Documents/PI-Installer
```

### Schritt 2: Backend starten
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

**Erfolgsmeldung:** Sie sehen `Uvicorn running on http://0.0.0.0:8000`

### Schritt 3: Frontend starten (neues Terminal-Tab)
```bash
cd frontend
npm install
npm run dev
```

**Erfolgsmeldung:** Sie sehen `http://localhost:3000`

### Schritt 4: GUI öffnen
Öffnen Sie im Browser: **http://localhost:3000** 🎉

---

## 📖 Dokumentation Navigation

### Für Anfänger
1. **Dieses Dokument (STARTED.md)** - Los geht's!
2. **[INSTALL.md](./INSTALL.md)** - Detaillierte Installation
3. **[README.md](./README.md)** - Projekt-Übersicht

### Für Entwickler
1. **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System-Design
2. **[FEATURES.md](./FEATURES.md)** - Feature-Liste
3. **Source Code** - `/backend` & `/frontend`

### Für Erweiterer
1. **[SUGGESTIONS.md](./SUGGESTIONS.md)** - Feature-Ideen
2. **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** - Zusammenfassung
3. **API Docs** - http://localhost:8000/docs

---

## 🎯 Was können Sie jetzt machen?

### 1. Dashboard erkunden
- System-Informationen sehen
- CPU, RAM, Speicher auslesen
- Module-Übersicht anschauen

### 2. Installationsassistent verwenden
- 6-Schritt Wizard
- Alle Komponenten wählen
- Installation starten

### 3. Einzelne Module konfigurieren
- **Sicherheit:** Firewall, SSH, Updates
- **Benutzer:** Neue User erstellen
- **Entwicklung:** Sprachen installieren
- **Webserver:** Web-Stack aufbauen
- **Mailserver:** (Optional) E-Mail-Server

---

## 🔧 Troubleshooting

### Port 8000 bereits in Benutzung?
```bash
# Finden Sie den Prozess
lsof -i :8000

# Beenden Sie ihn (PID einsetzen)
kill -9 <PID>
```

### Port 3000 bereits in Benutzung?
```bash
# Alternative Port in vite.config.ts setzen
```

### Python-Fehler?
```bash
# Stellen Sie sicher, dass Python 3.9+ installiert ist
python3 --version

# Virtual Environment neu erstellen
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### npm-Fehler?
```bash
# node_modules löschen und neu installieren
rm -rf node_modules
npm install
```

---

## 📚 Feature-Übersicht

### 🔒 Sicherheit
- Automatische Sicherheitsupdates
- Firewall (UFW) Konfiguration
- SSH-Hardening
- Fail2Ban gegen Brute-Force
- Audit-Logging

### 👥 Benutzerverwaltung
- Neue Benutzer erstellen
- 3 Rollen: Admin, Developer, User
- SSH-Key Management
- Passwort-Verwaltung

### 💻 Entwicklungsumgebung
- Python, Node.js, Go, Rust
- PostgreSQL, MySQL, MongoDB, Redis
- Docker, Git, GitHub-Integration
- VS Code Server

### 🌐 Webserver
- Nginx oder Apache
- SSL/TLS (Let's Encrypt)
- PHP-Support
- CMS (WordPress, Drupal, Nextcloud)
- Webadmin Panels

### 📧 Mailserver (Optional)
- Postfix SMTP
- Dovecot IMAP/POP3
- SpamAssassin Filter
- TLS/SSL verschlüsselt

---

## 🎨 GUI Features

### Design
- 🌙 Dark Mode mit Sky-Blue Accents
- ✨ Glasmorphism Styling
- 📱 Responsive auf allen Geräten
- ⚡ Schnelle Performance

### Navigation
- 📊 Dashboard mit Live-Daten
- 🧙 Installationsassistent
- ⚙️ Modul-Management Interfaces
- 🔔 Toast Notifications

---

## 📊 API Beispiele

### System-Status abrufen
```bash
curl http://localhost:8000/api/status
```

### Benutzer auflisten
```bash
curl http://localhost:8000/api/users
```

### Neue User erstellen
```bash
curl -X POST http://localhost:8000/api/users/create \
  -H "Content-Type: application/json" \
  -d '{
    "username": "developer",
    "email": "dev@example.com",
    "role": "developer",
    "create_ssh_key": true
  }'
```

### Sicherheit konfigurieren
```bash
curl -X POST http://localhost:8000/api/security/configure \
  -H "Content-Type: application/json" \
  -d '{
    "enable_firewall": true,
    "enable_fail2ban": true,
    "enable_auto_updates": true,
    "open_ports": [22, 80, 443]
  }'
```

---

## 🚀 Nächste Schritte

### Nach der Installation

1. **Testen Sie die Sicherheits-Scan**
   - Gehen Sie zu "Sicherheit"
   - Klicken Sie "Scan durchführen"
   - Überprüfen Sie die Ergebnisse

2. **Erstellen Sie einen Administrator-User**
   - Gehen Sie zu "Benutzer"
   - Fügen Sie einen neuen Admin-Benutzer hinzu
   - Generieren Sie SSH-Keys

3. **Installieren Sie die Entwicklungsumgebung**
   - Wählen Sie benötigte Sprachen
   - Wählen Sie Datenbanken
   - Starten Sie die Installation

4. **Richten Sie Webserver ein**
   - Wählen Sie Nginx/Apache
   - Aktivieren Sie SSL
   - (Optional) Installieren Sie CMS

---

## 💡 Tipps & Tricks

### Backend Live-Entwicklung
```bash
# Mit auto-reload (installieren Sie watch)
pip install watchfiles
# Dann normal starten - ändert sich auto
```

### Frontend Live-Entwicklung
```bash
# Hot Module Reloading ist automatisch an
npm run dev
```

### Docker-Setup
```bash
docker-compose up -d
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

### API-Dokumentation ansehen
```
http://localhost:8000/docs
```

---

## 🎓 Lernressourcen

- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **React Docs:** https://react.dev/
- **Tailwind CSS:** https://tailwindcss.com/
- **Raspberry Pi Docs:** https://www.raspberrypi.org/documentation/

---

## ❓ FAQ

**F: Welche Python-Version wird benötigt?**
A: Python 3.9 oder höher

**F: Welche Node-Version wird benötigt?**
A: Node 16 oder höher

**F: Kann ich auf verschiedenen Raspberry Pi Modellen installieren?**
A: Ja, aber Pi 4 oder besser empfohlen

**F: Ist Internetverbindung erforderlich?**
A: Ja, für Package-Downloads

**F: Wie lang dauert die Installation?**
A: 45-120 Minuten je nach Auswahl

**F: Kann ich einzelne Module deinstallieren?**
A: Ja, manuell über System-Befehle

---

## 🆘 Support erhalten

1. **GitHub Issues:** Bug Reports & Features
2. **GitHub Discussions:** Fragen & Community
3. **Dokumentation:** Umfangreiche Guides
4. **Email:** support@pi-installer.local

---

## 🎉 Viel Erfolg!

Sie sind jetzt bereit, PI-Installer zu verwenden!

### Zu erkundende Bereiche:
- 📊 Dashboard-Seite erkunden
- 🧙 Installationsassistent durchgehen
- ⚙️ Einzelne Module konfigurieren
- 📚 Dokumentation lesen
- 💬 Community beitreten

**Viel Spaß! 🚀**

---

### Schnelle Referenz

| Task | Command |
|------|---------|
| Backend starten | `cd backend && python3 app.py` |
| Frontend starten | `cd frontend && npm run dev` |
| GUI öffnen | `http://localhost:3000` |
| API Docs | `http://localhost:8000/docs` |
| System-Info | `curl http://localhost:8000/api/system-info` |
| Beide Prozesse beenden | `Ctrl+C` |

---

**Version:** 1.0.0  
**Stand:** Januar 2026  
**Autor:** Gabriel Glienke  
**Status:** 🟢 Produktionsreif
