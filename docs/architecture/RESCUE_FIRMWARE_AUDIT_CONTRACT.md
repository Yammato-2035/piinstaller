# Rescue Firmware Audit Contract

**Modules:** `rescue_firmware_inventory.py`, `rescue_bios_official_compare.py`

## Rules

- Inventory is read-only.
- Official sources only: ASUS Support, MSI Support, optional LVFS metadata.
- Third-party BIOS portals rejected.
- `update_available` is a recommendation only → end state `bios_checked`, never `bios_updated`.
- No flashrom, no capsule flash, no automatic download execution.
- Offline → `latest_version_unknown_offline`.
- Ambiguous model → `blocked_model_ambiguous`.
