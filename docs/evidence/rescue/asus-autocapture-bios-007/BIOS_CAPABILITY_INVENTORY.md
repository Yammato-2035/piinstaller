# BIOS_CAPABILITY_INVENTORY

See runtime module defaults in `backend/core/asus_lab/bios_control.py`.

Schreibbar ohne Firmware-UI (aktuell): BootOrder, BootNext via `efibootmgr`.
Secure Boot / SetupMode / TPM / VMD / Fast Boot: read or firmware-UI checklist only — no raw NVRAM invention.

`bios_capability_inventory.json` is produced per orchestrator run under `bios/`.
