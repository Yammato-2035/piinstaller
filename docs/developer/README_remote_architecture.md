# Remote Companion – Architektur & Integrationsplan (Phase 1)

Dieses Dokument beschreibt die Bestandsaufnahme des PI-Installer-Projekts und die geplante Integration des **modularen Smartphone-Companion-Systems** (QR-Pairing, Session, Rollen, Modul-Registry, REST + WebSocket, PWA). Es gilt ausschließlich für **Phase 1 / Control Plane**; Dateisync, CalDAV/CardDAV und Cloud-Sync sind ausdrücklich nicht Teil dieser Phase.

---

## 1. Bestandsaufnahme: Aktuelle Projektstruktur

### 1.1 Backend

- **Einstiegspunkt:** `backend/app.py` – eine zentrale FastAPI-App (`app = FastAPI(...)`).
- **Router:** Es gibt **keine** getrennten APIRouter; alle Endpoints werden direkt an `app` registriert (`@app.get(...)`, `@app.post(...)` usw.). Routen leben vollständig in `app.py`.
- **Module:** Unter `backend/modules/` existieren inhaltliche Module (z. B. `security.py`, `users.py`, `devenv.py`, `webserver.py`, `mail.py`, `backup.py`, `raspberry_pi_config.py`, `control_center.py`), die von `app.py` importiert und genutzt werden. Sie exportieren Klassen (z. B. `SecurityModule`, `UserModule`, `ControlCenterModule`) und werden in `backend/modules/__init__.py` gebündelt.
- **Models/Services:** Keine zentrale Pydantic-Model-Sammlung; Request/Response-Strukturen sind teils inline in `app.py`, teils in den Modulen. Typisierung ist uneinheitlich.
- **Datenbank:** Kein allgemeines DB-Framework. SQLite wird **nur** an wenigen Stellen in `app.py` verwendet (z. B. Radio-Stationen/Metadaten). Konfiguration: `config.json` über `_config_path()` (Priorität: `/etc/pi-installer/config.json`, Fallback `~/.config/pi-installer/config.json`); Einstellungen in `APP_SETTINGS` / `CONFIG_STATE`.
- **Auth/Session:** Keine echte Benutzer-Auth für die API. Session-relevant ist nur ein **in-memory** `sudo_password_store` in `app.py` für sudo-Passwort während der Laufzeit. Keine Tokens, kein JWT, keine persistente Session-Datenbank.

### 1.2 Frontend

- **Einstieg:** `frontend/src/main.tsx` → `App.tsx`.
- **Routing:** Kein React Router; **zustandsbasiertes Routing** über `currentPage` (useState) und optional `?page=...` (URLSearchParams). `App.tsx` definiert den Typ `Page` und einen großen `switch (currentPage)` in `renderPage()`.
- **Seiten:** Alle Seiten liegen unter `frontend/src/pages/`. Navigation über `Sidebar.tsx` und (optional) direkte Links mit `?page=...`.
- **State:** Lokaler React-State in `App.tsx` (systemInfo, theme, firstRunDone, backendError, …); `api.ts` mit `getApiBase()`/`setApiBase()` und optional localStorage (`API_BASE_STORAGE_KEY`, Theme). Kein Redux/Zustand für globalen App-State; Kontext nur `PlatformContext` für plattformspezifische Infos.
- **API-Zugriff:** `frontend/src/api.ts` – `fetchApi(path, init)` mit konfigurierbarer Basis-URL (Tauri vs. Browser, Screenshot-Modus).

### 1.3 Weitere relevante Punkte

- **Backend-Start:** `start-backend.sh` startet Uvicorn mit `app:app`, Host `0.0.0.0`, Port aus `PI_INSTALLER_BACKEND_PORT` (Standard 8000), ein Worker.
- **WebSocket:** Derzeit **nicht** vorhanden (kein WebSocket-Endpoint, kein Eventbus).
- **Sabrina Tuner / DSI-Radio:** Über `?view=dsi-radio` wird eine spezielle kompakte UI (Radio-Player) angezeigt; Backend bietet zahlreiche `/api/radio/...` Endpoints. Wird als eigenes „Modul“ für die Remote-Companion-Stubs genutzt.

---

## 2. Integrationspunkte für Remote-Companion

