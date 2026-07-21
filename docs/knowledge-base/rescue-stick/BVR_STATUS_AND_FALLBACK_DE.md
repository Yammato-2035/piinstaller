# BVR-Status & GUI-Fallback (KB)

**Task:** PI-RS-BVR-GUI-DCC-001

## Gesamtstatus-Werte

| Status | Bedeutung |
|--------|-----------|
| `passed` | BVR + GUI sichtbar |
| `passed_with_gui_fallback` | BVR bestanden, GUI nicht sichtbar / Fallback |
| `failed` | BVR-Kern fehlgeschlagen |
| `implemented_pending_physical_retest` | Fix im Code, kein bestätigter MSI-Lauf |
| `review_required` | Manuelle Bewertung nötig |

## Baseline (referenz)

Run `e2e-rescue-msi-20260721-232222-ba58c7a7`, Payload `1.10.1.0`:

- BVR: **passed** (Backup/Verify/Restore/Manifest/Auto-Shutdown)
- GUI: **nicht sichtbar** (`http_server_failed`)
- Gesamt: **`passed_with_gui_fallback`**

## DCC-Felder

`bvr_core_status`, `gui_status`, `gui_failure_code`, `watchdog_fallback_status`, `last_physical_run_status`, `traffic_lights`.

Ampel GUI bei Fallback: **gelb**, nie grün bei `unknown`.

## Regel

BVR-Kern und GUI **getrennt** bewerten. GUI-Ausfall blockiert Backup/Verify/Restore nicht.

## Siehe auch

- [GUI_WATCHDOG_FALLBACK.md](../../rescue-stick/GUI_WATCHDOG_FALLBACK.md)
- [RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md](../../operator/RESCUE_BVR_GUI_RUNTIME_RUNBOOK.md)
