> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/dev-dashboard/EXTERNAL_CONTROL_CENTER_EN.md`). Bitte bei Release manuell gegenlesen.

# Externe Centre de contrôle du développement (EN)

## Second monitor

The control center runs as a **separate Tauri window** (`label: cockpit`, ~1440×900) — intended on a second monitor Suivant to the main app. The main app handles setup tasks; governance and gates are lecture seule in the cockpit.

## Multi-window (Tauri)

- Command: `open_development_cockpit`
- Dev URL: `http://localhost:5173/?window=cockpit`
- Build URL: `index.html?window=cockpit`
- Capability: `frontend/src-tauri/capabilities/cockpit.json`

## Views

| Mode | Content |
|------|---------|
| **Operations** | Matrix + runtime gate, safe-test, Déploiement drift |
| **Compact** | governance matrix only |
| **Timeline** | local transitions, clearable history |

Auto-Actualiser: 5–15 s (configurable via `localStorage`).

## Runtime gate & safe test mode

- **runtime_gate_passed = true** only when workspace/runtime match, `Déploiement_drift` vert, service active, Non blockers.
- **Safe test mode UNLOCKED** only with a vert runtime gate — otherwise LOCKED (Retourup, Restauration, verify, HW bloqué).

## Transition tracking

Real per-area state changes (e.g. `runtime: rouge → vert`) are recorded in the timeline. Non vert without a prior API/gate signal change.

## Out of scope

Non Retourup, Restauration, Déploiement, apt, or hardware tests — lecture seule by design.
