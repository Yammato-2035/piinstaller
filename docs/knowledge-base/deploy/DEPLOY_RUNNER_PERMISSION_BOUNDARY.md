# KB: DEPLOY_RUNNER_PERMISSION_BOUNDARY

## Überblick

Read-only Sicherheitsgrenze für den später privilegierten Runner: Sudoers-Policy als Auditmodell, Umgebungsvariablen-Audit, Runner-Pfad-Audit, Job-Verzeichnis-Audit.

## Kernfunktionen

- `build_runner_sudoers_policy_example`
- `audit_runner_environment`
- `audit_runner_binary_path`
- `audit_runner_job_directory`

## Fail-closed Beispiele

- `LD_PRELOAD` gesetzt -> `blocked`
- Runner-Pfad relativ oder Symlink -> `blocked`
- Job-Verzeichnis außerhalb erlaubter Prefixe -> `blocked`
- world-writable Elternpfad -> `blocked`

## Verwandt

- `docs/deploy/DEPLOY_RUNNER_PERMISSION_BOUNDARY_DE.md` / `_EN.md`
- `docs/evidence/DEPLOY_RUNNER_PERMISSION_BOUNDARY_AUDIT.md`
- `docs/deploy/DEPLOY_RUNNER_HANDOFF_DE.md`