- **Backend:** Remote-Funktionalität sollte **nicht** alles in `app.py` stopfen. Empfohlen:
  - Eigener **Namespace** für Remote: z. B. alle Routen unter `/api/remote/...` (Pairing, Session, Module, State, Actions).
  - Eigene **Substruktur** unter `backend/` (z. B. `backend/remote/`), die Router, Services und Pydantic-Modelle bündelt; in `app.py` wird nur ein einziger inkludierter Router eingehängt (`app.include_router(remote_router, prefix="/api/remote", tags=["remote"])`). So bleibt die bestehende Architektur erhalten, keine doppelten Strukturen.
- **Konfiguration:** Nutzung der bestehenden Config-Pfade für Remote-relevante Einstellungen (z. B. „Remote aktiviert“, Pairing-Timeout), wo sinnvoll in `APP_SETTINGS`/config.json erweitern, statt neuer paralleler Config-Dateien.
- **Frontend:** Zwei sinnvolle Varianten:
  - **A)** Eine neue „Seite“ im bestehenden Frontend (z. B. `page='remote-companion'` oder `remote`) für Admin/Setup (QR anzeigen, gekoppelte Geräte verwalten) – Sidebar + App.tsx um einen Eintrag erweitern.
  - **B)** Eine **eigenständige PWA** (z. B. unter `frontend/remote-pwa/` oder `frontend/companion/`), die nur für Smartphone-Companion genutzt wird und auf dieselbe Backend-API zugreift. Für Phase 1 kann beides vorbereitet werden; Fokus „Responsive PWA für Smartphone“ spricht für eine **eigenständige PWA**, die unter gleicher Domain (oder Subpath) ausgeliefert wird und die bestehende API + neue `/api/remote/*` nutzt.
- **Auth/Sicherheit:** Das aktuelle System hat keine API-Auth. Für Remote müssen **Pairing und Session** neu eingeführt werden (siehe unten). Bestehende Auth-Logik gibt es nicht zu „verändern“ – nur ergänzen für den neuen Pfad `/api/remote/*`.

---

## 3. Warum PWA zuerst, WLAN primär, Control Plane getrennt

- **PWA zuerst:** Keine native Mobile-App in Phase 1; geringerer Aufwand, eine Codebasis (Web), einfache Updates über Backend-Deployment. PWA erlaubt „Zum Homescreen hinzufügen“, Offline-Anzeige von statischen Teilen und ein einheitliches UI auf allen Geräten.
- **WLAN primär:** Der Pi und das Smartphone sind typischerweise im gleichen Netzwerk; WLAN ist für Steuerung und Live-Status ausreichend und vermeidet Bluetooth-Komplexität (Pairing, Profile, Plattformunterschiede). Spätere Erweiterung um Bluetooth optional denkbar, aber nicht Haupttransport.
- **Control Plane getrennt von Sync/Cloud:** Steuerung („Modul X starten“, „Status abfragen“, „Einstellung setzen“) und Daten-Sync (Dateien, Kalender, Kontakte) haben unterschiedliche Anforderungen (Latenz, Konfliktbehandlung, Speicher). Phase 1 liefert nur die **Steuerungsebene** (REST + WebSocket); Dateisync, CalDAV/CardDAV und Cloud-Sync werden weder in derselben API-Logik vermischt noch implementiert.

---

## 4. Ziel-Dateibaum (neue/erweiterte Bereiche)

Nachfolgend der **Ziel-Dateibaum** nur für die neuen bzw. erweiterten Bereiche. Bestehende Dateien, die nur punktuell erweitert werden, sind mit „(erweitern)“ gekennzeichnet.

