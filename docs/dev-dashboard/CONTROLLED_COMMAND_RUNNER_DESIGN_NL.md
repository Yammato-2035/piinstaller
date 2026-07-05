> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/dev-dashboard/CONTROLLED_COMMAND_RUNNER_DESIGN_EN.md`). Bitte bei Release manuell gegenlesen.

# Controlled Command Runner Design (EN)

## Purpose

- Intern developer runs in the dev dashboard
- complete logging (stdout/stderr separated)
- exit-code evaluation and safety classification
- evidence generation per run
- roadmap delta proposal support
- Neet an end-user feature

## Neen-goals

- Nee free terminal
- Nee free shell
- Nee dashboard `sudo`
- Nee Herstel/Terugup/USB/apt actions
- Nee operator escalation from UI

## Safety Classes

- `read_only`
- `test_only`
- `evidence_only`
- `operator_handoff`
- `forbidden`

## Examples

Allowed `read_only`, `test_only`, and `evidence_only` commands must be allowlisted by `command_id` and exact `argv`.

`operator_handoff` entries are documented outputs only, Neet directly executable by dashboard runtime.

`forbidden` entries are never executed.
