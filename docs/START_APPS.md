# PI-Installer – Startoptionen (Backend, Tauri-App, Browser)

Übersicht aller Möglichkeiten, Backend und Frontend zu starten.

---

## Übersicht

| Ziel | Befehl / Starter | Hinweis |
|------|------------------|---------|
| **Alle Startoptionen (zentral)** | `./scripts/start-all.sh` | Menü: Backend, Backend+Frontend, PI-Installer, nur Frontend (Browser/Tauri/Vite) |
| **PI-Installer (empfohlen)** | `./scripts/start-pi-installer.sh` oder Desktop-Starter | Wartet auf Backend (Service), dann Auswahl: Tauri / Browser / Vite |
| **Backend** | läuft als Service (`pi-installer-backend.service`) | Port 8000, erforderlich für Frontend |
| **Frontend (Browser)** | `./scripts/start-frontend-desktop.sh --browser` | Vite Port 3001 + Standard-Browser öffnen |
| **Frontend (Tauri-App)** | `./scripts/start-frontend-desktop.sh --window` | Eigenes Fenster, Port 5173 (Dev) |
| **Frontend (nur Server)** | `./scripts/start-frontend.sh` | Nur Vite, kein Fenster/Browser |
| **Beide zusammen (Browser)** | `./start.sh` | Backend + Frontend (Vite), dann http://localhost:3001 |

---

## 0a. Zentrale Startfunktion (alle Optionen)

**Ein Einstieg für Backend und alle Frontend-Varianten aus dem Repo:**

```bash
./scripts/start-all.sh
```

Ohne Argument erscheint ein **Terminal-Menü** mit allen Möglichkeiten:

- **Nur Backend** (Vordergrund oder Hintergrund)
- **Backend + Frontend** gemeinsam: Browser, Tauri-App oder nur Vite
- **PI-Installer** (wie start-pi-installer.sh: Dialog Tauri/Browser/Vite)
- **Nur Frontend**: Browser, Tauri oder nur Vite (Backend wird bei Bedarf automatisch gestartet)

### Direktaufruf (ohne Menü)

```bash
./scripts/start-all.sh help          # Optionen anzeigen
./scripts/start-all.sh backend       # Nur Backend (Vordergrund)
./scripts/start-all.sh backend-bg    # Nur Backend (Hintergrund)
./scripts/start-all.sh both-browser  # Backend + Frontend im Browser (wie start.sh)
./scripts/start-all.sh both-tauri    # Backend starten/prüfen + Tauri-App
./scripts/start-all.sh both-vite     # Backend starten/prüfen + nur Vite (Port 3001)
./scripts/start-all.sh menu         # Menü anzeigen
./scripts/start-all.sh pi-installer  # PI-Installer (Dialog)
./scripts/start-all.sh frontend-browser   # Nur Frontend – Browser
./scripts/start-all.sh frontend-tauri     # Nur Frontend – Tauri-App
./scripts/start-all.sh frontend-vite      # Nur Frontend – nur Vite-Server
```

---

## 0. PI-Installer (Kombi-Starter, empfohlen)

**Ein Starter für alles:** Das Skript wartet auf das Backend (läuft als Service), danach erscheint ein Dialog zur Auswahl.

### Terminal
```bash
./scripts/start-pi-installer.sh
```
- Wartet bis Backend antwortet (max. 60 s; Backend läuft als Service `pi-installer-backend`)
- Dialog (zenity/kdialog) oder Terminal-Auswahl: **Tauri** / **Browser** / **Nur Frontend**
- Tauri: mit `GDK_BACKEND=x11` (stabiles Rendering unter Wayland auf Pi)

