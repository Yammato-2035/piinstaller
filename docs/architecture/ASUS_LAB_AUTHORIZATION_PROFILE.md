# ASUS Lab Authorization Profile

Contract for machine-bound lab grants on Gabriel's ASUS ROG Strix G513QM.

## Profile

- ID: `ASUS_ROG_GABRIEL_LAB`
- Source: `config/lab-targets/asus-rog-gabriel.yaml`
- Scope: `machine_bound` — never transferable to MSI, developer ASUS, or unknown hosts

## Identity gate

Required for `exact_match` (grants usable):

1. Manufacturer contains ASUS
2. Board/product contains G513QM
3. `machine_id` hash equals profile
4. `system_uuid_hash` equals profile

Outcomes: `exact_match` | `partial_match` | `mismatch` | `unknown`

| Match | Read-only diagnose | Destructive / firmware / unrestricted shell |
|-------|--------------------|---------------------------------------------|
| exact | yes | yes (per grant flags) |
| partial | yes | no |
| mismatch / unknown | limited | no |

Hostname, IP, USB stick presence, or env vars alone never activate grants.

## Disk roles

Internal disks are identified by `nvme_identity_hash` (and optional serial/WWN hashes), never by `/dev/nvmeXnY` alone.

Destructive actions additionally require:

- matching disk fingerprint(s)
- `confirmed: true` on expected roles (until operator confirms)
- Rescue-stick labels (`SETUP_LOGS`, `SETUPHELFER`) excluded as write targets

## Authorization flags

YAML `authorization.*` grants bios flash, disk delete/repartition, internal restore, Windows EFI change, Secure Boot key lab, unrestricted shell, Mint install on linux_lab_nvme.

**Hard override:** `bitlocker_mutation` is always `false`. No API mutates BitLocker.

## Indirect BitLocker risk

Firmware, Secure Boot, TPM, or EFI changes may trigger BitLocker recovery UI. Operators must capture read-only BitLocker status first and warn; keys must never be logged or committed.

## Modules

- `backend/core/rescue_asus_lab_authorization.py`
- `backend/core/rescue_bitlocker_mutation_guard.py`
- `backend/api/routes/rescue_asus_lab_control.py`
