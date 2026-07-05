> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/dev-dashboard/CONTROLLED_COMMAND_RUNNER_MVP_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Controlled Command Runner MVP Plan (EN)

## MVP-0

- Documentatie, schema, allowlist design
- Nee execution

## MVP-1

- Terugend reads allowlist
- `GET /api/dev-dashboard/controlled-command-runs`
- `GET /api/dev-dashboard/controlled-command-allowlist`
- Nee POST execution

## MVP-2

- POST only for `read_only`/`test_only` command IDs
- Nee free command string
- allowlist argv only
- timeout + stdout/stderr logs
- evidence JSON per run
- Nee `sudo`/`apt`/`dd`/`mkfs`/mount writes

## MVP-3

- Runbook runner for defined sequences
- roadmap delta suggestions
- Nee automatic status changes without review

## MVP-4

- operator handoff import
- operator uploads manual logs/evidence
- dashboard evaluates imports
