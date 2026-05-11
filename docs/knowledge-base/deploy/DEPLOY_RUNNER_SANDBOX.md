# KB: DEPLOY_RUNNER_SANDBOX

## Überblick

Read-only Sandbox-Policy für den Deploy-Runner: ENV-Minimierung, STDIO-/FD-Regeln, Timeout-/Stop-Modell, Privilege-Drop-Empfehlung und Recovery-Failure-Modes.

## Kernpunkte

- one-shot-only, kein Background-Modus
- `PATH` fest (`/usr/bin:/bin`), kritische ENV geblockt
- stdin deaktiviert, stdout/stderr capture-only, `close_fds_required=true`
- Timeout-Modell mit modellierten Stop-Signalen
- nie Backend als root

## Verwandt

- `docs/deploy/DEPLOY_RUNNER_SANDBOX_DE.md` / `_EN.md`
- `docs/evidence/DEPLOY_RUNNER_SANDBOX_AUDIT.md`
- `docs/deploy/DEPLOY_RUNNER_PERMISSION_BOUNDARY_DE.md`
