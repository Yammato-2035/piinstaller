# Developer DCC + Telemetrie — Operator Smoke Result

**Status:** `blocked_awaiting_operator_deploy_and_config`  
**Datum:** 2026-06-06  
**Workspace HEAD:** `efd3966` (vor Commit dieser Evidence ggf. neuer)

## Zusammenfassung

| Ziel | Ergebnis |
|------|----------|
| Release ohne Token blockiert DCC | **PASS** — `/api/dev-dashboard/status` → 404 `PROFILE_ROUTE_BLOCKED` |
| `capability-status` ohne Token erreichbar | **FAIL (Live)** — 404 `PROFILE_ROUTE_BLOCKED` wegen Deploy-Drift |
| Telemetrie-Health unter Release | **FAIL (Live)** — 404 Not Found (Router fehlt auf `/opt`) |
| Workspace-Unit/HTTP-Tests | **PASS** (21 pytest) |
| Operator-Smoke mit Token | **nicht ausgeführt** — `/etc/setuphelfer/dcc_developer.token` fehlt |
| USB-Write freigegeben | **nein** — DCC+Telemetrie-Live-Smoke ausstehend |

## Phase 0 — Live-Ist

```text
install_profile=release
dev_control_enabled=false
backend_runtime_path=/opt/setuphelfer/backend
```

| Endpunkt | HTTP | Code/Body |
|----------|------|-----------|
| `/api/dev-dashboard/status` | 404 | `PROFILE_ROUTE_BLOCKED` |
| `/api/dev-dashboard/capability-status` | 404 | `PROFILE_ROUTE_BLOCKED` |
| `/api/rescue/telemetry/health` | 404 | `{"detail":"Not Found"}` |

## Root Cause

1. **`/opt/setuphelfer/backend`** enthält weder `core/developer_capability.py` noch `rescue_telemetry/`.
2. **`route_exposure.py` auf `/opt`** blockiert `/api/dev-dashboard/*` bei `dev_control_enabled=false`, bevor `capability-status` ausgenommen werden kann.
3. Workspace-Code (Commit `efd3966`) ist korrekt; pytest bestätigt 200 für `capability-status` und Telemetrie-Health.

## Operator-Aktionen (Pflicht vor USB-Write)

1. **Deploy:** `docs/evidence/dev-dashboard/DEVELOPER_DCC_TELEMETRY_DEPLOY_OPERATOR_HANDOFF.md`
2. **Lokale Capability:** `docs/evidence/dev-dashboard/DEVELOPER_DCC_CAPABILITY_LOCAL_CONFIG_OPERATOR_HANDOFF.md`
3. Smoke erneut — JSON aktualisieren: `developer_dcc_and_telemetry_operator_smoke_latest.json`

## Erwartung nach erfolgreichem Operator-Lauf

| Check | Erwartung |
|-------|-----------|
| `capability-status` ohne Token | HTTP **200**, kein Secret |
| `status` ohne Token | HTTP **404** |
| `status` mit Token | HTTP **200** |
| `telemetry/health` | HTTP **200**, `profile_gate_independent: true` |
| DCC UI | Kompaktstatus, Telemetrie sichtbar, nicht leer |

## Secrets

Kein Token-Wert in diesem Dokument oder in JSON.

## Next Prompt

**Jetzt:** Operator muss Deploy + Config ausführen → danach Smoke wiederholen.

- Bei Erfolg: `RESCUE_USB_WRITE_OPERATOR_FOR_WINDOWS_INSPECT`
- Wenn `capability-status` nach Deploy noch blockiert: `DEVELOPER_DCC_CAPABILITY_ROUTE_GATE_FAILURE_TRIAGE`
- Wenn Telemetrie nach Deploy noch 404: `RESCUE_TELEMETRY_INGEST_LIVE_FAILURE_TRIAGE`

Strukturiert: `developer_dcc_and_telemetry_operator_smoke_latest.json`
