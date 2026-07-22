# PI-RS-ASUS-DIAG-BIND-002 – Abschlussbericht

## 1. Workspace und Git
- Sauberer Worktree: `/tmp/piinstaller-asus-diag-bind-002`
- Branch: `pi-rs-asus-diag-bind-002`
- Basis: `b3ac81d3`
- Fremde Drift: unberührt

## 2. Baseline
- Gabriel G513QM / BIOS G513QM.331 / Boot 20260722_184957_boot
- Fremde MSI-Session ausgeschlossen

## 3. Gabriel-Machine-Binding
- Bound: `asus_rog_gabriel` (diagnostics only)
- Write storage/firmware/install: false

## 4. Importer-Root-Cause
- `boot_id == X or not session_id` → newest MSI
- Fix: boot_id + identity gate

## 5. Run-Control
- hardware_discovery: ok without BVR fields
- full_e2e blocked: run_control_invalid korrekt

## 6. NVMe
- Incomplete: PCI known, serial/SMART missing

## 7. Windows-Setup-Evidence
- no_setup_logs_found / insufficient_evidence

## 8. BIOS
- update_available → G513QM.335 (official ASUS EZ Flash)
- Flash: false

## 9. Zielrollen
- unassigned; write false

## 13. Endstatus
**diagnosis_incomplete**

## 14. Nächster Auftrag
Controlled Gabriel hardware_discovery with nvme-cli/smart + Panther RO mount.
