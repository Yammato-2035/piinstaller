# ASUS-02 — Fix `openvt_console_2_not_released`

Stand: 2026-08-07

## Root Cause (belegt)

Boot `20260807_173226`, Payload `55a144ae…`:

- Journal: `Started getty@tty2.service` vor GUI-Versuch
- `gui-start.log`: `openvt: Konsole 2 konnte nicht freigegeben werden`
- Watchdog blankte/wechselte VT bevor openvt erfolgreich war → Operator sah weder GUI noch TUI

`pci=noaer` auf ASUS-Cmdline ließ zudem `msi_compat_active` greifen und Fehlklassifikation begünstigen.

## Workspace-Fix

1. `setuphelfer_rescue_release_kiosk_vt` — stop + runtime-mask `getty@ttyN`, optional `fuser`/`deallocvt`
2. `setuphelfer_rescue_run_on_kiosk_vt` — Release vor openvt; Alternativ-VTs 3–7; Direct-Fallback via `setsid`/`chvt`
3. Watchdog: tty1 bis GUI-Health behalten; Blank erst nach `GUI_HEALTH_OK`; Restore bei Fail
4. Entrypoint: tty1-Restore + TUI-Rerender-Marker nach GUI-Fail
5. `msi_compat_active`: `pci=noaer` + `setuphelfer_asus_profile=` → kein MSI-Compat

## Tests

`backend/tests/test_rescue_asus02_openvt_vt_release_v1.py` (+ MSI-Regression) — passed.

## Nächster Schritt

SquashFS neu packen → Payload-Update auf Stick (nur mit Operator-Bestätigungen) → physisch ASUS-02 booten.
