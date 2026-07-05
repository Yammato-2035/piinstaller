> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/dev-dashboard/CONTROLLED_COMMAND_RUNNER_DESIGN_EN.md`). Bitte bei Release manuell gegenlesen.

# Controlled Command Runner Design (EN)

## Purpose

- Interne developer runs in the dev dashboard
- complete logging (stdout/stderr separated)
- exit-code evaluation and safety classification
- evidence generation per run
- roadmap delta proposal support
- Nont an end-user feature

## Nonn-goals

- Non free terminal
- Non free shell
- Non dashboard `sudo`
- Non Restauration/Retourup/USB/apt actions
- Non operator escalation from UI

## Safety Classes

- `read_only`
- `test_only`
- `evidence_only`
- `operator_handoff`
- `forbidden`

## Examples

Allowed `read_only`, `test_only`, and `evidence_only` commands must be allowlisted by `command_id` and exact `argv`.

`operator_handoff` entries are documented outputs only, Nont directly executable by dashboard runtime.

`forbidden` entries are never executed.
