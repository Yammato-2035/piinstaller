# Linux Companion – Übersicht & Architektur

Das **modulare Smartphone-Companion-System** (Linux Companion) ermöglicht die Steuerung des PI-Installers und angeschlossener Apps (z. B. DSI-Radio/Sabrina Tuner) über eine PWA auf dem Smartphone im gleichen WLAN. Läuft auf **Raspberry Pi** und **Linux-Desktops**. **Phase 1** umfasst ausschließlich die **Control Plane**: Pairing (mit QR-Code auf allen Plattformen), Session, Rollen, Modul-Registry, REST-API und WebSocket-Eventbus. Dateisync, CalDAV/CardDAV und Cloud-Sync sind nicht Teil von Phase 1.

- **Entwicklerleitfaden** (neues Modul anlegen, Widgets, Aktionen, Events): siehe [REMOTE_COMPANION_DEV.md](./REMOTE_COMPANION_DEV.md).

---

## 1. Ablauf aus Nutzersicht

1. **Backend** auf dem Pi läuft; Remote-Feature ist in den Einstellungen aktiviert.
2. **Pairing:** Am Linux-Gerät (Pi, Desktop) wird ein neues Pairing erstellt; ein **QR-Code** wird angezeigt (auch auf Linux-Desktop, nicht nur Pi).
3. **Smartphone:** Nutzer öffnet die PWA (z. B. `http://<host-ip>:3001` – Frontend-Port – mit Seite „Linux Companion“), scannt den QR-Code bzw. gibt den Token ein und löst das Pairing ein (**Claim**). API-Backend läuft auf Port 8000.
4. **Session:** Nach erfolgreichem Claim erhält die PWA ein **Session-Token** (wird z. B. im localStorage gespeichert). Alle weiteren API-Aufrufe und der WebSocket nutzen dieses Token.
5. **Dashboard:** Die PWA zeigt Geräte-Info und die Liste der **Module** (z. B. Sabrina Tuner, PI-Installer). Pro Modul können **Status** abgefragt und **Aktionen** ausgeführt werden (je nach Rolle).
6. **Live-Updates:** Optional verbindet sich die PWA per **WebSocket** (`/api/ws?session=TOKEN`) und erhält Events (z. B. Lautstärke geändert, Now Playing, Job-Fortschritt).

---

## 2. Architektur (Phase 1)

### 2.1 Backend

- **Einstieg:** `backend/app.py` – FastAPI-App; beim Start werden Config geladen, Remote-DB initialisiert und `app.state.app_settings`, `app.state.device_id` gesetzt.
- **Router:** Alle Remote-Endpoints liegen unter `backend/api/routes/` und werden per `app.include_router(...)` eingebunden:
  - **Pairing:** `pairing.py` – Erzeugen und Einlösen von Pairing-Tickets (QR/Token).
  - **Sessions:** `sessions.py` – Session-Info, Refresh, Logout.
  - **Gerät:** `devices.py` – Geräte-Info (device_id, Name).
  - **Module:** `modules.py` – Liste der Module, Modul-Beschreibung, Modul-State.
  - **Aktionen:** `actions.py` – Ausführen von Modul-Aktionen (Schreibrecht erforderlich).
  - **WebSocket:** `ws.py` – Live-Eventbus unter `/api/ws?session=TOKEN`.
- **Kernlogik:** `backend/core/` – Auth (Session-Validierung), Permissions (Rollen), Registry (Modulvertrag), Eventbus, QR-Payload.
- **Persistenz:** SQLite-Datenbank (Pfad über Config oder `PI_INSTALLER_REMOTE_DB`), Tabellen: `pairing_tickets`, `sessions`, `remote_device_profiles`, `audit_log`. Tokens werden gehashed gespeichert, nicht im Klartext.
- **Module/Services:** Implementierungen in `backend/services/` (z. B. `sabrina_tuner_service.py`, `pi_installer_service.py`); Registrierung über `services/module_loader.py` in der zentralen `ModuleRegistry`.

### 2.2 Frontend (PWA)

- **Ort:** `frontend/src/features/remote/` – API-Client, Store (Zustand), Seiten (Pair, Dashboard, Modul-Detail), Komponenten (StatusCard, VolumeSlider, …).
- **Navigation:** Im Haupt-Frontend existiert die Seite `remote` (Menüpunkt „Linux Companion“); ohne Session wird die **Pair-Seite** (mit QR-Code-Anzeige auf allen Plattformen), mit Session **Dashboard** oder **Modul-Detail** angezeigt.
- **Session:** Token wird im localStorage unter `pi-installer-remote-session` gespeichert; REST-Requests nutzen `Authorization: Bearer <token>`; WebSocket: `?session=<token>`.

---

## 3. API-Übersicht

