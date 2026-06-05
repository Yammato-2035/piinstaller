# DCC Frontend Profile Desync / False Release Disabled Page — Fix Result

**Datum:** 2026-06-05  
**HEAD:** `5efff70`  
**Branch:** `main`

## Phase 0 Runtime Truth (read-only checks)

### Backend / API

- `GET /api/version` (HTTP 200)
  - `install_profile`: `release`
  - `profile_gate_status`: `green`
  - `dev_control_enabled`: `false`
  - `backend_runtime_path`: `/opt/setuphelfer/backend`
- `GET /api/dev-dashboard/status` (HTTP 404)
  - `code`: `PROFILE_ROUTE_BLOCKED`
- `GET /api/dev-dashboard/backend-health` (HTTP 404)
  - `code`: `PROFILE_ROUTE_BLOCKED`
- `GET /api/dev-dashboard/recent-evidence` (HTTP 404)
  - `code`: `PROFILE_ROUTE_BLOCKED`
- `GET /api/fleet/sessions` (HTTP 404)
  - `code`: `PROFILE_ROUTE_BLOCKED`

### Frontend / Ports

- Browser UI `http://127.0.0.1:3001/?window=cockpit` (HTTP 200)
- nginx `http://127.0.0.1:8080/` (HTTP 200, not SetupHelfer DCC)

## Problem Summary

Die Seite „Development Control nicht verfügbar“ wurde im Frontend weiterhin angezeigt, obwohl in dem betroffenen Szenario die Runtime-API Dev-Routen freigeben konnte.

## Root Cause

`frontend/src/pages/ExternalDevelopmentControlCenter.tsx` hat die Disabled-Page bislang (teilweise) anhand eines **Build-Time Markers** (`devControlUiEnabled`) gerendert.

Dadurch konnte ein **staler/inkonsistenter Build- oder Profilmarker** im Browser die Disabled-Page „release-disabled“ festhalten, obwohl die serverseitige Wahrheit (`/api/dev-dashboard/status`) Dev-Control eigentlich erlauben sollte.

## Fix (Frontend-Gating)

1. **Source-of-Truth:** `GET /api/dev-dashboard/status`
2. **Cache-Hardening:** `cache: "no-store"` und Query-Param `?t=<Date.now()>`
3. **Entscheidung:** Wenn `/api/dev-dashboard/status` **HTTP 200** liefert, wird die Disabled-Page nicht angezeigt (unabhaengig vom `/api/version` Snapshot).
4. **Debug-Unterstuetzung (Disabled-Page):** zeigt
   - zuletzt abgefragte API-URLs
   - HTTP-Codes von `/api/version` und `/api/dev-dashboard/status`
   - `backend code` aus der Status-Response (z. B. `PROFILE_ROUTE_BLOCKED`)
   - Ports aus `runtime_ports` (API/UI/nginx sowie optional QEMU Ports)
5. **No runtime actions:** nur fetch/caching + UI-Logik.

## Tests (keine Runtime-Aktionen)

- `npm --prefix frontend run build`: OK
- `npm --prefix frontend run test -- --run`: OK
- Unit-Tests: `frontend/src/lib/devDashboard/dccGate.test.ts`

## Aktueller Status / verbleibender Operator-Check

In dieser konkreten Phase ist die Runtime weiterhin im `release`-Blocker-Zustand (erwartet): `/api/dev-dashboard/status` ist 404 `PROFILE_ROUTE_BLOCKED`, daher bleibt die Disabled-Page korrekt sichtbar.

**Nächster Pflicht-Check (Operator, local_lab-Szenario):**

Wenn die Runtime-API `local_lab` meldet und `/api/dev-dashboard/status` **HTTP 200** liefert, muss das Frontend **die Disabled-Page nicht mehr** anzeigen. Das ist jetzt ein Frontend-Gating-Verhalten, das über `/api/dev-dashboard/status` als Wahrheit abgesichert ist.

