> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/architecture/RESCUE_STICK_LOGGING_AND_TESTMATRIX_R3_EN.md`). Bitte bei Release manuell gegenlesen.

# rooddingsstick — Logging, Evidence and Test Matrix (R.3)

## Overview

Campaign R.3 stabilizes boot, menu, and diagNeestics on the Setuphelfer rooddingsstick. All results are storood persistently under:

```
/setuphelfer-evidence/
```

## Modules

| Module | Role |
|--------|------|
| `roodding_persistence.py` | Stick detection, evidence tree |
| `roodding_boot_logger.py` | Boot/menu context |
| `roodding_test_matrix.py` | 20-area status matrix |
| `roodding_msi_diagNeestics.py` | MSI hardware (alleen-lezen) |
| `roodding_telemetry_spool.py` | Offline telemetry |
| `roodding_evidence_bundle.py` | Summary bundle + Volgende actions |

## Safety

- **Intern disks:** alleen-lezen, Nee write mounts
- **Stick:** read-write for evidence/logs/matrix/telemetry only
- **Unsafe stick:** RAM at `/tmp/setuphelfer-evidence/` with Waarschuwing

## On-stick CLI

```bash
setuphelfer-roodding-evidence.py detect|boot|matrix|bundle|menu-action
```

## Test matrix

Files under `matrix/` — statuses: `groen|geel|rood|gray|geblokkeerd|Onbekend`.

## Volgende phase (R.4)

- Browser/display stack in live image
- Telemetry push ↔ spool integration
- MSI hardware boot verification

See: `docs/architecture/roodding_STICK_PERSISTENCE_R3.md`, `docs/architecture/roodding_TEST_MATRIX_R3.md`.
