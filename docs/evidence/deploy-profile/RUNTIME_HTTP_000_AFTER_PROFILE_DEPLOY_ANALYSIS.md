# HTTP 000 nach Profil-Deploy — Analyse

**Datum:** 2026-05-31 · **HEAD:** `3ea1c69`+

## Symptom

```
check-runtime-profile-deploy-gate: /api/version HTTP 000000
```

Direkt nach `deploy-to-opt.sh` + `systemctl restart setuphelfer-backend.service`.

## Ist-Zustand (nach Stabilisierung)

| Prüfung | Ergebnis |
|---------|----------|
| `setuphelfer-backend.service` | **active** / running |
| Port `127.0.0.1:8000` | **lauscht** |
| `GET /api/version` | **HTTP 200** |
| Profil-Gate | **Exit 0** |

## Ursache HTTP 000

**Primär: Race nach Restart** — das Profil-Gate führte **einen** `curl` ohne Retry aus, während Uvicorn noch nicht auf Port 8000 antwortete (`connection refused` → `http_code=000`).

**Nicht:** Import-Crash, SyntaxError oder dauerhaft inaktiver Dienst (aktuell stabil).

**Anzeige „000000“:** sehr wahrscheinlich verkettete/leer formatierte Exit-Anzeige; technisch `000` = curl nicht verbunden.

## Fix (Repo)

`check-runtime-profile-deploy-gate.sh`: Retries wie Legacy-Gate (`RUNTIME_GATE_API_RETRIES`, `/health` dann `/api/version`, dann OpenAPI).

## Release-Profil live

| Feld | Wert |
|------|------|
| `install_profile` | `release` |
| `dev_server_enabled` | `false` (Override `SETUPHELFER_DEV_SERVER_ENABLED` ignoriert) |
| `profile_gate_status` | `green` |

| Pfad | HTTP |
|------|------|
| `/api/dev-dashboard/status` | 404 |
| `/api/fleet/sessions` | 404 |
| `/api/dev-diagnostics/latest` | 404 |
| `/api/rescue-remote/jobs` | 404 |
| `/api/dev-server/health` | **404** (vorher 200) |

## systemd

- `install-profile.conf`: `SETUPHELFER_INSTALL_PROFILE=release`
- `90-devserver-local-lab.conf`: `SETUPHELFER_DEV_SERVER_ENABLED=true` — im Release-Profil **wirkungslos** (Capability-Gate)

## Legacy-Gate

Weiter Exit **20** (dev-dashboard 404) — `LEGACY_GATE_NON_PROFILE_AWARE`, nicht blockierend für Profil-Gate.
