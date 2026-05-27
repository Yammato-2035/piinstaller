# Roadmap Command Logging — Delta

**Datum:** 2026-05-27

## Prompts

| ID | vorher | nachher |
|----|--------|---------|
| TERMINAL_A_READONLY | available | **completed** |
| selected (next_prompts) | RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD | unverändert |

## Areas / Milestones

| Eintrag | Änderung |
|---------|----------|
| dev-dashboard | Evidence + Hinweis Live-Deploy vor Rescue; `next_prompt_id` → RESCUE_ISO |
| dev-dashboard-command-logging-readonly | **neu**, status **green** |
| dashboard-api-tests-system-python | **neu**, status **yellow** |

## status_counts (Area-Ebene)

Unverändert: `partial_green:3, blocked:3, deferred:2, yellow:4, unknown:1` — Grün nur auf **Milestone**-Ebene (Command Logging), nicht gesamte Area auf green (kein Fake-Green).

## Fake-Green vermieden

- backup, restore, rescue, release-gate, hardware unverändert blockiert/gelb/rot
- System-Python-API explizit gelb
