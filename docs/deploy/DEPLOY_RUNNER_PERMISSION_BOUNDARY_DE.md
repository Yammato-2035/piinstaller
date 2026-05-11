# Deploy Runner Permission Boundary (Read-only Audit)

## Ziel

Read-only Sicherheitsanalyse für die spätere privilegierte Runner-Ausführung, ohne sudoers-Installation und ohne Rechteänderungen am System.

## Modul

`backend/deploy/runner_permission_boundary.py`

Funktionen:
- `build_runner_sudoers_policy_example(...)`
- `audit_runner_environment(...)`
- `audit_runner_binary_path(...)`
- `audit_runner_job_directory(...)`

## Analysierte Risiken

- sudoers-Wildcards und Argument-Injection
- PATH-/PYTHONPATH-/LD_PRELOAD-/LD_LIBRARY_PATH-Risiken
- Shell Escaping / freie Kommandos
- Symlink-/Traversal-Risiken für Runner-Pfad und Job-Verzeichnis
- world-writable Verzeichnisse in Pfadketten

## Sudoers-Policy-Modell (nur Beispiel)

`build_runner_sudoers_policy_example` liefert ein reines Auditmodell und schreibt nichts nach `/etc`.

Erforderliche Restriktionen:
- `RUNNER_REQUIRE_ABSOLUTE_PATH`
- `RUNNER_REQUIRE_FIXED_JOB_DIRECTORY`
- `RUNNER_REQUIRE_ENV_RESET`
- `RUNNER_BLOCK_PYTHONPATH`
- `RUNNER_BLOCK_LD_PRELOAD`
- `RUNNER_BLOCK_DYNAMIC_PATH`
- `RUNNER_BLOCK_WILDCARDS`
- `RUNNER_REQUIRE_NOINTERACTIVE`
- `RUNNER_REQUIRE_NO_SHELL`

## Read-only API-Routen

- `POST /api/deploy/runner/audit/sudoers`
- `POST /api/deploy/runner/audit/environment`
- `POST /api/deploy/runner/audit/path`
- `POST /api/deploy/runner/audit/jobdir`

## Grenzen

- Kein sudoers-Write, kein visudo, kein sudo-Aufruf
- Kein chmod/chown auf Systemdateien
- Kein Device-Write, kein Mount/Partitionierungs-Tool
