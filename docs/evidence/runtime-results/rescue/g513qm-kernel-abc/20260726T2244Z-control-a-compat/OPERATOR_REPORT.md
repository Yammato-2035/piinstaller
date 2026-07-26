# Control A — physical result (operator report)

## Run

| Field | Value |
|-------|-------|
| Run-ID | `20260726T2244Z-control-a-compat` |
| Control | A — official Linux Mint 22.1 Cinnamon |
| ISO status | verified (SHA256 + GPG) |
| Stick (intended) | Intenso Ultra Line Serial `24111412110212` |
| Mode | **Compatibility Mode** (official menu) |
| Setuphelfer modified | no |
| Reported at (UTC) | 2026-07-26T20:44:20Z |

## Prior invalid attempt

First freeze photo showed USB serial `24111412110686` (Setuphelfer carrier) — **invalid for Control A**. Discarded as wrong media / mixed USB.

## Observation (this run)

```text
Boot progressed through Compatibility Mode.
At/after: cups.service started
Then: black screen
No console, no GUI/TUI further action
```

## Classification (provisional)

```text
display_or_session_path_failure_after_cups
not_hardware_defect_confirmed
control_a_desktop_not_reached
```

Same **class** as earlier Gabriel Setuphelfer multi-user hangs near cups/HID — but on **unmodified** Mint 22.1 Compatibility Mode. That weakens a pure Setuphelfer-only explanation for this symptom; Control B/C still required before Fall-3/BIOS/HW decision.

## Not captured

| Item | Status |
|------|--------|
| Kernel `uname -r` | not_captured (no console) |
| Caps Lock / SysRq alive | not_captured |
| Ping / network alive | not_captured |
| VT switch Ctrl+Alt+Fn | not_captured |
| External HDMI | not_tested |
| BIOS version photo | not_captured in this note |
| Secure Boot | not_captured |

## Operator next

1. Alive probes once (Caps Lock, Ctrl+Alt+F2–F9) — do not assume total crash from black alone.
2. Cold power-off if no response.
3. Proceed to Control B (official Mint 22.3) on same or rewritten second stick.
4. Keep Setuphelfer stick (`…10686`) unused until Control C.
