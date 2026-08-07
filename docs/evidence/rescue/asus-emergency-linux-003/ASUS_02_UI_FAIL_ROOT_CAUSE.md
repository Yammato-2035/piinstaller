# ASUS-02 — Failed to start setuphelfer-rescue-ui.service / keine GUI / keine TUI

## Root Cause (belegt im Payload)

Die Live-SquashFS enthielt **nicht**:

- `setuphelfer-rescue-gui-start`
- `setuphelfer-rescue-gui-watchdog`
- `setuphelfer-rescue-entrypoint`
- `setuphelfer-rescue-tui`
- `setuphelfer-rescue-backend-start.sh`

`prepare-controlled-live-build-tree.sh` kopierte diese Skripte nicht in includes.chroot.
ASUS-00/01 wirkten trotzdem, weil `start-assistant` ohne Entrypoint eigene Whiptail-TUI hat.

ASUS-02 startet `setuphelfer-rescue-ui.service` (`kiosk=1`) → ExecStart fehlt →
**Failed to start** + Restart-Storm auf tty1 → auch TUI unbrauchbar.

## Fix

1. Prepare/Repack installieren GUI-Kette unter den Unit-Namen (ohne `.sh`)
2. `gui-start` deferiert bei `setuphelfer_start_assistant=1` (kein Doppel-Owner)
3. UI-Unit: kein ExecStartPre; SuccessExitStatus=0 5
4. Neue SquashFS SHA256: `3856a94c79ac23fdf3f40dade7e0523974dfb8af4e454867993e496d3b33e212`

## Nächster Schritt

Payload-Update auf Stick (Operator-Bestätigungen), dann erneut **nur ASUS-02**.