### Desktop-Starter (mit Icon)
Alle Starter liegen im Ordner **Desktop/PI-Installer/**.

Einzelnen Starter anlegen:
```bash
bash scripts/desktop-pi-installer-launcher-anlegen.sh
```

Alle Starter anlegen (PI-Installer, Frontend-Varianten, DSI Radio, Bilderrahmen):
```bash
bash scripts/desktop-launcher-alle-anlegen.sh
```
Danach: Doppelklick auf **„PI-Installer“** im Ordner **PI-Installer** – wartet auf Backend, dann Auswahl.

### Auswahl ohne Dialog
```bash
PI_INSTALLER_MODE=tauri ./scripts/start-pi-installer.sh
PI_INSTALLER_MODE=browser ./scripts/start-pi-installer.sh
PI_INSTALLER_MODE=frontend ./scripts/start-pi-installer.sh
```

---

## 1. Backend (Service oder manuell)

**Erforderlich** – Frontend (Tauri oder Browser) und DSI-Radio (Sendersuche, Logos, Metadaten) benötigen das Backend.

- **Port:** http://localhost:8000  
- **API-Dokumentation:** http://localhost:8000/docs  

### Backend automatisch beim Boot starten (empfohlen)

Damit das Backend als Service beim Systemstart startet, einmalig ausführen:

```bash
./scripts/install-backend-service.sh
```

Das richtet den systemd-Service **pi-installer-backend** ein (enable + start). Danach läuft das Backend nach jedem Neustart automatisch.  
Status prüfen: `sudo systemctl status pi-installer-backend`  
Neustart nach Backend-Update: `./scripts/restart-backend-service.sh` oder `sudo systemctl restart pi-installer-backend`.

### Manuell starten

- **Als Service (falls bereits installiert):** `sudo systemctl start pi-installer-backend`  
- **Im Terminal (z. B. Entwicklung):** Im Projektroot `./scripts/start-backend.sh` – Backend läuft im Vordergrund bis Strg+C.

---

## 2. Frontend mit Tauri-App (eigenes Fenster)

Desktop-Anwendung mit eigenem Fenster – keine Browser-Leiste.

### Voraussetzung
- **Backend muss laufen** (in der Regel als Service `pi-installer-backend`)
- Rust/Tauri-Toolchain (bei erstem Aufruf: `cargo` wird genutzt)

### Terminal
```bash
./scripts/start-frontend-desktop.sh --window
# oder
./scripts/start-frontend-desktop.sh --tauri
```
- Startet Vite (Port 5173) + Tauri-Fenster
- Verbindet sich mit Backend unter 127.0.0.1:8000

### Direkt (im frontend/ Verzeichnis)
```bash
cd frontend
npm run tauri:dev
```
Startet automatisch das Backend im Hintergrund, falls es noch nicht läuft (via `beforeDevCommand`).

### Desktop-Starter
Nach `bash scripts/desktop-launcher-alle-anlegen.sh`:  
Im Ordner **Desktop/PI-Installer/** Doppelklick auf **„PI-Installer Frontend (App-Fenster)“**

---

## 3. Frontend im Browser

Web-Oberfläche im Standard-Browser.

### Voraussetzung
- **Backend muss laufen**

### Terminal
```bash
./scripts/start-frontend-desktop.sh --browser
```
- Startet Vite auf Port 3001
- Öffnet automatisch http://localhost:3001 im Standard-Browser

### Alternativ (manuell)
```bash
./scripts/start-frontend.sh
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
Im Ordner **Desktop/PI-Installer/** Doppelklick auf **„PI-Installer Frontend (Browser)“**

---

## 4. Alle Desktop-Starter anlegen

```bash
cd /pfad/zum/piinstaller
bash scripts/desktop-launcher-alle-anlegen.sh
```

Es wird der Ordner **Desktop/PI-Installer/** angelegt mit:
- **PI-Installer** – Kombi (wartet auf Backend-Service, dann Auswahl)
- **PI-Installer Frontend starten** (nur Vite-Server)
- **PI-Installer Frontend (App-Fenster)** – Tauri
- **PI-Installer Frontend (Browser)** – Vite + Browser
- **DSI Radio** – PyQt-Radio-App (Freenove-TFT/DSI)
- **Bilderrahmen** – Fotos im Loop (TFT-Seite)

---

## Reihenfolge

1. **Backend** läuft als Service (`pi-installer-backend`) – einrichten mit `./scripts/install-backend-service.sh`
2. **Frontend** starten (Tauri oder Browser) per Desktop-Starter oder Terminal

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
Erwartung: JSON-Antwort. Wenn nicht: Backend starten mit `./scripts/start-backend.sh` oder Service einrichten mit `./scripts/install-backend-service.sh`, danach `sudo systemctl start pi-installer-backend`.

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

---

## Fehlerbehebung: Tauri-App startet, Backend wird nicht erkannt

**Symptom:** Tauri-Fenster öffnet sich, aber „Server nicht erreichbar“ oder Sudo-Dialog bleibt hängen.

### 1. Entwicklung (npm run tauri:dev)
- Ab v1.3.8 startet `npm run tauri:dev` das Backend automatisch, falls es nicht läuft.
- Prüfen: `curl http://127.0.0.1:8000/api/version` – bei Fehler Backend manuell starten: `./scripts/start-backend.sh` (im Projektroot).

### 2. Gebaute App (Binary, .deb, AppImage)
- Die Tauri-Binary startet **kein** Backend – sie verbindet sich nur mit `http://127.0.0.1:8000`.
- **Lösung:** Backend zuerst starten oder **scripts/start-pi-installer.sh** nutzen (startet Backend + App).
- Desktop-Einträge von `install-desktop-entries.sh` nutzen bereits `start-pi-installer.sh` – Backend wird mitgestartet.
- Bei Installation nur der Tauri-.deb-Datei: Backend separat starten (`./scripts/start-backend.sh` oder Service).
