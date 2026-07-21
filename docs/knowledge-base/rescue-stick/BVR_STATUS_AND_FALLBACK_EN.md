# BVR Status & GUI Fallback (KB)

**Task:** PI-RS-BVR-GUI-DCC-001

## Overall status values

| Status | Meaning |
|--------|---------|
| `passed` | BVR + GUI visible |
| `passed_with_gui_fallback` | BVR passed, GUI not visible / fallback |
| `failed` | BVR core failed |
| `implemented_pending_physical_retest` | Fix in code, no confirmed MSI run |
| `review_required` | Manual assessment needed |

## Baseline (reference)

Run `e2e-rescue-msi-20260721-232222-ba58c7a7`, payload `1.10.1.0`:

- BVR: **passed** (backup/verify/restore/manifest/auto-shutdown)
- GUI: **not visible** (`http_server_failed`)
- Overall: **`passed_with_gui_fallback`**

## DCC fields

`bvr_core_status`, `gui_status`, `gui_failure_code`, `watchdog_fallback_status`, `last_physical_run_status`, `traffic_lights`.

GUI traffic light on fallback: **yellow**, never green when `unknown`.

## Rule

Evaluate BVR core and GUI **separately**. GUI failure does not block backup/verify/restore.

## See also

- [GUI_WATCHDOG_FALLBACK.md](../../rescue-stick/GUI_WATCHDOG_FALLBACK.md)
- [RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md](../../operator/RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md)
