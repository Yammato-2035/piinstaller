# Rescue NVMe Install Target Contract

**Module:** `backend/core/rescue_nvme_install_target.py`

## Rules

- Never bind roles from `/dev/nvme0n1` vs `nvme1n1` alone.
- Stable key: model + serial_hash + size_bytes + PCI path + NGUID/EUI.
- Roles: `windows`, `linux`, `unassigned`.
- `write_allowed` default false; separate grants per disk.
- Manifest: `asus_rog_install_targets.json` pattern via `build_asus_install_targets_manifest()`.
- Device rename after reboot must re-resolve via serial_hash.

## Health

`healthy` | `review_required` | `unsuitable_for_install` | `unknown`  
Install blocked on `unsuitable_for_install`.
