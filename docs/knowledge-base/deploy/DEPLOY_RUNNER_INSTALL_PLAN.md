# KB: DEPLOY_RUNNER_INSTALL_PLAN

## Ueberblick

Read-only Installations-/Betriebsplan fuer den spaeter privilegierten Deploy-Runner.

## Planinhalte

- Runner-Binary-Modell (feste absolute Pfade, keine Symlinks)
- Jobdirectory-Modell (fester Prefix, TTL/Cleanup)
- Sudoers-Policy-Plan (restriktiv, ohne Installation)
- Service-Modell (one-shot, kein Daemon)
- Manual Steps + Blocked Steps

## Verwandt

- `docs/deploy/DEPLOY_RUNNER_INSTALL_PLAN_DE.md` / `_EN.md`
- `docs/evidence/DEPLOY_RUNNER_INSTALL_PLAN_AUDIT.md`
- `docs/deploy/DEPLOY_RUNNER_PERMISSION_BOUNDARY_DE.md`
