# Rescue Telemetry Ingest — Operator Smoke Handoff

**Status:** `prepared_awaiting_operator_runtime_smoke`  
**Getrennt von:** DCC Developer-Capability (`/api/dev-dashboard/*`)

## Grundsatz

- `GET /api/rescue/telemetry/health` ist unter **Release** erreichbar (kein `PROFILE_ROUTE_BLOCKED`).
- `POST /api/rescue/telemetry/v1/ingest` folgt `RESCUE_TELEMETRY_INGEST_ENABLED`, nicht dem DCC-Token.
- Kein Secret im Repo, in Evidence oder in API-Antworten.

## Lokale Konfiguration (Platzhalter)

```bash
# /etc/setuphelfer/developer.env — BEISPIEL
RESCUE_TELEMETRY_INGEST_ENABLED=1
# RESCUE_TELEMETRY_INGEST_TOKEN=<separate-local-secret>
# RESCUE_TELEMETRY_INGEST_STORAGE_ROOT=docs/evidence/runtime-results/rescue/telemetry-ingest
```

Backend-Restart nur mit **expliziter Operator-Freigabe** nach Env-Änderung.

## Smoke-Schritte

### 1. Health unter Release

```bash
curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile,backend_runtime_path}'
curl -i http://127.0.0.1:8000/api/rescue/telemetry/health
# Erwartung: HTTP 200, ingest_enabled false/true je nach Env, profile_gate_independent true
```

### 2. Ingest disabled

```bash
curl -i -X POST http://127.0.0.1:8000/api/rescue/telemetry/v1/ingest \
  -H 'Content-Type: application/json' -d '{}'
# Erwartung: HTTP 503, code TELEMETRY-DISABLED-001 — nicht PROFILE_ROUTE_BLOCKED
```

### 3. Ingest enabled (Operator)

```bash
export RESCUE_TELEMETRY_INGEST_ENABLED=1
# Envelope aus Operator-Lauf — kein Sample als Evidence committen
curl -i -X POST http://127.0.0.1:8000/api/rescue/telemetry/v1/ingest \
  -H 'Content-Type: application/json' \
  -H 'X-Setuphelfer-Payload-Hash: <hash>' \
  -d @/path/to/envelope.json
# Erwartung: HTTP 200 acknowledged oder 202 queued
```

### 4. DCC-Diagnose parallel

```bash
curl -sS http://127.0.0.1:8000/api/dev-dashboard/capability-status | jq .
```

## Deploy-Hinweis

Wenn `/api/rescue/telemetry/health` **404 Not Found** liefert, fehlt der Router in der produktiven Runtime unter `/opt/setuphelfer`. Workspace-Code deployen und Backend nur mit Operator-Freigabe neu starten.

## Evidence nach Smoke

- `docs/evidence/dev-dashboard/RESCUE_TELEMETRY_INGEST_OPERATOR_SMOKE_RESULT.md` (Operator)
- Keine Token-Werte in Logs/Evidence

**Next Prompt nach erfolgreichem Smoke:** `RESCUE_USB_WRITE_OPERATOR_FOR_WINDOWS_INSPECT` (parallel USB-Track)  
**Bei Health 404/503 Deploy-Drift:** `RESCUE_TELEMETRY_INGEST_LIVE_FAILURE_TRIAGE`
