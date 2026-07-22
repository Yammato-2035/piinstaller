# Rescue Machine Identity Contract

**Task:** PI-RS-ASUS-WIN11-LINUX-001  
**Module:** `backend/core/rescue_machine_identity_profiles.py`

## Purpose

Distinguish MSI GE63 (MS-16P5) and ASUS ROG (Gabriel) before any write action.

## Rules

- Read DMI from `/sys/class/dmi/id/*` (and optional dmidecode on live).
- Public/DCC status: serial masked (`…XXXX`) + `serial_hash` only.
- Profiles: `msi_ge63`, `asus_rog` (generic), `asus_rog_gabriel` (nur nach Operator-Bind), `unknown`.
- `asus_rog_gabriel` wird **niemals** allein aus DMI gesetzt.
- Bekannter Development-Host (`G713PI` / Volker) ist `is_developer_workstation=true` und darf nicht als Gabriel gebunden werden.
- `unknown` or `confidence=low` → diagnosis only; no install, no partition, no safe BIOS recommendation.
- ASUS exact SKU for Gabriel is completed after physical diagnosis + `POST /api/rescue/hardware/bind-gabriel`.
- Operator confirmation always required for writes.

## API

`GET /api/rescue/hardware/identity`


## Fingerprint 1.1

See `build_machine_fingerprint()` — manufacturer, product, board required; UUID/board serial hashed; GPU/storage PCI IDs optional.

Gabriel bind requires G513QM + operator phrase and sets write_permissions diagnostics-only.

## PI-RS-ASUS-PHYSICAL-DIAG-003

- `hardware_discovery` requires no BVR run_control.
- NVMe identity: model + serial_hash + EUI/NGUID + nsid + PCI (never `/dev/nvmeXn1` alone).
- Write authorization stays false after provisional role_binding.