| Methode | Endpoint | Beschreibung | Auth |
|--------|----------|--------------|------|
| POST | `/api/pairing/create` | Neues Pairing-Ticket erzeugen (QR/Token) | – (Feature-Flag prüfen) |
| POST | `/api/pairing/claim` | Ticket einlösen, Session erhalten | – |
| GET | `/api/sessions/me` | Aktuelle Session-Info | Session |
| POST | `/api/sessions/refresh` | Session verlängern | Session |
| DELETE | `/api/sessions/me` | Session beenden | Session |
| GET | `/api/device` | Geräte-Info (device_id, Name) | Session |
| GET | `/api/modules` | Liste aller Module (Deskriptoren) | Session |
| GET | `/api/modules/{id}` | Ein Modul (Deskriptor) | Session |
| GET | `/api/modules/{id}/state` | Aktueller Modul-State | Session |
| POST | `/api/modules/{id}/actions/{action_id}` | Aktion ausführen | Session (mind. controller) |
| WS | `/api/ws?session=TOKEN` | WebSocket für Live-Events | Session (Query) |

- **Session:** Bearer-Token im Header `Authorization: Bearer <token>` oder bei GET optional als Query-Parameter `session=<token>`.
- **Fehler:** 401 bei fehlender/ungültiger Session, 403 bei unzureichenden Rechten (z. B. viewer darf keine Aktionen auslösen), 404 bei unbekanntem Modul.

---

## 4. Datenmodell (Kernbegriffe)

- **Pairing-Ticket:** Einmaliges Ticket (status: pending → claimed/expired), TTL konfigurierbar; nach Claim wird eine Session und ein Geräteprofil angelegt.
- **Session:** session_id, token (gehasht gespeichert), device_id, expires_at, refreshed_at.
- **Geräteprofil:** device_id, name, role (viewer, controller, admin, sync); wird beim Claim angelegt.
- **Audit-Log:** Einträge für sicherheitsrelevante Ereignisse (z. B. session_created).

---

## 5. Rollen & Berechtigungen

| Rolle | Lesen (State, Module, Gerät) | Aktionen ausführen (POST …/actions/…) |
|------|-----------------------------|----------------------------------------|
| viewer | ja | nein |
| controller | ja | ja |
| admin | ja | ja (+ Admin-Funktionen) |
| sync | für spätere Sync-Integration vorgesehen | – |

- Beim **Claim** wird dem Gerät standardmäßig die Rolle **viewer** zugewiesen; eine spätere Erweiterung um konfigurierbare Rollen pro Gerät ist möglich.
- **Aktionen-Endpunkt** verlangt mindestens Rolle **controller** (`require_write`).

---

## 6. Events (WebSocket)

- **Verbindung:** `WS /api/ws?session=TOKEN`. Bei ungültiger Session: Close mit Code **4401**.
- **Nachrichten:** JSON-Objekte mit `type`/`topic`, `payload`, `ts` (ISO-8601).
- **Bekannte Topics** (siehe `backend/models/events.py`):
  - `module.state.changed` – Modul-State hat sich geändert.
  - `log.line` – Log-Zeile (z. B. PI-Installer-Job).
  - `job.progress` – Job-Fortschritt.
  - `tuner.now_playing` – Sabrina Tuner: Now Playing.
  - `tuner.volume_changed` – Lautstärke/Stummschaltung.
  - `sync.status.changed` – (Phase 2) Sync-Status.

Clients können nach Verbindung auf alle vom Server gesendeten Events reagieren; ein explizites Subscribe pro Topic ist derzeit nicht nötig (Broadcast).

---

## 7. Konfiguration

- **Einstellungen** (z. B. in `config.json` unter `settings.remote` oder über die App-Einstellungen):
  - Remote aktivieren/deaktivieren
  - Pairing-TTL (Sekunden)
  - Session-TTL (Sekunden)
  - Basis-URL für QR (optional)
  - Gerätename (optional)
- **Datenbank:** SQLite; Pfad über Konfiguration oder Umgebungsvariable `PI_INSTALLER_REMOTE_DB` (z. B. für Tests).

---

## 8. Phase 2 (konzeptionell)

Folgende Punkte sind **nicht** in Phase 1 implementiert, aber als spätere Integrationspunkte vorgesehen:

- **Sync-Status:** Topic `sync.status.changed` und ggf. Endpoints für Sync-Status (z. B. Ordner-Sync, Cloud-Sync).
- **Ordner-Profile / Folder-Profile:** Konfigurierbare Sync-Ordner pro Gerät oder Profil.
- **CalDAV/CardDAV:** Healthcheck und Anzeige des DAV-Status (nur konzeptionell; keine Implementierung in Phase 1).
- **Dateisync:** Kein Datei-Transfer in Phase 1; nur Control Plane (Steuerung, Status, Live-Events).

Die bestehende API und die Modul-Registry sind so angelegt, dass spätere Module (z. B. „Sync“, „DAV-Status“) ohne Änderung der REST-Struktur ergänzt werden können.

---

*Stand: Phase 1 (Control Plane) umgesetzt; Dokumentation mit Arbeitspaket 10.*