```
backend/
  app.py                          # (erweitern) include_router(remote_router, prefix="/api/remote", ...)
  modules/                        # unverändert; keine Duplikation
  remote/                         # NEU – Remote Companion
    __init__.py
    router.py                     # FastAPI APIRouter für /api/remote/*
    models.py                     # Pydantic-Modelle (Pairing, Session, Module, Rollen)
    pairing.py                    # QR-Pairing, Token-Erzeugung, Speicherung (nicht Klartext)
    session.py                    # Session-Handling, Ablauf, Refresh
    permissions.py                # Rollen/Rechte (z. B. viewer, operator, admin)
    registry.py                   # Modul-Registry (registrierte Remote-Module)
    events.py                     # WebSocket-Eventbus (Live-Status)
    stubs/
      __init__.py
      sabrina_tuner.py            # Stub: Sabrina Tuner (State/Actions)
      pi_installer.py              # Stub: PI-Installer (State/Actions)

frontend/
  src/
    App.tsx                       # (erweitern) optional: Seite 'remote-companion' für Admin/QR
    components/
      Sidebar.tsx                 # (erweitern) optional: Menüpunkt „Remote Companion“
  remote-pwa/                     # NEU – eigenständige PWA für Smartphone (oder companion/)
    index.html
    src/
      main.tsx
      App.tsx
    package.json
    vite.config.ts
    # … PWA-Manifest, Service Worker, Build auf Subpath oder eigene Origin

docs/
  remote_companion.md             # NEU – Nutzer-/Entwickler-Doku Remote Companion
```

Keine neuen Top-Level-Skripte oder Änderungen an Bootreihenfolge, `config.txt`, NVMe-/SD-Bootlogik oder Installer-Nebenbaustellen.

---

## 5. Dateien: neu vs. erweitern

| Aktion    | Datei/ Bereich |
|----------|-----------------|
| **Neu**  | `backend/remote/__init__.py` |
| **Neu**  | `backend/remote/router.py` |
| **Neu**  | `backend/remote/models.py` |
| **Neu**  | `backend/remote/pairing.py` |
| **Neu**  | `backend/remote/session.py` |
| **Neu**  | `backend/remote/permissions.py` |
| **Neu**  | `backend/remote/registry.py` |
| **Neu**  | `backend/remote/events.py` |
| **Neu**  | `backend/remote/stubs/__init__.py` |
| **Neu**  | `backend/remote/stubs/sabrina_tuner.py` |
| **Neu**  | `backend/remote/stubs/pi_installer.py` |
| **Neu**  | `frontend/remote-pwa/` (kompletter PWA-Baum) |
| **Neu**  | `docs/remote_companion.md` |
| **Erweitern** | `backend/app.py` – nur Router-Include und ggf. CORS/WebSocket-Mount für `/api/remote` und Eventbus |
| **Erweitern** (optional) | `frontend/src/App.tsx`, `frontend/src/components/Sidebar.tsx` – eine Seite + Menüpunkt für Admin/QR im Desktop-Frontend |

In **Arbeitspaket 1** wird **ausschließlich** diese Architekturdatei (`README_remote_architecture.md`) angelegt. Noch **keine** Code-Änderungen an `app.py`, Frontend oder neuen Backend-Dateien – die Tabelle dient als Plan für spätere Arbeitspakete.

---

## 6. Abnahmekriterium Arbeitspaket 1

- Architektur ist schriftlich dokumentiert (dieses Dokument).
- Bestehende App startet weiterhin (keine Funktionsänderung).
- Keine unnötigen Funktionsänderungen; keine neuen Dateien außer dieser README und ggf. Verweis in der Haupt-README/Doku.

---

## 7. Risiken und Hinweise (für spätere Pakete)

- **Sicherheit:** Pairing- und Session-Tokens dürfen **nicht im Klartext** persistiert werden; Speicherung gehashed oder verschlüsselt. Keine Erweiterung der bestehenden `sudo_password_store`-Logik für Remote – eigene, abgegrenzte Speicherung.
- **Bestehende Auth/Settings/Registry:** Es gibt derzeit keine zentrale Auth oder Modul-Registry; beides wird **neu** nur im Kontext `backend/remote/` eingeführt, ohne bestehende Endpoints zu verändern.
- **Router/Import:** Sobald umgesetzt: Nur **ein** neuer Einstieg in `app.py` (`include_router`); alle Remote-Routen unter einem Prefix. Keine Streuung von Remote-Logik in bestehende Endpoints.
- **Datenbank:** Falls Phase 1 persistente Pairings/Sessions braucht: entweder erweiterte Nutzung von SQLite in einem dedizierten Schema/Datei unter `remote/` oder konfigurierter Pfad – kein Umbau der bestehenden Config- oder Radio-DB.

---

*Stand: Arbeitspaket 1 – nur Bestandsaufnahme und Architektur; keine Code-Änderungen außer dieser Datei.*
