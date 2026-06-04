# Runtime Governance — Boundary Guard

| Guard | Status |
|-------|--------|
| `runtime_governance/**` importiert nicht `app` | **yes** (`test_runtime_governance_module_boundaries_v1`) |
| Keine Backup/Restore/USB-Runner in governance | **yes** (manuell + Audit) |
| Keine systemd/sudo in governance | **yes** |
| `scripts/check-module-boundaries.sh` | erweitert um `runtime_governance_no_app_import` |

**Status:** `ok`
