# Stage A Result — PI-RS-ASUS-WIN11-STAGE-A-006

## Completed in this run
- Runtime /opt → **1.9.21.2** (runtime-opt, Tauri skipped, gate OK)
- Payload **1.10.2.3** injected to Ultra Line stick
- WinPE collector on SETUP_LOGS + in squashfs
- API `/api/rescue/win11-retest/*` probed HTTP 200

## Pending operator
- Confirm Windows/Linux NVMe roles
- Isolate Linux NVMe
- Verify official Windows 11 media
- Execute Stage A install under BIOS **G513QM.331**
- Collect Panther/Rollback/SetupDiag on abort, or postcheck on success

## Endstatus
`ready_for_windows_retest_bios331`
