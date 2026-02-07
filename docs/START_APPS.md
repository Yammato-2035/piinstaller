# PI-Installer – Startoptionen (Backend, Tauri-App, Browser)

Übersicht aller Möglichkeiten, Backend und Frontend zu starten.

---

## Übersicht

| Ziel | Befehl / Starter | Hinweis |
|------|------------------|---------|
| **PI-Installer (empfohlen)** | `./start-pi-installer.sh` oder Desktop-Starter | Startet Backend, wartet auf Ready, dann Auswahl: Tauri / Browser / Vite |
| **Backend** | `./start-backend.sh` oder Desktop-Starter | Port 8000, erforderlich für Frontend |
| **Frontend (Browser)** | `./start-frontend-desktop.sh --browser` | Vite Port 3001 + Standard-Browser öffnen |
| **Frontend (Tauri-App)** | `./start-frontend-desktop.sh --window` | Eigenes Fenster, Port 5173 (Dev) |
| **Frontend (nur Server)** | `./start-frontend.sh` | Nur Vite, kein Fenster/Browser |
| **Beide zusammen (Browser)** | `./start.sh` | Backend + Frontend (Vite), dann http://localhost:3001 |

---

## 0. PI-Installer (Kombi-Starter, empfohlen)

**Ein Starter für alles:** Backend wird zuerst gestartet (falls nicht läuft), dann wartet das Skript auf Backend-Ready (`/api/version`), danach erscheint ein Dialog zur Auswahl.

### Terminal
```bash
./start-pi-installer.sh
```
- Startet Backend im Hintergrund (falls nicht läuft)
- Wartet bis Backend antwortet (max. 60 s)
- Dialog (zenity/kdialog) oder Terminal-Auswahl: **Tauri** / **Browser** / **Nur Frontend**
- Tauri: mit `GDK_BACKEND=x11` (stabiles Rendering unter Wayland auf Pi)

### Desktop-Starter (mit Icon)
```bash
bash scripts/desktop-pi-installer-launcher-anlegen.sh
```
Danach: Doppelklick auf **„PI-Installer“** – startet Backend, wartet auf Ready, dann Auswahl.

Oder alle Starter anlegen:
```bash
bash scripts/desktop-launcher-alle-anlegen.sh
```
Legt u. a. „PI-Installer“ (Kombi), „PI-Installer Backend starten“ und die drei Frontend-Starter an.

### Auswahl ohne Dialog
```bash
PI_INSTALLER_MODE=tauri ./start-pi-installer.sh
PI_INSTALLER_MODE=browser ./start-pi-installer.sh
PI_INSTALLER_MODE=frontend ./start-pi-installer.sh
```

---

## 1. Backend starten

**Erforderlich** – Frontend (Tauri oder Browser) benötigt das Backend.

### Terminal
```bash
./start-backend.sh
```
- Startet Backend auf **http://localhost:8000**
- API-Dokumentation: http://localhost:8000/docs

### Desktop-Starter
```bash
bash scripts/desktop-launcher-alle-anlegen.sh
```
Danach: Doppelklick auf **„PI-Installer Backend starten“**

---

## 2. Frontend mit Tauri-App (eigenes Fenster)

Desktop-Anwendung mit eigenem Fenster – keine Browser-Leiste.

### Voraussetzung
- **Backend muss laufen** (zuerst `./start-backend.sh` oder Desktop-Starter)
- Rust/Tauri-Toolchain (bei erstem Aufruf: `cargo` wird genutzt)

### Terminal
```bash
./start-frontend-desktop.sh --window
# oder
./start-frontend-desktop.sh --tauri
```
- Startet Vite (Port 5173) + Tauri-Fenster
- Verbindet sich mit Backend unter 127.0.0.1:8000

### Direkt (im frontend/ Verzeichnis)
```bash
cd frontend
npm run tauri:dev
```

### Desktop-Starter
Nach `bash scripts/desktop-launcher-alle-anlegen.sh`:  
Doppelklick auf **„PI-Installer Frontend (App-Fenster)“**

---

## 3. Frontend im Browser

Web-Oberfläche im Standard-Browser.

### Voraussetzung
- **Backend muss laufen**

### Terminal
```bash
./start-frontend-desktop.sh --browser
```
- Startet Vite auf Port 3001
- Öffnet automatisch http://localhost:3001 im Standard-Browser

### Alternativ (manuell)
```bash
./start-frontend.sh
# Dann im Browser öffnen: http://localhost:3001
```

### Beide zusammen (Backend + Frontend)
```bash
./start.sh
```
- Startet Backend und Frontend
- Browser manuell öffnen: http://localhost:3001

### Desktop-Starter
Nach `bash scripts/desktop-launcher-alle-anlegen.sh`:  
Doppelklick auf **„PI-Installer Frontend (Browser)“**

---

## 4. Alle Desktop-Starter anlegen

```bash
cd ~/Documents/PI-Installer
bash scripts/desktop-launcher-alle-anlegen.sh
```

Es werden angelegt:
- **PI-Installer Backend starten**
- **PI-Installer Frontend starten** (nur Vite-Server)
- **PI-Installer Frontend (App-Fenster)** – Tauri
- **PI-Installer Frontend (Browser)** – Vite + Browser

---

## Reihenfolge

1. Zuerst **Backend** starten
2. Danach **Frontend** (Tauri oder Browser)

Ohne laufendes Backend schlagen Sudo-Passwort-Speicherung und API-Aufrufe fehl.

---

## Ports

| Service | Port |
|---------|------|
| Backend | 8000 |
| Frontend (Vite, Browser) | 3001 |
| Frontend (Tauri Dev) | 5173 |

---

## Fehlerbehebung: Browser erreicht Backend nicht

**Symptom:** Frontend lädt, aber API-Aufrufe schlagen fehl („Backend nicht erreichbar“, Netzwerkfehler).

### 1. Prüfen: Läuft das Backend?
```bash
curl http://127.0.0.1:8000/api/version
```
Erwartung: JSON-Antwort. Wenn nicht: Backend zuerst mit `./start-backend.sh` starten.

### 2. Beide auf demselben Rechner
- Frontend (Vite) leitet `/api` per Proxy an `127.0.0.1:8000` weiter.
- Backend muss auf Port 8000 laufen.
- Reihenfolge: zuerst Backend starten, danach Frontend.

### 3. Remote-Entwicklung (Frontend auf Laptop, Backend auf Pi)
Der Vite-Proxy nutzt standardmäßig `127.0.0.1:8000` (lokal). Wenn das Backend auf einem anderen Rechner läuft:
```bash
VITE_PROXY_TARGET=http://192.168.1.XX:8000 npm run dev
```
`192.168.1.XX` durch die IP des Raspberry Pi ersetzen.

### 4. Firewall
- Port 8000 (Backend) und 3001 (Frontend) müssen erreichbar sein.
- Bei Remote-Zugriff: Einstellungen → Frontend-Netzwerk-Zugriff prüfen.
