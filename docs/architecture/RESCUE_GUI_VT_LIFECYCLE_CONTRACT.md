# Rescue GUI VT Lifecycle Contract (PI-RS-BVR-GUI-VT-PROGRESS-002)

## Owners

| VT | Owner | Notes |
|----|-------|-------|
| tty1 | TUI | Never selected as GUI VT |
| GUI VT (default 7, fallback 8/9) | Xorg + Chromium via openvt | Configurable `SETUPHELFER_RESCUE_KIOSK_VT` |

## States

`vt_unknown` → `vt_selecting` → `vt_available`/`vt_reserved` → `x_starting` → `x_ready` →
`chromium_starting` → `chromium_ready` → `vt_switching` → `gui_visible` →
(`fallback_requested`/`fallback_active`) → `gui_stopping` → `vt_releasing` → `vt_released` | `failed`

## Rules

1. Select GUI VT only after occupancy check; never kill foreign processes.
2. TUI VT is never taken for GUI.
3. DISPLAY/XAUTHORITY explicit; Chromium only after HTTP + X readiness.
4. Visibility requires: X ready, Chromium process for kiosk URL, window registered, expected VT active.
5. Watchdog fallback preserved; structured `rescue.gui.*` error codes.
6. Ordered stop of own process group with bounded terminate then kill.
7. Auto-shutdown only after VT release confirmed or timed out with evidence.
