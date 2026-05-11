# Deploy Runner Sandbox (simuliert, read-only)

## Ziel

Diese Phase modelliert eine strikt kontrollierte Sandbox-Ausführung für den später privilegierten Runner — ohne echte Privilegierung und ohne Device-Aktionen.

## Umfang

- Prozessmodell: one-shot, nicht interaktiv, kein Hintergrundmodus
- Minimale ENV-Whitelist, Blockliste für riskante Variablen
- STDIO-/FD-Härtung als Policy-Modell
- Timeout-/Shutdown-/Hard-stop als Signalmodell (nur hypothetisch)
- Privilege-Drop-Empfehlungen (nur Analyse)
- Crash/Recovery-Failure-Modes (nur Analyse)

## Modul

`backend/deploy/runner_sandbox.py`

Funktionen:
- `build_runner_sandbox_policy`
- `build_sandbox_environment`
- `build_runner_stdio_policy`
- `build_runner_timeout_model`
- `build_runner_privilege_model`
- `build_runner_recovery_analysis`

## Read-only API

- `POST /api/deploy/runner/sandbox/policy`
- `POST /api/deploy/runner/sandbox/environment`
- `POST /api/deploy/runner/sandbox/stdio`
- `POST /api/deploy/runner/sandbox/timeout`
- `POST /api/deploy/runner/sandbox/privileges`
- `POST /api/deploy/runner/sandbox/recovery`

## Grenzen

- Keine echten Signale
- Kein sudo/setuid
- Keine echte Prozesseskalation
- Kein Device-Write, kein Mount, kein Deploy
