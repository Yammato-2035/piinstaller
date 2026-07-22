# PHYSICAL_DIAGNOSIS_RESULT — PI-RS-ASUS-DIAG-BIND-002

## Machine Binding

- Profile: `asus_rog_gabriel`
- Model: ROG Strix G513QM / Board G513QM
- BIOS installed: G513QM.331
- Operator phrase confirmed (documented bind)
- Write permissions: diagnostics only (no storage/firmware/install)

## Importer

- Root cause: `boot_id match OR newest session` fallback attached MSI GE63 session
- Fix: require boot_id match + manufacturer/board compatibility
- Re-import: `session_imported=false`, status `identity_conflict_session_excluded`
- MSI evidence preserved, not deleted

## Run type

- Declared: `hardware_discovery`
- MSI `run_control_invalid` correct for full_e2e, **incorrect** as discovery failure
- Discovery import allowed without BVR run-control

## BIOS (official ASUS)

- Support: https://www.asus.com/supportonly/g513qm/helpdesk_bios/
- Installed: G513QM.331 (DMI date 2023-02-24; Windows package dated 2023/03/30)
- Latest EZ Flash: **G513QM.335** (2025-12-24)
- Status: `update_available`
- Flash: **not performed**

## NVMe

- Two Samsung controllers at 0000:04:00.0 and 0000:05:00.0
- Serial/EUI/NGUID/SMART: **missing** (auto_discovery=0 on capture)
- Roles: unassigned, write_allowed=false

## Windows evidence

- Panther/Rollback: **not found** / not scanned on this capture
- Likely cause confidence: **low**
- Plausible: partition layout (nvme0 has p1–p3; nvme1 empty in dmesg); BIOS lag vs 335

## Endstatus

`diagnosis_incomplete`

Next: controlled Gabriel hardware_discovery with nvme-cli/smart + read-only Panther scan.
