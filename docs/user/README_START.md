# PI-Installer - Startanleitung

> **Vollständige Übersicht:** [docs/START_APPS.md](docs/START_APPS.md) – Backend, Tauri-App, Browser

## 🚀 Schnellstart

### Option 1: Beide Services zusammen (Browser)
```bash
./start.sh
```
Backend + Frontend, dann **http://localhost:3001** im Browser öffnen.

### Option 2: Backend + Tauri-App (eigenes Fenster)
```bash
./start-backend.sh          # Terminal 1
./start-frontend-desktop.sh --window   # Terminal 2
```

### Option 3: Backend + Browser (mit Auto-Öffnen)
```bash
./start-backend.sh          # Terminal 1
./start-frontend-desktop.sh --browser  # Terminal 2 – öffnet Browser automatisch
```

### Option 4: Mit Startskripten (getrennt)

#### Backend:
```bash
./start-backend.sh
```

#### Frontend (nur Vite-Server):
```bash
./start-frontend.sh
```
Browser manuell: http://localhost:3001

---

## 📋 Detaillierte Anleitung

### Backend (Port 8000)

1. **In das Backend-Verzeichnis wechseln:**
   ```bash
   cd backend
   ```

2. **Virtual Environment aktivieren:**
   ```bash
   source venv/bin/activate
   ```
   
   Falls venv nicht existiert:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Dependencies installieren (falls nötig):**
   ```bash
   pip install -r requirements.txt --only-binary :all:
   ```
   
   Falls das fehlschlägt:
   ```bash
   pip install -r requirements.txt
   ```

4. **Backend starten:**
   ```bash
   python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
   ```
   Oder einfacher: `./start-backend.sh` (im Projektroot)

   Backend läuft dann auf: **http://localhost:8000**
   API Dokumentation: **http://localhost:8000/docs**

---

### Frontend – drei Varianten

| Variante | Befehl | Port |
|----------|--------|------|
| Browser | `./start-frontend-desktop.sh --browser` | 3001 |
| Tauri-App (eigenes Fenster) | `./start-frontend-desktop.sh --window` | 5173 |
| Nur Server | `./start-frontend.sh` oder `npm run dev` | 3001 |

**Im Frontend-Verzeichnis:**
```bash
cd frontend
npm install
npm run dev          # Browser: http://localhost:3001
# oder
npm run tauri:dev    # Tauri-App (eigenes Fenster)
```

---

## 🔧 Troubleshooting

### Backend startet nicht

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**Problem:** Port 8000 bereits belegt
```bash
# Prüfe welcher Prozess Port 8000 nutzt
sudo lsof -i :8000
# Beende den Prozess oder ändere den Port in app.py
```

### Frontend startet nicht

**Problem:** `vite: not found`
```bash
cd frontend
npm install
```

**Problem:** Port 3001 bereits belegt
- Vite wählt automatisch einen anderen Port (3002, 3003, etc.)
- Oder beende den Prozess auf Port 3001:
  ```bash
  sudo lsof -i :3001
  sudo kill -9 <PID>
  ```

### Frontend kann Backend nicht erreichen

**Problem:** `Error: getaddrinfo ENOTFOUND backend`
- Stelle sicher, dass Backend auf Port 8000 läuft
- Prüfe `vite.config.ts` - Proxy sollte auf `http://localhost:8000` zeigen

---

## 🖥️ Desktop-Starter

Alle Starter auf einmal anlegen (Backend, Frontend, Tauri-App, Browser):
```bash
bash scripts/desktop-launcher-alle-anlegen.sh
```
Siehe [docs/START_APPS.md](docs/START_APPS.md) für Details.

---

## 📝 Wichtige URLs

- **Frontend:** http://localhost:3001
- **Backend API:** http://localhost:8000
- **API Dokumentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 🛑 Services beenden

- **Ctrl+C** im jeweiligen Terminal
- Oder mit `start.sh` gestartet: Einmal Ctrl+C beendet beide

---

## 💡 Tipps

1. **Zwei Terminal-Fenster öffnen:** Eines für Backend, eines für Frontend
2. **Logs beobachten:** Beide Services zeigen nützliche Logs im Terminal
3. **Browser-Console:** F12 im Browser für Frontend-Debugging
4. **API testen:** http://localhost:8000/docs für interaktive API-Dokumentation
