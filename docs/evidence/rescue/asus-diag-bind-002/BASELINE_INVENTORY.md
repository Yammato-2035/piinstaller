# Baseline Inventory — PI-RS-ASUS-DIAG-BIND-002

## Gabriel

- Evidence: `docs/evidence/rescue/asus-win11-linux-001/gabriel_physical_20260722/`
- Boot: `20260722_184957_boot`
- Boot-ID: `503549ad-1af5-46fd-bcbb-131aaf5e7b47`
- Model: ROG Strix G513QM / Board G513QM / BIOS G513QM.331
- Payload on stick: 1.10.1.2

## Conflict

- Auto-Discovery attached MSI GE63 session `rescue-session-20260721T230213Z-bb356a62`
- Cause: importer used `boot_id match OR first session` fallback
- Action: excluded from Gabriel result; MSI evidence not deleted

## Missing for complete diagnosis

- NVMe serial hashes / EUI / NGUID / SMART (no Gabriel session with storage collector)
- Windows Panther/Rollback
- Physical second capture run on G513QM
