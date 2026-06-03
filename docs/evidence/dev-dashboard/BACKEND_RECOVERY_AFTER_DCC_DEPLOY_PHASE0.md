# Backend Recovery After DCC Deploy — Phase 0

**Datum:** 2026-06-03  
**HEAD:** `a5d57ed`  
**Branch:** `main`

| Feld | Wert |
|------|------|
| setuphelfer-backend.service | **active** (running) |
| setuphelfer.service | **active** |
| Port 8000 listening | **yes** |
| Port 3001 listening | **yes** |
| `/api/version` HTTP 200 | **yes** |
| systemd drop-ins | vorhanden (`install-profile.conf`, `90-devserver-local-lab.conf`, …) |
| Runtime-Profil (API) | `local_lab` |
| `dev_control_enabled` | `true` |
| systemd-Warnung | **daemon-reload erforderlich** (Unit-Dateien geändert) |

**Vorläufige Klassifikation:** `daemon_reload_required` → Operator-Recovery; Agent-Messung: **recovered**
