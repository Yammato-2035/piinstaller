> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/dev-dashboard/CONTROLLED_COMMAND_RUNNER_MVP_PLAN_EN.md`). Bitte bei Release manuell gegenlesen.

# Controlled Command Runner MVP Plan (EN)

## MVP-0

- Documentation, schema, allowlist design
- Non execution

## MVP-1

- Retourend reads allowlist
- `GET /api/dev-dashboard/controlled-command-runs`
- `GET /api/dev-dashboard/controlled-command-allowlist`
- Non POST execution

## MVP-2

- POST only for `read_only`/`test_only` command IDs
- Non free command string
- allowlist argv only
- timeout + stdout/stderr logs
- evidence JSON per run
- Non `sudo`/`apt`/`dd`/`mkfs`/mount writes

## MVP-3

- Runbook runner for defined sequences
- roadmap delta suggestions
- Non automatic status changes without review

## MVP-4

- operator handoff import
- operator uploads manual logs/evidence
- dashboard evaluates imports
