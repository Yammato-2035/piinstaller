# 02 – Physical Run Result

Erfasst: `2026-07-21T21:23:32Z`

## Gerät / Payload
- MSI GE63 Raider RGB 8RF / MS-16P5
- Payload: **1.10.1.0**
- Boot-ID: `1b3feb71-2f89-43a6-9505-d131f07fab6b`
- Run-ID: `e2e-rescue-msi-20260721-232222-ba58c7a7`

## Cmdline (Default GUI Physical E2E)
```text
setuphelfer_mode=gui
setuphelfer_kiosk=1
setuphelfer_gui_watchdog=1
setuphelfer_msi_e2e_auto=1
setuphelfer_auto_shutdown=1
setuphelfer_auto_discovery=0
```

## Backup / Verify / Restore
| Schritt | Ergebnis |
|---------|----------|
| SABRENT Identity / Wipe+Layout | ok (`dedicated_external_lab_hdd`) |
| Backup | **passed** (162 Dateien, 135 313 271 Bytes) |
| Verify | **passed** (`backup_recovery.ok`) |
| Restore | **passed** (162 Dateien, Manifest match) |
| Vergleich | file/bytes/manifest **match** |
| Workflow-Status | `physical_rescue_backup_restore_e2e_passed` |
| Terminal Run-Control | `physical_rescue_passed_server_verification_pending` |
| Auto-Shutdown | ja (`shutdown_reason=e2e_complete`, phase `auto_shutdown_physical_e2e_complete`) |

## GUI
| Check | Ergebnis |
|-------|----------|
| GUI per cmdline angefordert | ja |
| Fortschritts-URL vorbereitet | `http://127.0.0.1:8765/auto-e2e-progress.html` |
| GUI sichtbar gestartet | **nein** (`rescue-ui-status`: `http_server_failed`) |
| gui-availability | `msi_compat_nomodeset` / disabled |
| Watchdog-/TUI-Fallback | **ja** (BVR lief unattended weiter) |

Cloud-Diagnose HTTP 404 ist erwartet (offline / `diagnostics_required=false`) und blockiert den BVR-Erfolg nicht.
