# Rescue Stick — Logging, Evidence and Test Matrix (R.3)

## Overview

Campaign R.3 stabilizes boot, menu, and diagnostics on the Setuphelfer rescue stick. All results are stored persistently under:

```
/setuphelfer-evidence/
```

## Modules

| Module | Role |
|--------|------|
| `rescue_persistence.py` | Stick detection, evidence tree |
| `rescue_boot_logger.py` | Boot/menu context |
| `rescue_test_matrix.py` | 20-area status matrix |
| `rescue_msi_diagnostics.py` | MSI hardware (read-only) |
| `rescue_telemetry_spool.py` | Offline telemetry |
| `rescue_evidence_bundle.py` | Summary bundle + next actions |

## Safety

- **Internal disks:** read-only, no write mounts
- **Stick:** read-write for evidence/logs/matrix/telemetry only
- **Unsafe stick:** RAM at `/tmp/setuphelfer-evidence/` with warning

## On-stick CLI

```bash
setuphelfer-rescue-evidence.py detect|boot|matrix|bundle|menu-action
```

## Test matrix

Files under `matrix/` — statuses: `green|yellow|red|gray|blocked|unknown`.

## Next phase (R.4)

- Browser/display stack in live image
- Telemetry push ↔ spool integration
- MSI hardware boot verification

See: `docs/architecture/RESCUE_STICK_PERSISTENCE_R3.md`, `docs/architecture/RESCUE_TEST_MATRIX_R3.md`.
