# Externes Development Control Center (DE)

## Zweiter Monitor

Das Control Center ist als **eigenes Tauri-Fenster** (`label: cockpit`, ca. 1440×900) gedacht — auf einem zweiten Monitor neben der Haupt-App. Die Haupt-App bleibt für Setup-Aufgaben; Governance und Gates laufen read-only im Cockpit.

## Multiwindow (Tauri)

- Command: `open_development_cockpit`
- URL Dev: `http://localhost:5173/?window=cockpit`
- URL Build: `index.html?window=cockpit`
- Capability: `frontend/src-tauri/capabilities/cockpit.json`

## Ansichten

| Modus | Inhalt |
|-------|--------|
| **Operations** | Matrix + Runtime-Gate, Safe-Test, Deploy-Drift |
| **Kompakt** | nur Governance-Matrix |
| **Timeline** | lokale Übergänge, Historie löschbar |

Auto-Refresh: 5–15 s (einstellbar, `localStorage`).

## Runtime Gate & Safe Test Mode

- **runtime_gate_passed = true** nur wenn u. a. Workspace↔Runtime konsistent, `deploy_drift` grün, Dienst aktiv, keine Blocker.
- **Safe Test Mode UNLOCKED** nur bei grünem Runtime-Gate — sonst LOCKED (Backup, Restore, Verify, HW gesperrt).

## Transition Tracking

Echte Zustandswechsel pro Bereich (z. B. `runtime: red → green`) werden in der Timeline protokolliert. Kein Grün ohne vorherigen API-/Gate-Signalwechsel.

## Was das Cockpit nicht tut

Kein Backup, Restore, Deploy, apt, Hardwaretests — bewusst read-only.
