# External Development Control Center (EN)

## Second monitor

The control center runs as a **separate Tauri window** (`label: cockpit`, ~1440×900) — intended on a second monitor next to the main app. The main app handles setup tasks; governance and gates are read-only in the cockpit.

## Multi-window (Tauri)

- Command: `open_development_cockpit`
- Dev URL: `http://localhost:5173/?window=cockpit`
- Build URL: `index.html?window=cockpit`
- Capability: `frontend/src-tauri/capabilities/cockpit.json`

## Views

| Mode | Content |
|------|---------|
| **Operations** | Matrix + runtime gate, safe-test, deploy drift |
| **Compact** | governance matrix only |
| **Timeline** | local transitions, clearable history |

Auto-refresh: 5–15 s (configurable via `localStorage`).

## Runtime gate & safe test mode

- **runtime_gate_passed = true** only when workspace/runtime match, `deploy_drift` green, service active, no blockers.
- **Safe test mode UNLOCKED** only with a green runtime gate — otherwise LOCKED (backup, restore, verify, HW blocked).

## Transition tracking

Real per-area state changes (e.g. `runtime: red → green`) are recorded in the timeline. No green without a prior API/gate signal change.

## Out of scope

No backup, restore, deploy, apt, or hardware tests — read-only by design.
