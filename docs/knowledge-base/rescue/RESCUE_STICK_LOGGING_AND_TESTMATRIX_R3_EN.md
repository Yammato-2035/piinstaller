# Rescue Stick — Logging & Test Matrix (R.3 overview)

The rescue stick writes diagnostic results to `/setuphelfer-evidence/` on the stick (or RAM with a warning).

**Important:** Internal disks are never written to.

## On-stick layout

| Folder | Content |
|--------|---------|
| `boot/` | Kernel, UEFI, cmdline, live environment |
| `menu/` | TUI menu actions |
| `hardware/` | MSI diagnostics |
| `matrix/` | Test matrix JSON/MD |
| `telemetry/spool/` | Offline telemetry |
| `summaries/` | Combined bundle |

## Reading the matrix

`matrix/rescue_test_matrix_latest.md` — status lights and `next_action` per area.

## Assistant

`setuphelfer-rescue-start-assistant` — catches errors, returns to menu, blocks write actions.

Details: `docs/architecture/RESCUE_STICK_LOGGING_AND_TESTMATRIX_R3_EN.md`
