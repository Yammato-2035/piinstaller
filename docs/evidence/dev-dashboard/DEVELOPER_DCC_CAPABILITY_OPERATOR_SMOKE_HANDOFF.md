# Developer DCC Capability — Operator Smoke Handoff

**Status:** `prepared_awaiting_operator_runtime_smoke`  
**Parallel zu:** `RESCUE_USB_WRITE_OPERATOR_FOR_WINDOWS_INSPECT` (getrennte Tracks)

## Grundsatz

| System | DCC | Telemetrie |
|--------|-----|------------|
| Release ohne Token | blockiert | `/api/rescue/telemetry/health` erreichbar |
| Developer mit gültigem Token | `dcc_allowed=true` | separat via `RESCUE_TELEMETRY_INGEST_ENABLED` |
| Fremder Release-Rechner | blockiert | Health weiterhin erreichbar |

**Kein Token im Git. Kein Secret in Evidence. Kein Secret in API-Antworten.**

## Lokale Konfiguration (Operator)

Empfohlen: `/etc/setuphelfer/developer.env` (Dateirechte `0640`, root:setuphelfer)

Platzhalter — **echten Wert lokal setzen, nicht committen:**

```bash
# /etc/setuphelfer/developer.env — BEISPIEL, KEIN ECHTER TOKEN
DCC_DEVELOPER_TOKEN=<local-secret>
SETUPHELFER_INSTALL_PROFILE=developer
# Optional separat:
# RESCUE_TELEMETRY_INGEST_ENABLED=1
# RESCUE_TELEMETRY_INGEST_TOKEN=<separate-local-secret>
```

Alternativ Token-Datei: `/etc/setuphelfer/developer.dcc.token` (siehe `docs/knowledge-base/development/DCC_DEVELOPER_CAPABILITY.md`).

Backend-Restart nur mit **expliziter Operator-Freigabe**.

## Smoke-Schritte

### 1. Release-Referenz (ohne Token)

```bash
curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile,dcc_allowed,developer_capability_available,rescue_telemetry_separate_from_dcc}'
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/api/dev-dashboard/status
# Erwartung unter release: 404 + PROFILE_ROUTE_BLOCKED oder DEVELOPER_CAPABILITY_*
curl -sS http://127.0.0.1:8000/api/rescue/telemetry/health
# Erwartung: 200 (Route nicht vom DCC-Gate blockiert)
```

### 2. Developer mit Token

```bash
export DCC_DEVELOPER_TOKEN='<local-secret>'
curl -sS -H "X-Setuphelfer-Developer-Token: $DCC_DEVELOPER_TOKEN" \
  http://127.0.0.1:8000/api/dev-dashboard/status | head
# Erwartung: HTTP 200, DCC-Status-JSON (kein Secret in Response)
```

### 3. Negativtests

- Request ohne Header unter `developer`-Profil → `DEVELOPER_CAPABILITY_REQUIRED`
- Token in URL **verboten** — nur Header oder Bearer
- `/api/rescue/telemetry/v1/ingest` bleibt über Telemetrie-Policy, nicht DCC-Token

## Implementierung (Workspace)

- `backend/core/developer_capability.py`
- `backend/core/install_profile.py` — `path_allowed_for_active_profile()`
- `backend/runtime_governance/route_exposure.py` — Telemetrie ausgenommen
- `frontend/src/lib/devDashboard/dccGate.ts` — Disabled bei Capability-Fehler

## Evidence nach Smoke

- `docs/evidence/dev-dashboard/DEVELOPER_CAPABILITY_DCC_MODEL_RESULT.md` aktualisieren
- Keine Token-Werte in Logs/Evidence

**Next Prompt:** `DEVELOPER_DCC_CAPABILITY_OPERATOR_SMOKE`
