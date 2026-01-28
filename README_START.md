# PI-Installer - Startanleitung

## 🚀 Schnellstart

### Option 1: Beide Services zusammen starten
```bash
./start.sh
```

### Option 2: Getrennt starten

#### Backend starten (Terminal 1):
```bash
cd backend
source venv/bin/activate
python3 app.py
```

#### Frontend starten (Terminal 2):
```bash
cd frontend
npm run dev
```

### Option 3: Mit Startskripten

#### Backend:
```bash
./start-backend.sh
```

#### Frontend:
```bash
./start-frontend.sh
```

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
   python3 app.py
   ```

   Backend läuft dann auf: **http://localhost:8000**
   API Dokumentation: **http://localhost:8000/docs**

---

### Frontend (Port 3001)

1. **In das Frontend-Verzeichnis wechseln:**
   ```bash
   cd frontend
   ```

2. **Dependencies installieren (falls nötig):**
   ```bash
   npm install
   ```

3. **Frontend starten:**
   ```bash
   npm run dev
   ```

   Frontend läuft dann auf: **http://localhost:3001**

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
