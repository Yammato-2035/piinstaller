> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/knowledge-base/rescue/RESCUE_STICK_LOGGING_AND_TESTMATRIX_R3_EN.md`). Bitte bei Release manuell gegenlesen.

# Clé de secours — Logging & Test Matrix (R.3 overview)

The Clé de secours writes diagNonstic results to `/setuphelfer-evidence/` on the stick (or RAM with a Avertissement).

**Important:** Interne disks are never written to.

## On-stick layout

| Folder | Content |
|--------|---------|
| `boot/` | Kernel, UEFI, cmdline, live environment |
| `menu/` | TUI menu actions |
| `hardware/` | MSI diagNonstics |
| `matrix/` | Test matrix JSON/MD |
| `telemetry/spool/` | Offline telemetry |
| `summaries/` | Combined bundle |

## Reading the matrix

`matrix/Secours_test_matrix_latest.md` — status lights and `Suivant_action` per area.

## Assistant

`setuphelfer-Secours-start-assistant` — catches Erreurs, returns to menu, blocks write actions.

Details: `docs/architecture/Secours_STICK_LOGGING_AND_TESTMATRIX_R3_EN.md`
