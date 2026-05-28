# Controlled Command Runner MVP Plan (EN)

## MVP-0

- Documentation, schema, allowlist design
- no execution

## MVP-1

- Backend reads allowlist
- `GET /api/dev-dashboard/controlled-command-runs`
- `GET /api/dev-dashboard/controlled-command-allowlist`
- no POST execution

## MVP-2

- POST only for `read_only`/`test_only` command IDs
- no free command string
- allowlist argv only
- timeout + stdout/stderr logs
- evidence JSON per run
- no `sudo`/`apt`/`dd`/`mkfs`/mount writes

## MVP-3

- Runbook runner for defined sequences
- roadmap delta suggestions
- no automatic status changes without review

## MVP-4

- operator handoff import
- operator uploads manual logs/evidence
- dashboard evaluates imports
