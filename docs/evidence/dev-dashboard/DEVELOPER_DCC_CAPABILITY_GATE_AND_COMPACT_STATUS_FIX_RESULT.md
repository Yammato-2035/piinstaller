# Developer DCC Capability Gate + Compact Status Fix

**Status:** `workspace_fix_verified`  
**Datum:** 2026-06-07

## Problem

Nach Deploy mit gültigem Developer-Token:

- `/api/dev-dashboard/status` → HTTP 200 (korrekt)
- `deploy_drift.status` → **rot**, weil `forbidden_api_paths_visible` `/api/dev-dashboard` enthielt
- DCC-UI zeigte zu viel Rohdaten (~178 KB Status-Payload)

## Fix

### 1. Gate-Trennung (`profile_deploy_manifest.py`)

| Feld | Bedeutung |
|------|-----------|
| `deploy_drift` | Datei-/Manifest-Sync (legacy + profile-aware merge) |
| `profile_exposure` | Unerlaubte Dev-API-Sichtbarkeit (ohne lokale Capability) |
| `developer_capability_exposure` | Lokal erlaubte DCC-Route-Registrierung mit `DCC_DEVELOPER_ENABLED` + Token |

Unter Release mit konfigurierter Developer-Capability: `/api/dev-dashboard` in `exempt_api_prefixes`, **nicht** in `forbidden_api_paths_visible`.

### 2. Kompaktstatus

- `GET /api/dev-dashboard/compact-status` — kleines JSON ohne Voll-Dashboard
- Felder: Profil, DCC, Capability, Deploy-Drift, Telemetrie, Rescue-ISO/USB, Blocker, nächste Aktion

### 3. UI

- `DccCompactOverviewPanel` — Standardansicht Ampel + nächste Aktion
- Roh-JSON nur in `<details>` (optional)

## Tests

- pytest: profile drift + compact status + status service (36+ passed)
- vitest: `dccCompactOverviewPanel`, `dccCompactStatus`, `dccGate`

## Security

- Release ohne Token: DCC blockiert
- Falsches Token: 404
- Telemetrie unabhängig erreichbar
- Keine Token-Werte in API/Evidence/UI

## Next Prompt

`RESCUE_USB_BOOT_AND_WINDOWS_INSPECT_OPERATOR_RUN`

Operator: Deploy + Frontend-Build nach `/opt`, Smoke wiederholen.
