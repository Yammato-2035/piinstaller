# Setuphelfer – Startoptionen (Backend, Tauri-App, Browser)

Übersicht aller Möglichkeiten, Backend und Frontend zu starten.

**Installiert unter `/opt` (systemd) vs. Entwicklung im Repo:** strikt getrennte Startmodi und typische Fehler (z. B. Vite-Dev im Installationspfad) – siehe **`docs/BETRIEB_REPO_VS_SERVICE.md`**.

**systemd (Produktion):** **`setuphelfer-backend.service`** (Port **8000**), **`setuphelfer.service`** (Web-UI, **vite preview**). Legacy: `pi-installer*.service`.

---

## Übersicht

| Ziel | Befehl / Starter | Hinweis |
|------|------------------|---------|
| **Alle Startoptionen (zentral)** | `./scripts/start-all.sh` | Menü: Backend, Backend+Frontend, Setuphelfer, nur Frontend (Browser/Tauri/Vite) |
| **SetupHelfer (empfohlen)** | `./scripts/start-setuphelfer.sh` oder `./scripts/start-pi-installer.sh` (Alias) bzw. **SetupHelfer.desktop** | Wartet auf Backend, dann Auswahl: **Tauri-App / Browser / Nur Backend** |
| **Backend** | **`setuphelfer-backend.service`** (Owner von :8000) | Pflicht für Web-UI und Tauri; Web-UI startet kein zweites Backend |
| **Frontend (Browser)** | `./scripts/start-frontend-desktop.sh --browser` | Vite Port 3001 + Standard-Browser |
| **Frontend (Tauri-App)** | `./scripts/start-frontend-desktop.sh --window` | Eigenes Fenster, Port 5173 (Dev) |
| **Frontend (nur Server)** | `./scripts/start-frontend.sh` | Nur Vite, kein Fenster/Browser |
| **Beide zusammen (Browser)** | `./start.sh` | Backend + Frontend (Vite), dann http://localhost:3001 |

---

## 0a. Zentrale Startfunktion (alle Optionen)

```bash
./scripts/start-all.sh
```

Ohne Argument erscheint ein **Terminal-Menü**. Direktaufruf:

```bash
./scripts/start-all.sh help
./scripts/start-all.sh backend
./scripts/start-all.sh backend-bg
./scripts/start-all.sh both-browser
./scripts/start-all.sh both-tauri
./scripts/start-all.sh both-vite
./scripts/start-all.sh menu
./scripts/start-all.sh setuphelfer    # Dialog (Alias: pi-installer)
./scripts/start-all.sh frontend-browser
./scripts/start-all.sh frontend-tauri
./scripts/start-all.sh frontend-vite
```

---

## 0. SetupHelfer (Kombi-Starter, empfohlen)

### Terminal

```bash
./scripts/start-setuphelfer.sh
# oder (Legacy-Name, leitet weiter):
./scripts/start-pi-installer.sh
```

- Wartet bis Backend antwortet (max. 60 s; Backend typischerweise als Service **`setuphelfer-backend`**)
- Dialog (zenity/kdialog) oder Terminal-Auswahl: **Tauri / Browser / Nur Backend**

### Desktop-Starter

```bash
bash scripts/desktop-setuphelfer-launcher-anlegen.sh
# Legacy-Dateiname (leitet weiter):
bash scripts/desktop-pi-installer-launcher-anlegen.sh
```

Weitere Starter (DSI Radio, …) im Ordner **Desktop/PI-Installer/** (Skripte `desktop-launcher-alle-anlegen.sh`):

```bash
bash scripts/desktop-launcher-alle-anlegen.sh
```

### Auswahl ohne Dialog

```bash
PI_INSTALLER_MODE=tauri ./scripts/start-setuphelfer.sh
PI_INSTALLER_MODE=browser ./scripts/start-setuphelfer.sh
PI_INSTALLER_MODE=backend ./scripts/start-setuphelfer.sh
PI_INSTALLER_MODE=frontend ./scripts/start-setuphelfer.sh
```

---

## 1. Backend (Service oder manuell)

- **Port:** http://localhost:8000  
- **API-Dokumentation:** http://localhost:8000/docs  

### Automatisch beim Boot

```bash
./scripts/install-backend-service.sh
```

Richtet **`setuphelfer-backend`** ein (enable + start). Status: `sudo systemctl status setuphelfer-backend`  
Neustart: `./scripts/restart-backend-service.sh` oder `sudo systemctl restart setuphelfer-backend`.

### Manuell

- **Service:** `sudo systemctl start setuphelfer-backend`  
- **Terminal:** `./scripts/start-backend.sh`

**Venv nach Updates:** `./scripts/start-backend.sh` synchronisiert bei geändertem `requirements.txt`; siehe **docs/user/QUICKSTART.md**.

---

## 2. Frontend mit Tauri-App (eigenes Fenster)

### Voraussetzung

- Backend auf Port 8000 (in der Regel **`setuphelfer-backend.service`**)

### Terminal

```bash
./scripts/start-frontend-desktop.sh --window
```

### Direkt im `frontend/`-Ordner

```bash
cd frontend
npm run tauri:dev
```

### Desktop-Starter

Nach `bash scripts/desktop-launcher-alle-anlegen.sh`: Ordner **Desktop/PI-Installer/** – z. B. **„PI-Installer Frontend (App-Fenster)“** (Bezeichnung je nach Skriptversion).

---

## 3. Frontend im Browser

```bash
./scripts/start-frontend-desktop.sh --browser
```

### Beide zusammen

```bash
./start.sh
```

---

## 4. Alle Desktop-Starter anlegen

```bash
cd /pfad/zum/piinstaller
bash scripts/desktop-launcher-alle-anlegen.sh
```

Es wird u. a. der Ordner **Desktop/PI-Installer/** mit weiteren Startern befüllt (DSI Radio, Vite, …).

---

## Reihenfolge

1. **Backend** läuft als **`setuphelfer-backend`** – einrichten mit `./scripts/install-backend-service.sh`
2. **Frontend** starten (Tauri oder Browser)

Ohne Backend schlagen API-Aufrufe fehl.

---

## Ports

| Service | Port |
|---------|------|
| Backend | 8000 |
| Frontend (Vite, Browser) | 3001 |
| Frontend (Tauri Dev) | 5173 |

---

## Fehlerbehebung: Browser erreicht Backend nicht

```bash
curl http://127.0.0.1:8000/api/version
```

Wenn leer: `./scripts/start-backend.sh` oder `sudo systemctl start setuphelfer-backend`.

Remote-Entwicklung: `VITE_PROXY_TARGET=http://192.168.x.x:8000 npm run dev`

---

## Fehlerbehebung: Tauri-App startet, Backend wird nicht erkannt

- **`npm run tauri:dev`:** Backend wird bei Bedarf mitgestartet (siehe Frontend-`package.json`).
- **Gebaute Binary:** verbindet nur mit `http://127.0.0.1:8000` – Backend vorher starten oder **`start-setuphelfer.sh`** nutzen.
- **Desktop:** `install-desktop-entries.sh` verweist auf den Starter unter `/opt/setuphelfer/scripts/…`.
