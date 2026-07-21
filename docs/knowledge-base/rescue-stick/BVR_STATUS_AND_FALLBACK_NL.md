# BVR-status en GUI-fallback (KB)

**Task:** PI-RS-BVR-GUI-DCC-001

## Overall-statuswaarden

| Status | Betekenis |
|--------|-----------|
| `passed` | BVR + GUI zichtbaar |
| `passed_with_gui_fallback` | BVR geslaagd, GUI niet zichtbaar / fallback |
| `failed` | BVR-kern mislukt |
| `implemented_pending_physical_retest` | Fix in code, geen bevestigde MSI-run |
| `review_required` | Handmatige beoordeling nodig |

## Baseline (referentie)

Run `e2e-rescue-msi-20260721-232222-ba58c7a7`, payload `1.10.1.0`:

- BVR: **passed**
- GUI: **niet zichtbaar** (`http_server_failed`)
- Overall: **`passed_with_gui_fallback`**

## Regel

BVR-kern en GUI **apart** beoordelen. GUI-fout blokkeert backup/verify/restore niet.

## Zie ook

- [GUI_WATCHDOG_FALLBACK.md](../../rescue-stick/GUI_WATCHDOG_FALLBACK.md)
