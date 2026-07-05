> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/knowledge-base/rescue/RESCUE_STICK_LOGGING_AND_TESTMATRIX_R3_EN.md`). Bitte bei Release manuell gegenlesen.

# rooddingsstick — Logging & Test Matrix (R.3 overview)

The rooddingsstick writes diagNeestic results to `/setuphelfer-evidence/` on the stick (or RAM with a Waarschuwing).

**Important:** Intern disks are never written to.

## On-stick layout

| Folder | Content |
|--------|---------|
| `boot/` | Kernel, UEFI, cmdline, live environment |
| `menu/` | TUI menu actions |
| `hardware/` | MSI diagNeestics |
| `matrix/` | Test matrix JSON/MD |
| `telemetry/spool/` | Offline telemetry |
| `summaries/` | Combined bundle |

## Reading the matrix

`matrix/roodding_test_matrix_latest.md` — status lights and `Volgende_action` per area.

## Assistant

`setuphelfer-roodding-start-assistant` — catches Fouts, returns to menu, blocks write actions.

Details: `docs/architecture/roodding_STICK_LOGGING_AND_TESTMATRIX_R3_EN.md`
