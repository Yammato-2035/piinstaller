# Rescue USB Operator Selection — Developer Toolbox

**Prompt:** `RESCUE_USB_OPERATOR_SELECTION_AND_WRITE_CONFIRMATION_TOOLBOX`  
**Datum:** 2026-06-05

## Ziel

Kein blindes `dd` — Operator wählt USB-Stick explizit im DCC Developer Toolbox, bestätigt Checkboxen + Textphrase, Evidence wird geschrieben; DCC zeigt nur den Operator-Befehl.

## Backend

- `backend/core/rescue_usb_operator_selection.py`
- `GET /api/dev-dashboard/rescue-usb/candidates` (read-only lsblk via `safe_device`)
- `GET|POST /api/dev-dashboard/rescue-usb/selection` (Evidence)
- Evidence: `docs/evidence/runtime-results/rescue/usb_operator_selection_latest.json`
- Compact-Status: `rescue.usb_operator` + Blocker-Codes

## Blocker (ohne Freigabe)

- `RESCUE_USB_OPERATOR_SELECTION_REQUIRED`
- `RESCUE_USB_DESTRUCTIVE_WRITE_NOT_CONFIRMED`
- `RESCUE_USB_OLD_VERSION_REPLACE_NOT_CONFIRMED` (bei erkanntem SETUPHELFER_RESCUE / iso9660)

## Sicherheit

- Kein dd aus DCC (`dd_execution_allowed: false` immer)
- `/dev/sda`, `/dev/nvme*`, System-/Boot-Disk, Backup-Mounts blockiert
- Nur USB-Transport (`tran=usb`) wählbar
- Textphrase exakt: `WRITE SETUPHELFER RESCUE USB`

## Frontend

- `RescueUsbOperatorToolbox.tsx` (DCC Tab Rescue, nur bei Developer Capability)
- Tests: `rescueUsbOperatorToolbox.test.ts`, `test_rescue_usb_operator_selection_v1.py`

## Next Prompt

`RESCUE_USB_WRITE_OPERATOR_FOR_WINDOWS_INSPECT` (manueller dd-Lauf nach Freigabe)
