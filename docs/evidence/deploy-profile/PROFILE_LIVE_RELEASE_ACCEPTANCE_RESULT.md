# Live-Abnahme Release-Profil

**Datum:** 2026-05-31

## Durchführung

| Schritt | Ergebnis |
|---------|----------|
| `SETUPHELFER_INSTALL_PROFILE=release` auf `/opt` | **nicht gesetzt** (kein sudo-Deploy) |
| Deploy Workspace → `/opt` | **blocked** — `deploy_blocked_sudo_required` |
| OpenAPI Dev-Routen live | **nicht neu geprüft** (Runtime ohne Commit-Deploy) |

## Phase-0-Baseline (lesend)

- `GET /api/version`: `install_profile=opt` (Legacy), kein Capability-Gate
- `check-runtime-deploy-gate.sh`: Exit **16** (manifest_match)
- `check-runtime-profile-deploy-gate.sh`: Exit **16** (Basis-Gate)

## Erwartung nach Operator-Deploy

1. systemd-Drop-in: `SETUPHELFER_INSTALL_PROFILE=release`
2. `sudo ./scripts/deploy-to-opt.sh`
3. OpenAPI ohne `/api/fleet`, `/api/dev-diagnostics`, `/api/rescue-remote`, `/api/dev-dashboard`
4. `check-runtime-profile-deploy-gate.sh` Exit **0**

## Statische Abnahme

- Unit-Tests Release blockiert Dev-Router: **OK**
- Shell-Gate Release + Fleet-Pfad: Exit **19**
