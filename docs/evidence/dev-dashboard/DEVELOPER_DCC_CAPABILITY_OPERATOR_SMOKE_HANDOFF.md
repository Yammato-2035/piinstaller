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
DCC_DEVELOPER_ENABLED=1
DCC_DEVELOPER_TOKEN_FILE=/etc/setuphelfer/dcc_developer.token
DCC_ALLOWED_HOSTNAME=volker-ROG-Strix
# Optional separat:
# RESCUE_TELEMETRY_INGEST_ENABLED=1
```

Alternativ Token-Datei: `/etc/setuphelfer/dcc_developer.token` (Legacy: `developer.dcc.token`).

Backend-Restart nur mit **expliziter Operator-Freigabe**.

## Smoke-Schritte

### 1. Release-Referenz (ohne Token)

```bash
curl -sS http://127.0.0.1:8000/api/version | jq '{install_profile,dcc_allowed,developer_capability_available,rescue_telemetry_separate_from_dcc}'
curl -i http://127.0.0.1:8000/api/dev-dashboard/capability-status
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8000/api/dev-dashboard/status
# Erwartung unter release: 404 + PROFILE_ROUTE_BLOCKED oder DEVELOPER_CAPABILITY_*
curl -sS http://127.0.0.1:8000/api/rescue/telemetry/health
# Erwartung: 200 (Route nicht vom DCC-Gate blockiert) — nach Deploy auf /opt
```

### 2. Developer-Laptop (Release + lokale Capability)

```bash
# Token nur lokal — nicht ins Repo:
TOKEN="$(sudo cat /etc/setuphelfer/dcc_developer.token)"
curl -i -H "X-Setuphelfer-Developer-Token: $TOKEN" \
  http://127.0.0.1:8000/api/dev-dashboard/status
# Erwartung: HTTP 200 wenn DCC_DEVELOPER_ENABLED=1 und Hostname-Binding passt
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
