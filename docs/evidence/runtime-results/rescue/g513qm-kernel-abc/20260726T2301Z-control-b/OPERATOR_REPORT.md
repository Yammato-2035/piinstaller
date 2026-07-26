# Control B — physical result (operator report)

## Run

| Field | Value |
|-------|-------|
| Run-ID | `20260726T2301Z-control-b` |
| Control | B — official Linux Mint 22.3 Cinnamon |
| ISO | verified SHA256 `a081ab20…` |
| Stick | Intenso Serial `24111412110212` |
| Setuphelfer modified | no |
| Reported | 2026-07-26 ~23:01 local |

## Observation

```text
Boot progressed (operator: message like "password: passwd changed" / similar)
Then: black screen
Ctrl+Alt+F2: no console
No further GUI/TUI action
```

Exact systemd/casper line not photographed — treat wording as approximate operator recall.

## Classification (provisional)

```text
control_b_desktop_not_reached
display_or_session_path_failure_late_boot
vt_unreachable
not_hardware_defect_confirmed
```

## Matrix context

| Control | Result |
|---------|--------|
| A Compat (22.1) | black after cups.service |
| B (22.3) | black after late password/passwd message; VT dead |
| C | still pending (Setuphelfer stick may need restore after accidental dd) |

Unmodified Mint A and B both fail to a usable desktop → Setuphelfer-only fault less likely; proceed to Control C + BIOS/HW gates per decision matrix (Fall 3 direction if C also freezes on amdgpu / nomodeset stays OK).
