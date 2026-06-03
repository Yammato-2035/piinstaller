# Developer Backend Watchdog — Deploy Live Result

**Datum:** 2026-06-03  
**HEAD:** `8fba260`

## Zusammenfassung

| Aussage | Wert |
|---------|------|
| Watchdog deployed nach `/opt` | **no** — Agent-Deploy blockiert (sudo) |
| Healthcheck live (Workspace) | **yes** — Exit 0, `overall_status=ok` |
| Healthcheck live (`/opt`) | **no** — Skript fehlt |
| Backend-Health API live (local_lab) | **no** — nicht getestet (Deploy+Profil ausstehend) |
| DCC Panel live unter `/opt` | **no** |
| release restored | **n/a** — blieb release |
| Timer auto-aktiviert | **no** |
| QEMU / ISO / USB | **no** |

## Ursache Blockierung

`sudo ./scripts/deploy-to-opt.sh` → Exit **1** (Passwort). Ohne Deploy fehlen in `/opt` Healthcheck-Skript, Backend-Loader/Route und aktuelles Frontend-Bundle.

## Operator-Abschluss (Pflicht)

1. `sudo ./scripts/deploy-to-opt.sh /home/volker/piinstaller` → Exit 0
2. `/opt/setuphelfer/scripts/dev-dashboard/check-backend-health.sh` → Exit 0
3. local_lab + `curl /api/dev-dashboard/backend-health` → HTTP 200, `current_health` ok
4. Browser: `http://127.0.0.1:3001/?window=cockpit` → Panel **Backend Health**
5. Release restore (`92-install-profile-release.conf.example`)
6. Dann: QEMU Guest Agent Smoke (wenn Health ok)

## Evidence

- `DEVELOPER_BACKEND_WATCHDOG_DEPLOY_PHASE0.md`
- `DEVELOPER_BACKEND_WATCHDOG_DEPLOY_DRIFT_REVIEW.md`
- `DEVELOPER_BACKEND_WATCHDOG_DEPLOY_RESULT.md`
- `DEVELOPER_BACKEND_WATCHDOG_DEPLOY_ONESHOT_RESULT.md`
- `DEVELOPER_BACKEND_WATCHDOG_API_LIVE_SMOKE.md`
- `DEVELOPER_BACKEND_WATCHDOG_FRONTEND_LIVE_REVIEW.md`
- `DEVELOPER_BACKEND_WATCHDOG_RELEASE_RESTORE_RESULT.md`
- `DEVELOPER_BACKEND_WATCHDOG_TIMER_HANDOFF_READY.md`
- `DEVELOPER_BACKEND_WATCHDOG_DEPLOY_TEST_RESULT.md`

## Offene Risiken

- Live-Verifikation hängt an **einem** Operator-Deploy-Lauf im Terminal 6.
- API-Smoke und DCC-Panel können erst nach Deploy + kurzem local_lab belegt werden.
