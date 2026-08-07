# ASUS-02 Headless — tty1 SIGHUP Race

Boot: `20260807_171519` — Profil ASUS-02, Payload `3856a94c…`, DRM ok (`amdgpudrmfb`, eDP connected).

## Ursache

`setuphelfer-rescue-ui.service` und `setuphelfer-rescue-start-assistant.service`
starteten gleichzeitig, beide mit `TTYPath=/dev/tty1` + Hangup.

Journal: Assistent `code=killed, signal=HUP` → failed.
UI `Deactivated successfully` (Defer exit 0) → kein Console-Owner → headless.

## Fix

1. UI-Unit: kein `TTYPath`; `Type=oneshot`; Journal-only IO
2. UI nicht mehr in `multi-user.target.wants` / nicht enable
3. Console-Owner ausschließlich: start-assistant → entrypoint → gui-watchdog (VT2) / TUI (tty1)

Neue SquashFS: siehe `asus02_tty1_owner_fix.sha256`
