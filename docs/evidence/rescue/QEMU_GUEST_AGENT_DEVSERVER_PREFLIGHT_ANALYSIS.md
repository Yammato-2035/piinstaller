# QEMU Guest Agent — Devserver Preflight Analysis

**Datum:** 2026-06-03  
**Kontext:** Runtime während Ingest auf `release`; prior QEMU-Smokes ohne aktiven Host-Devserver.

## Aktueller Runtime-Stand (readonly)

| Feld | Wert |
|------|------|
| Aktuelles Profil | `release` |
| `profile_gate_status` | `green` |
| `dev_control_enabled` | `false` |
| `/api/dev-dashboard/status` erreichbar | **no** (HTTP 404) |
| `/api/fleet/sessions` erreichbar | **no** (HTTP 404) |
| `/api/rescue-agent/sessions` erreichbar | **no** (HTTP 404) |

Bei `release` ist **PROFILE_ROUTE_BLOCKED** erwartet (404 auf Dev-/Fleet-/Rescue-Agent-Routen).

## Ursache deaktivierter Development Server

**Klassifikation:** `release_profile_active` + `local_lab_not_enabled` + `devserver_routes_blocked`

- Backend läuft unter `install_profile=release`.
- `dev_control_enabled=false` → Dev-Dashboard/Fleet/Rescue-Agent-Router deaktiviert.
- Frühere Guest-Report-Ausfälle (`guest_report_missing`, `report_new=false`) sind **kein** Guest-Agent-Defekt, wenn der Host zu diesem Zeitpunkt keinen empfangsbereiten Devserver (`local_lab` + Fleet-API) hatte.

## Skript-Analyse

| Skript | Bisherige Prüfung |
|--------|-------------------|
| `qemu-guest-agent-smoke-operator.sh` | Manifest developer-qemu; schaltet `local_lab`; prüfte nur `install_profile==local_lab` |
| `run-qemu-developer-iso-smoke.sh` | Autopilot, Proxy Port 8001, Fleet-Session |
| `fleet-session-api.sh` | Fleet-API-Wrapper |

## Pflichtbefund

| Aussage | Wert |
|---------|------|
| QEMU-Smoke darf ohne local_lab nicht starten | **yes** |

**Empfehlung:** Preflight vor QEMU muss `dev_control_enabled`, Fleet-API 200 und Dev-Dashboard 200 erzwingen (implementiert in Phase 6).
