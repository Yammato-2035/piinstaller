# Backend Configuration Guide

## 🔧 Environment Variables (.env)

Erstellen Sie eine `.env` Datei im `backend/` Verzeichnis:

```bash
cd backend
cat > .env << 'EOF'
# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=true

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# Security
SECRET_KEY=your-secret-key-here-change-in-production

# System
SYSTEM_USER=pi
BACKUP_DIR=/backups

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/pi-installer/app.log

# Features
ENABLE_MAILSERVER=false
WEBSERVER_TYPE=nginx

# Timeouts
INSTALL_TIMEOUT=7200
COMMAND_TIMEOUT=300
EOF
```

---

## 📋 Verfügbare Umgebungsvariablen

### Server Einstellungen

| Variable | Default | Beschreibung |
|----------|---------|-------------|
| `SERVER_HOST` | `0.0.0.0` | Server Bind Address |
| `SERVER_PORT` | `8000` | Server Port |
| `DEBUG` | `true` | Debug Mode |

### CORS Einstellungen

```python
# Mehrere Origins (komma-getrennt)
CORS_ORIGINS=http://localhost:3000,http://example.com
```

### Security

```python
# JWT Secret generieren
openssl rand -hex 32
# Ergebnis in SECRET_KEY eintragen
```

### System Einstellungen

```python
# Welcher User für sudo commands?
SYSTEM_USER=pi  # oder root

# Wo werden Backups gespeichert?
BACKUP_DIR=/backups
```

### Logging

```python
# Log Level Options:
LOG_LEVEL=DEBUG      # Sehr detailliert
LOG_LEVEL=INFO       # Normal
LOG_LEVEL=WARNING    # Nur Warnungen
LOG_LEVEL=ERROR      # Nur Fehler
```

### Features

```python
# Mailserver aktivieren?
ENABLE_MAILSERVER=true|false

# Webserver Type
WEBSERVER_TYPE=nginx|apache
```

### Timeouts (in Sekunden)

```python
# Wie lange darf Installation dauern?
INSTALL_TIMEOUT=7200  # 2 Stunden

# Wie lange darf ein Kommando dauern?
COMMAND_TIMEOUT=300   # 5 Minuten
```

---

## 🚀 Unterschiedliche Modi

### Development Mode

```bash
DEBUG=true
LOG_LEVEL=DEBUG
TEST_MODE=false
HOT_RELOAD=true
```

### Production Mode

```bash
DEBUG=false
LOG_LEVEL=INFO
TEST_MODE=false
HOT_RELOAD=false
```

### Test Mode

```bash
DEBUG=true
LOG_LEVEL=DEBUG
TEST_MODE=true
INSTALL_TIMEOUT=60  # Schnellere Tests
```

---

## 📧 Email Konfiguration (optional)

Für E-Mail Benachrichtigungen:

```
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=noreply@pi-installer.local
```

---

## 🐳 Docker Konfiguration

### Environment in docker-compose.yml

```yaml
environment:
  - SERVER_HOST=0.0.0.0
  - SERVER_PORT=8000
  - DEBUG=false
  - LOG_LEVEL=INFO
```

Oder mit `.env` Datei:

```yaml
env_file:
  - backend/.env
```

---

## 🔒 Sicherheit in Production

### Änderungen für Production:

1. **Debug ausschalten**
   ```
   DEBUG=false
   ```

2. **Secret Key setzen** (wichtig!)
   ```bash
   openssl rand -hex 32
   # Kopieren in SECRET_KEY
   ```

3. **CORS Origins begrenzen**
   ```
   CORS_ORIGINS=https://example.com
   ```

4. **Log Level auf WARNING**
   ```
   LOG_LEVEL=WARNING
   ```

5. **HTTPS aktivieren** (via Nginx)
   ```
   # In nginx.conf
   listen 443 ssl http2;
   ssl_certificate /path/to/cert.pem;
   ssl_certificate_key /path/to/key.pem;
   ```

---

## 🐛 Debug-Tipps

### Verbose Logging

```bash
LOG_LEVEL=DEBUG python3 app.py
```

### Test einzelner Module

```bash
# SecurityModule testen
python3 -c "
from modules.security import SecurityModule
import asyncio

async def test():
    sec = SecurityModule()
    result = await sec.scan_system()
    print(result)

asyncio.run(test())
"
```

### API Test

```bash
# Health Check
curl http://localhost:8000/health

# System Info
curl http://localhost:8000/api/system-info

# API Dokumentation
curl http://localhost:8000/openapi.json
```

---

## 📊 Log Dateien

### Standard Logs

```bash
# Live logs anschauen
tail -f /var/log/pi-installer/app.log

# Letzte 100 Zeilen
tail -100 /var/log/pi-installer/app.log

# Grep nach Errors
grep ERROR /var/log/pi-installer/app.log
```

### Systemd Logs (bei Service Installation)

```bash
journalctl -u pi-installer -f
journalctl -u pi-installer -n 100
```

---

## 🔄 Konfiguration zur Laufzeit ändern

### Environment Variable überschreiben

```bash
DEBUG=false python3 app.py
```

### Mehrere Override

```bash
DEBUG=true LOG_LEVEL=DEBUG python3 app.py
```

### Mit export (für Session)

```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
python3 app.py
```

---

## ✅ Konfiguration prüfen

```bash
# Python Imports testen
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('SERVER_HOST:', os.getenv('SERVER_HOST'))
print('SERVER_PORT:', os.getenv('SERVER_PORT'))
print('DEBUG:', os.getenv('DEBUG'))
"
```

---

## 🆘 Typische Konfigurationsfehler

### ❌ CORS Error

**Problem:** Frontend kann Backend nicht erreichen

**Lösung:**
```
CORS_ORIGINS=http://localhost:3000
```

### ❌ Permission Denied

**Problem:** `ModuleNotFoundError` oder `PermissionError`

**Lösung:**
```bash
sudo chown -R $USER:$USER /backups
chmod -R 755 /backups
```

### ❌ Port bereits in Benutzung

**Problem:** `Address already in use`

**Lösung:**
```
SERVER_PORT=8001  # Anderen Port nutzen
```

### ❌ Timeout bei Installation

**Problem:** Installation wird zu schnell abgebrochen

**Lösung:**
```
INSTALL_TIMEOUT=14400  # 4 Stunden
COMMAND_TIMEOUT=600    # 10 Minuten
```

---

## 📝 Beispiel .env Dateien

### Minimal (Development)
```
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=true
CORS_ORIGINS=http://localhost:3000
SYSTEM_USER=pi
LOG_LEVEL=INFO
```

### Full (Production)
```
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false

CORS_ORIGINS=https://pi-installer.example.com

SECRET_KEY=<32-byte-hex-string>

SYSTEM_USER=pi
BACKUP_DIR=/backups

LOG_LEVEL=WARNING
LOG_FILE=/var/log/pi-installer/app.log

ENABLE_MAILSERVER=true
WEBSERVER_TYPE=nginx

INSTALL_TIMEOUT=7200
COMMAND_TIMEOUT=300

SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=user@example.com
SMTP_FROM=noreply@pi-installer.local

WEBHOOK_URL=https://hooks.slack.com/services/...
```

---

**Version:** 1.0.0  
**Letzte Aktualisierung:** 2026-01-24
