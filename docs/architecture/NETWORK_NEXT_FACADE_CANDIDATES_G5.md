# Network Next Facade Candidates — G.5

**HEAD:** `307c411` · **Status:** Audit only — keine Implementierung

## Bewertungskriterien

- Kopplung zu `app.py`
- G.4-Blocker-Status
- Frontend-Abhängigkeit
- Risiko bei Migration (Response-Contract)
- Legacy-Elimination-Beitrag

## Kandidaten

### 1. System Info Facade (G.6)

| Feld | Wert |
|------|------|
| **Pfad (vorgeschlagen)** | `backend/core/system_info_facade.py` |
| **Scope** | `GET /api/system-info` Aggregation (psutil, Hardware, Sensoren, OS) |
| **Network** | `network`-Block delegiert weiter an `network_info_facade` |
| **Priorität** | **HIGH** |
| **Begründung** | Größter verbleibender Monolith-GET (~240 Zeilen); 4 Frontend-Konsumenten; G.4 als blocked dokumentiert |
| **Blocker** | Viele app-Helfer (`get_cpu_name`, `get_all_disks`, Pi-Modul) — schrittweise Adapter wie G.2 |
| **Router danach** | `api/routes/system_info.py` (optional G.6b) |

### 2. Webserver Status Facade (G.7)

| Feld | Wert |
|------|------|
| **Pfad (vorgeschlagen)** | `backend/core/webserver_status_facade.py` |
| **Scope** | `GET /api/webserver/status` Payload |
| **Priorität** | **HIGH** |
| **Begründung** | G.4-blockiert wegen `run_command`/`systemctl`; direkter `_detect_frontend_port`-Bypass |
| **Abhängigkeiten** | `get_running_services`, `get_installed_apps`, `get_website_names`, `ss`, Facade-Network |
| **Router danach** | `api/routes/webserver.py` (optional G.7b) |

### 3. Frontend Runtime Facade

| Feld | Wert |
|------|------|
| **Pfad (vorgeschlagen)** | `backend/core/frontend_runtime_facade.py` |
| **Scope** | Frontend-Port, Dev/Build-Runtime-Erkennung (5173/3001/3002) |
| **Priorität** | **MEDIUM** |
| **Begründung** | Querschnitt: `system/network` + `webserver/status`; eliminiert direkten `_detect_frontend_port`-Bypass |
| **Abhängigkeit** | `_detect_frontend_port` (16 Zeilen, `ss`) |
| **Kann** | Vor oder mit G.7 umgesetzt werden |

### 4. Port Detection Facade

| Feld | Wert |
|------|------|
| **Pfad (vorgeschlagen)** | `backend/core/port_detection_facade.py` oder Teil von Frontend Runtime |
| **Scope** | Nur Port-Scan-Logik |
| **Priorität** | **LOW** (als eigenständiges Modul) / **MEDIUM** (als Teil Frontend Runtime) |
| **Begründung** | Kleine Funktion; eigenes Modul nur sinnvoll wenn Frontend Runtime Facade zu breit wird |
| **Empfehlung** | Mit Frontend Runtime Facade zusammenführen, nicht separater Track |

### 5. Network Discovery Core (optional G.8)

| Feld | Wert |
|------|------|
| **Pfad (vorgeschlagen)** | `backend/core/network_discovery.py` |
| **Scope** | `get_network_info` Implementierung (ip/hostname) |
| **Priorität** | **CRITICAL** (für Legacy-Elimination) |
| **Begründung** | Bricht `facade → import app`-Zyklus; kein HTTP-Change nötig |
| **Reihenfolge** | Nach oder parallel zu G.6/G.7 — unabhängig von Router-Migration |

## Priorisierungsmatrix

| Kandidat | Priorität | Aufwand | Legacy-Elimination | Router-fähig |
|----------|-----------|---------|-------------------|--------------|
| Network Discovery Core (G.8) | **CRITICAL** | mittel | **hoch** | nein (intern) |
| System Info Facade (G.6) | **HIGH** | hoch | mittel | ja |
| Webserver Status Facade (G.7) | **HIGH** | mittel | mittel | ja |
| Frontend Runtime Facade | **MEDIUM** | niedrig | mittel | teilweise |
| Port Detection (standalone) | **LOW** | niedrig | niedrig | nein |

## Empfohlene Entscheidung

| Option | Wann wählen |
|--------|-------------|
| **G.6 System Info Facade** | Fokus Monolith-Reduktion, Dashboard-Polling, größter Handler |
| **G.7 Webserver Status Facade** | Fokus Network-Legacy-Bypass (`_detect_frontend_port`), kleinerer Scope, schnellerer Win |
| **G.8 Network Discovery** | Fokus reine Legacy-Elimination ohne neue HTTP-Facade |
| **Neuer Architektur-Track** | Wenn Hardware/Systeminfo und Webserver parallel owned werden sollen → „Platform Runtime Facade“ als Umbrella |

**Audit-Empfehlung:** **G.8 (Discovery)** oder **G.7 (Webserver)** zuerst — kleinerer Scope, schließt direkten Network-Legacy-Bypass. **G.6** als größter Monolith-Slice danach.

## Nicht-Ziele (bestätigt G.5)

Keine API-, Route- oder Response-Änderung in dieser Phase.
