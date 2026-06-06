# Developer Capability and DCC Profile Model

## Profiles

| Profile | DCC API | DCC UI | Telemetrie `/api/rescue/telemetry/*` |
|---------|---------|--------|--------------------------------------|
| `release` | blockiert ohne lokale Developer-Capability | Disabled-Seite mit Diagnose | separat erreichbar |
| `production` | wie release | wie release | separat |
| `developer` | mit gültiger Developer-Capability | sichtbar bei `dcc_allowed=true` | separat |
| `local_lab` | wie developer | wie developer | separat |

**Development Server auf Release:** nur wenn Host-Capability konfiguriert ist (`DCC_DEVELOPER_ENABLED` + Token-Datei/Env). DCC-Token allein reicht nicht für fremde Rechner ohne Host-Konfiguration.

## Sichtbarkeitsmodell

DCC darf sichtbar sein, wenn:

1. `install_profile` in `developer`, `local_lab` **und** `dev_control_enabled=true` **und** gültiges Token **oder**
2. `install_profile` == `release` **und** lokale Developer-Capability gültig ist

Lokale Developer-Capability gültig, wenn:

- `DCC_DEVELOPER_ENABLED=1` (Release-Override)
- gültiger Token per Header oder lokaler Datei
- optional `DCC_ALLOWED_HOSTNAME` stimmt mit `socket.gethostname()` überein
- kein Secret in API/Frontend/Evidence

## Token-Trennung

| Token | Zweck | DCC | Telemetrie |
|-------|-------|-----|------------|
| `DCC_DEVELOPER_TOKEN` / Datei | DCC-Freischaltung | ja | **nein** |
| `RESCUE_TELEMETRY_INGEST_TOKEN` | Telemetrie-Ingest | **nein** | ja |

Quellen DCC-Token (Priorität):

1. Environment `DCC_DEVELOPER_TOKEN`
2. Datei aus `DCC_DEVELOPER_TOKEN_FILE` oder `/etc/setuphelfer/dcc_developer.token` (Legacy: `developer.dcc.token`)
3. Request-Header `X-Setuphelfer-Developer-Token` oder `Authorization: Bearer …`

Empfohlene lokale Konfiguration (Platzhalter, nicht committen):

```bash
# /etc/setuphelfer/developer.env
DCC_DEVELOPER_ENABLED=1
DCC_DEVELOPER_TOKEN_FILE=/etc/setuphelfer/dcc_developer.token
DCC_ALLOWED_HOSTNAME=volker-ROG-Strix
RESCUE_TELEMETRY_INGEST_ENABLED=1
```

## Diagnose-Endpunkt

`GET /api/dev-dashboard/capability-status` — read-only, auch bei blockiertem DCC, **ohne Secrets**.

## Block-Codes

| Code | Bedeutung |
|------|-----------|
| `PROFILE_ROUTE_BLOCKED` | Release ohne `DCC_DEVELOPER_ENABLED` oder Lab ohne `dev_control` |
| `DEVELOPER_CAPABILITY_NOT_CONFIGURED` | DCC-Pfad offen, kein Token konfiguriert |
| `DEVELOPER_CAPABILITY_REQUIRED` | Token fehlt/ungültig oder Hostname-Binding |

## Implementierung

- Core: `backend/core/developer_capability.py`
- Telemetrie: `route_exposure.py` — `/api/rescue/telemetry/*` vom DCC-Gate getrennt
- Frontend: `DccCompactStatusBar`, blockierte Diagnose-Seite

## Operator-Smoke

- `docs/evidence/dev-dashboard/DEVELOPER_DCC_CAPABILITY_OPERATOR_SMOKE_HANDOFF.md`
- `docs/evidence/dev-dashboard/RESCUE_TELEMETRY_INGEST_OPERATOR_SMOKE_HANDOFF.md`
- `docs/evidence/dev-dashboard/DEVELOPER_DCC_TELEMETRY_DEPLOY_OPERATOR_HANDOFF.md` — **Pflicht vor Live-Smoke**
- `docs/evidence/dev-dashboard/DEVELOPER_DCC_CAPABILITY_LOCAL_CONFIG_OPERATOR_HANDOFF.md`
- Ergebnis: `docs/evidence/dev-dashboard/DEVELOPER_DCC_AND_TELEMETRY_OPERATOR_SMOKE_RESULT.md`
