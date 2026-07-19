# MSI Auto-Discovery 1.10.0.29 — TUI-Kill + Start-Gate Skip

**Status:** `rescue_auto_discovery_failure_fully_observed`  
**Boot-ID:** `c7a32069-0cba-4897-bb7d-1d8c47bae2b3`  
**Stick:** `/dev/sdd2` → `/media/volker/SETUP_LOGS2`

## Operator-Sicht

1. `rescue-state.service` startet → TUI verschwindet  
2. danach `boot-observer`  
3. Hold: „Automatische Systemerkundung konnte nicht gestartet werden.“

## Was wirklich passiert ist

| Zeitpunkt | Ereignis |
|-----------|----------|
| 13:45:04 | TUI startet (Guard) |
| 13:45:16 | `media-check` fertig → **`start-assistant` + `rescue-state` parallel** |
| 13:45:16 | TUI deaktiviert; start-assistant `killed (HUP)` |
| 13:45:34 / 13:46:04 | Guard startet TUI erneut → sofort wieder tot |
| 13:46:20 | Guard-Limit → **Hold** (`failed_discovery_unknown`) |
| 13:46:36 | Finalizer: `failed_discovery_start_gate_not_invoked` + **`auto-discovery.done`** |
| 13:47:31 | MSI evidence fertig → Discovery-Unit **übersprungen** wegen `auto-discovery.done` |

Zusätzlich: systemd Ordering-Cycle durch `late-journal-harvest.path` `After=auto-msi-evidence` (löscht u. a. initialen TUI-Start-Job).

## Root Causes

1. **TTY-Konflikt:** Cmdline hat `setuphelfer_start_assistant=1` **und** Lab-Auto. Beide Units nutzen `TTYPath=/dev/tty1` + `TTYVHangup=yes`. Start-Assistant (nach media-check) hangupt die TUI. `rescue-state` startet nur zeitgleich — killt die TUI nicht selbst.
2. **Discovery hinter MSI:** Unit `After=auto-msi-evidence` → Start-Gate erst nach ~120 s Late-Gate; bis dahin Hold/Finalizer.
3. **Vorzeitiges `auto-discovery.done`:** Finalizer schreibt Done-Marker → Condition `!auto-discovery.done` skippt Discovery dauerhaft.
4. **Path-Ordering-Cycle:** `.path` mit `After=` auf spätere Service-Unit.

## Observability (001D7E OK)

- Resolver, Observer, `discovery-boot/`, Late-Journal, Finalizer, Run-Control consumed  
- Acceptance: `rescue_auto_discovery_failure_fully_observed`

## Fix-Richtung (001D7F / Payload 1.10.0.30)

- Start-Assistant: Conditions `!setuphelfer_auto_discovery=1` / `!msi_lab_auto` / `!msi_e2e_auto`
- TUI: kein `Wants=start-assistant`; `Conflicts=start-assistant`
- Discovery: parallel zu MSI (Orchestrator wartet intern auf MSI)
- Finalizer: kein Done/Consume solange Start-Gate fehlt und MSI noch läuft
- `late-journal-harvest.path`: kein `After=auto-msi-evidence`
