> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/architecture/RESCUE_STICK_LOGGING_AND_TESTMATRIX_R3_EN.md`). Bitte bei Release manuell gegenlesen.

# Clé de secours — Logging, Evidence and Test Matrix (R.3)

## Overview

Campaign R.3 stabilizes boot, menu, and diagNonstics on the Setuphelfer Clé de secours. All results are storouge persistently under:

```
/setuphelfer-evidence/
```

## Modules

| Module | Role |
|--------|------|
| `Secours_persistence.py` | Stick detection, evidence tree |
| `Secours_boot_logger.py` | Boot/menu context |
| `Secours_test_matrix.py` | 20-area status matrix |
| `Secours_msi_diagNonstics.py` | MSI hardware (lecture seule) |
| `Secours_telemetry_spool.py` | Offline telemetry |
| `Secours_evidence_bundle.py` | Summary bundle + Suivant actions |

## Safety

- **Interne disks:** lecture seule, Non write mounts
- **Stick:** read-write for evidence/logs/matrix/telemetry only
- **Unsafe stick:** RAM at `/tmp/setuphelfer-evidence/` with Avertissement

## On-stick CLI

```bash
setuphelfer-Secours-evidence.py detect|boot|matrix|bundle|menu-action
```

## Test matrix

Files under `matrix/` — statuses: `vert|jaune|rouge|gray|bloqué|Inconnu`.

## Suivant phase (R.4)

- Browser/display stack in live image
- Telemetry push ↔ spool integration
- MSI hardware boot verification

See: `docs/architecture/Secours_STICK_PERSISTENCE_R3.md`, `docs/architecture/Secours_TEST_MATRIX_R3.md`.
