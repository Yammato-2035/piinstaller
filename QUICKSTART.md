# ⚡ PI-Installer - Schnellstart & Fehlerbehebung

## Python: 3.9 oder neuer (3.12 empfohlen)

Prüfen Sie zuerst:
```bash
python3 --version   # Sollte 3.9, 3.10, 3.11 oder 3.12 sein
```

Falls Sie **Python 3.12** haben, können Sie explizit `python3.12` nutzen. Ansonsten reicht `python3` (3.9+).  
Bei Problemen: **PYTHON_SETUP.md**

---

## 🚀 Sofort Starten (3 Befehle)

### Terminal 1: Backend
```bash
cd ~/Documents/PI-Installer/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python3 app.py
```

**✅ Erfolgreich wenn Sie sehen:**
```
Uvicorn running on http://0.0.0.0:8000
```

### Terminal 2: Frontend
```bash
cd ~/Documents/PI-Installer/frontend
npm install
npm run dev
```

**✅ Erfolgreich wenn Sie sehen:**
```
Local:   http://localhost:3001
```

### Browser: GUI öffnen
```
http://localhost:3001
```

---

## 🔧 Häufige Fehler & Lösungen

### ❌ Fehler: `pydantic-core build failed` oder `PyO3` Fehler

**Ursache:** Oft Python 3.13 oder sehr alte Version.

**Lösung:**

#### Option 1: Python 3.9–3.12 verwenden (empfohlen)

```bash
# Prüfen welche Version Sie haben
python3 --version

# Falls 3.9–3.12: venv neu erstellen
cd ~/Documents/PI-Installer/backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python3 app.py
```

#### Option 2: Python 3.12 installieren (wenn nur 3.13 vorhanden)

```bash
sudo apt install -y python3.12 python3.12-venv python3.12-dev
# Dann: python3.12 -m venv venv usw. (siehe PYTHON_SETUP.md)
```

---

### ❌ Fehler: `frontend: No such file or directory`

**Ursache:** Befehle wurden im falschen Verzeichnis ausgeführt

**Lösung:**
```bash
# RICHTIG - Frontend Verzeichnis ist separat
cd ~/Documents/PI-Installer/frontend
npm install
npm run dev

# FALSCH - Nicht im backend Verzeichnis!
# cd ~/Documents/PI-Installer/backend
# cd frontend  # ← Das ist falsch!
```

---

### ❌ Fehler: `ModuleNotFoundError: No module named 'fastapi'`

**Ursache:** Dependencies nicht installiert

**Lösung:**
```bash
cd ~/Documents/PI-Installer/backend
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

---

### ❌ Fehler: `Port 8000 / 3000 already in use`

**Lösung:**
```bash
# Port 8000 freigeben
lsof -i :8000
kill -9 <PID>

# Port 3000 freigeben
lsof -i :3000
kill -9 <PID>
```

---

### ❌ Fehler: `npm: command not found`

**Ursache:** Node.js nicht installiert

**Lösung:**
```bash
# Installation Check
node --version  # Sollte v16+ sein
npm --version   # Sollte v8+ sein

# Falls nicht installiert:
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

---

### ❌ Fehler: `python3: command not found`

**Ursache:** Python nicht installiert (unwahrscheinlich auf Raspberry Pi)

**Lösung:**
```bash
python3 --version  # Check Version
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip
```

---

## 📋 Pre-Flight Checklist

Vor dem Start, prüfen Sie:

```bash
# 1. Python Version
python3 --version
# ✅ Sollte 3.9+ sein (optimal: 3.11+)

# 2. Node.js Version
node --version
# ✅ Sollte 16+ sein

# 3. npm Version
npm --version
# ✅ Sollte 8+ sein

# 4. Git (optional aber empfohlen)
git --version

# 5. Internetverbindung
ping -c 1 8.8.8.8
```

---

## 🎯 Schritt-für-Schritt Installation

### Schritt 1: Vorbereitung
```bash
cd ~/Documents/PI-Installer
ls -la  # Prüfen ob alles da ist
```

### Schritt 2: Backend Setup
```bash
cd backend

# Virtual Environment
python3 -m venv venv
source venv/bin/activate

# pip aktualisieren (WICHTIG!)
pip install --upgrade pip setuptools wheel

# Dependencies installieren
pip install -r requirements.txt

# Testen
python3 -c "import fastapi; print('FastAPI OK')"
```

### Schritt 3: Backend starten
```bash
python3 app.py
# Warten auf: "Uvicorn running on http://0.0.0.0:8000"
```

### Schritt 4: Frontend Setup (neues Terminal)
```bash
cd ~/Documents/PI-Installer/frontend

# Dependencies installieren
npm install

# Development Server starten
npm run dev
# Warten auf: "Local: http://localhost:3000"
```

### Schritt 5: Browser öffnen
```
http://localhost:3000
```

---

## 🐛 Debug-Modus

### Backend Debug Logs
```bash
cd backend
source venv/bin/activate
PYTHONDEBUG=1 python3 app.py
```

### Frontend Debug
```bash
cd frontend
npm run dev -- --host 0.0.0.0
```

### API testen
```bash
# Health Check
curl http://localhost:8000/health

# System Info
curl http://localhost:8000/api/system-info

# API Docs
curl http://localhost:8000/docs
```

---

## 💾 Alte Virtual Environment Löschen & Neu Anfangen

Falls etwas schiefläuft:

```bash
cd ~/Documents/PI-Installer/backend

# Alten venv löschen
rm -rf venv
rm -rf __pycache__

# Neu erstellen
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

python3 app.py
```

---

## 🚨 Falls immer noch Fehler

### Option 1: Docker verwenden (keine Dependencies!)
```bash
cd ~/Documents/PI-Installer
docker-compose up
```

### Option 2: Production Server
```bash
# Nginx + Backend
docker-compose up -d
# Öffnen: http://localhost
```

### Option 3: Einzelne Module testen
```bash
cd backend
source venv/bin/activate

# Module importieren testen
python3 -c "from modules.security import SecurityModule; print('OK')"
python3 -c "from modules.users import UserModule; print('OK')"
```

---

## ✅ Erfolgreiches Setup erkannt an:

**Backend:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Frontend:**
```
  VITE v5.0.0  ready in 234 ms

  ➜  Local:   http://localhost:3000/
  ➜  press h to show help
```

**Browser:** 
- Seite lädt mit Logo "π" 
- Sidebar sichtbar
- Dashboard zeigt System-Info

![Dashboard](docs/screenshots/screenshot-dashboard.png)

---

## 📞 Support

Wenn Sie immer noch Probleme haben:

1. Prüfen Sie **alle Befehle oben** erneut
2. Lesen Sie **INSTALL.md** für detaillierte Anleitung
3. Öffnen Sie ein **GitHub Issue** mit vollständiger Error-Meldung
4. Versuchen Sie Docker: `docker-compose up`

---

## 🎉 Alles funktioniert!

**Nächste Schritte:**
1. Dashboard erkunden
2. Installationsassistent durchgehen  
3. Module testen
4. Dokumentation lesen

---

**Version:** 1.0.0  
**Requirements aktualisiert:** 2026-01-24  
**Python-Versionen:** 3.9+ (getestet mit 3.11, 3.12, 3.13)
