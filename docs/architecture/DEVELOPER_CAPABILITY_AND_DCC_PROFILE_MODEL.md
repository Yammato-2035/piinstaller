# Developer Capability and DCC Profile Model

## Profiles

| Profile | DCC API | DCC UI | Telemetrie `/api/rescue/telemetry/*` |
|---------|---------|--------|--------------------------------------|
| `release` | blockiert (`PROFILE_ROUTE_BLOCKED`) | Disabled-Seite | separat erreichbar (eigene Ingest-Policy) |
| `production` | wie release | Disabled | separat |
| `developer` | nur mit gültiger Developer-Capability | sichtbar bei `dcc_allowed=true` | separat |
| `local_lab` | wie developer | wie developer | separat |

## Token-Trennung

| Token | Zweck | DCC | Backup/Restore/USB/Deploy |
|-------|-------|-----|------------------------------|
| `DCC_DEVELOPER_TOKEN` | DCC-Freischaltung | ja | **nein** |
| `RESCUE_TELEMETRY_INGEST_TOKEN` | Telemetrie-Ingest | **nein** | **nein** |

Quellen DCC-Token (Priorität):

1. Environment `DCC_DEVELOPER_TOKEN`
2. Datei `/etc/setuphelfer/developer.dcc.token`
3. Header `X-Setuphelfer-Developer-Token` oder `Authorization: Bearer …`

Kein Token im Repo, in Evidence oder in URLs.

## API-Felder (`/api/version`)

- `developer_capability_available`
- `developer_capability_valid` (false ohne Request-Token)
- `developer_capability_source`
- `dcc_profile_allowed`
- `dcc_allowed`
- `internal_dev_mode` (= `dcc_allowed`)
- `rescue_telemetry_separate_from_dcc`

Niemals Token-Wert ausgeben.

## Block-Codes

| Code | Bedeutung |
|------|-----------|
| `PROFILE_ROUTE_BLOCKED` | Release/Production oder `dev_control_enabled=false` |
| `DEVELOPER_CAPABILITY_NOT_CONFIGURED` | Profil erlaubt DCC, kein Token konfiguriert |
| `DEVELOPER_CAPABILITY_REQUIRED` | Token konfiguriert, Request ohne/ungültiges Token |

## Implementierung

- Core: `backend/core/developer_capability.py`
- Route-Gate: `path_allowed_for_active_profile()` + Middleware in `backend/app.py`
- Telemetrie bleibt in `route_exposure.py` vom DCC-Gate getrennt
