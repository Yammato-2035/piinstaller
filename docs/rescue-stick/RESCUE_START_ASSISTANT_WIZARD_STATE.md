# Rescue Start Assistant — WizardState (JSON)

Shared state file on live system: `/run/setuphelfer-rescue/wizard-state.json`

Used by TUI today; same schema for future GUI/WebUI.

## Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema_version` | int | Currently `1` |
| `step` | string | Current wizard step id |
| `selected_action` | string/null | `backup`, `restore`, `repair`, `install`, `diagnostics`, `expert` |
| `expert_mode` | bool | Expert shell path |
| `media_check` | object | Output of `setuphelfer-rescue-media-check` |
| `network_onboarding` | object | Output of network onboarding |
| `disk_discovery` | object | Read-only disk report |
| `action_plan` | object | Read-only plan from `setuphelfer-rescue-plan-builder.py` |
| `write_actions_allowed` | bool | Always `false` in v1 productization |
| `secrets_exposed` | bool | Always `false` |

## GUI readiness

- TUI (`setuphelfer-rescue-start-assistant`) reads/writes this file.
- Future GUI renders the same JSON; no duplicate business logic required in UI layer.
