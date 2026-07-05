> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/dev-dashboard/EXTERNAL_CONTROL_CENTER_EN.md`). Bitte bei Release manuell gegenlesen.

# Extern Ontwikkelingscontrolecentrum (EN)

## Second monitor

The control center runs as a **separate Tauri window** (`label: cockpit`, ~1440×900) — intended on a second monitor Volgende to the main app. The main app handles setup tasks; governance and gates are alleen-lezen in the cockpit.

## Multi-window (Tauri)

- Command: `open_development_cockpit`
- Dev URL: `http://localhost:5173/?window=cockpit`
- Build URL: `index.html?window=cockpit`
- Capability: `frontend/src-tauri/capabilities/cockpit.json`

## Views

| Mode | Content |
|------|---------|
| **Operations** | Matrix + runtime gate, safe-test, Deploy drift |
| **Compact** | governance matrix only |
| **Timeline** | local transitions, clearable history |

Auto-Vernieuwen: 5–15 s (configurable via `localStorage`).

## Runtime gate & safe test mode

- **runtime_gate_passed = true** only when workspace/runtime match, `Deploy_drift` groen, service active, Nee blockers.
- **Safe test mode UNLOCKED** only with a groen runtime gate — otherwise LOCKED (Terugup, Herstel, verify, HW geblokkeerd).

## Transition tracking

Real per-area state changes (e.g. `runtime: rood → groen`) are recorded in the timeline. Nee groen without a prior API/gate signal change.

## Out of scope

Nee Terugup, Herstel, Deploy, apt, or hardware tests — alleen-lezen by design.
