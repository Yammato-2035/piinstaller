# Controlled Command Runner Design (EN)

## Purpose

- internal developer runs in the dev dashboard
- complete logging (stdout/stderr separated)
- exit-code evaluation and safety classification
- evidence generation per run
- roadmap delta proposal support
- not an end-user feature

## Non-goals

- no free terminal
- no free shell
- no dashboard `sudo`
- no restore/backup/USB/apt actions
- no operator escalation from UI

## Safety Classes

- `read_only`
- `test_only`
- `evidence_only`
- `operator_handoff`
- `forbidden`

## Examples

Allowed `read_only`, `test_only`, and `evidence_only` commands must be allowlisted by `command_id` and exact `argv`.

`operator_handoff` entries are documented outputs only, not directly executable by dashboard runtime.

`forbidden` entries are never executed.
