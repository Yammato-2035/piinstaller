# Installationsprofile und Deploy-Scopes

**Stand:** 2026-05-31

## Grundsatz

Ein Repository darf mehrere Komponenten enthalten (Development Control Center, Fleet Sessions, Dev Diagnostics, Rescue Remote, …). Jede **Runtime** darf nur die Komponenten **aktivieren**, die im **aktiven Installationsprofil** erlaubt sind.

- Code im Repo ≠ aktivierte Runtime-Funktion
- Aktivierung: `SETUPHELFER_INSTALL_PROFILE` + Capability-Gates + Router-Registrierung + Middleware
- Deploy-Drift wird gegen das **Profil-Manifest** geprüft, nicht gegen das gesamte Repo

## Profile

| Profil | Zweck | Dev-Routen | Public Exposure |
|--------|-------|------------|-----------------|
| `release` | Normale Nutzer-Runtime | **nein** | **nein** |
| `developer` | Lokale Entwicklung | ja (lokal) | **nein** |
| `local_lab` | Lab-Abnahme 127.0.0.1 / freigegebenes LAN | ja (intern) | **nein** |
| `rescue_lab` | Rescue-/QEMU-Lab | Rescue Remote read-only | **nein** |
| `production` | Späteres Produktprofil | nur mit eigener Freigabe | policy-gesteuert |

## Konfiguration

Zentrale Quelle: `backend/core/install_profile.py`

| Variable | Wirkung |
|----------|---------|
| `SETUPHELFER_INSTALL_PROFILE` | `release` \| `developer` \| `local_lab` \| `rescue_lab` \| `production` |
| `PI_INSTALLER_DEV=1` | Fallback → `developer` (kein Public Exposure) |
| *(unset)* | Default → `release` |

## Router-Gates

| Router | Erlaubt wenn |
|--------|----------------|
| Fleet (`/api/fleet/*`) | Profil ∈ {developer, local_lab, rescue_lab} **und** `fleet_sessions_enabled` |
| Dev Diagnostics | Profil ∈ {developer, local_lab, rescue_lab} **und** `dev_diagnostics_enabled` |
| Rescue Remote | Profil ∈ {local_lab, rescue_lab} **und** `rescue_remote_enabled` **und** `write_runbooks_enabled=false` |
| Dev Server | Profil ∈ {developer, local_lab, rescue_lab} **und** `dev_server_enabled` |
| Dev Dashboard | Middleware blockiert bei `release`/`production`; Capability `dev_control_enabled` |

Release/Production: verbotene Pfade liefern **404** (`PROFILE_ROUTE_BLOCKED`) bzw. erscheinen nicht in OpenAPI, wenn Router nicht registriert sind.

## Deploy-Manifeste

`deploy/manifests/{common,release,developer,local_lab,rescue_lab,production}.manifest.json`

Generator:

```bash
python3 backend/tools/generate_deploy_manifest.py --profile release
python3 backend/tools/generate_deploy_manifest.py --profile local_lab
```

## Runtime-Gates

- Basis: `scripts/check-runtime-deploy-gate.sh`
- Profil: `scripts/check-runtime-profile-deploy-gate.sh` (liest `/api/version` + OpenAPI)

Exit-Codes (Profil): 17–22, 30 — siehe Skript-Kopf.

## `/api/version`

Liefert u. a. `install_profile`, `manifest_profile`, Capability-Flags, `profile_gate_status`, `profile_gate_errors`, `runtime_manifest_sha256`, `frontend_build_profile`.

## Frontend

Build-Profil über Vite (`frontend/vite.config.ts`, `frontend/src/config/buildProfile.ts`). Release-Build: keine Lab-/Dev-Control-UI. Local-Lab: Hinweis „Interne Entwicklungsdaten. Nicht öffentlich teilen.“

## Public Exposure

`public_exposure_allowed` ist standardmäßig **false**. Bind auf `0.0.0.0` ohne Freigabe → Gate **21**.
