# Rescue Machine Identity Contract

**Task:** PI-RS-ASUS-WIN11-LINUX-001  
**Module:** `backend/core/rescue_machine_identity_profiles.py`

## Purpose

Distinguish MSI GE63 (MS-16P5) and ASUS ROG (Gabriel) before any write action.

## Rules

- Read DMI from `/sys/class/dmi/id/*` (and optional dmidecode on live).
- Public/DCC status: serial masked (`…XXXX`) + `serial_hash` only.
- Profiles: `msi_ge63`, `asus_rog_gabriel`, `unknown`.
- `unknown` or `confidence=low` → diagnosis only; no install, no partition, no safe BIOS recommendation.
- ASUS exact SKU is completed after physical diagnosis.
- Operator confirmation always required for writes.

## API

`GET /api/rescue/hardware/identity`
