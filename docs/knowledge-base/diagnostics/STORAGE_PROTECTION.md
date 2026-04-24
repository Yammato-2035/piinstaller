# Storage Write Protection (SAFE-DEVICE-1)

## Purpose

Setuphelfer must **detect** all block devices but **must not write** to arbitrary media. `validate_write_target()` enforces fail-fast rules before backups, raw images, partition layout reads, and restore staging that passes through the restore engine.

## Rules (summary)

1. **System disk** (mount includes `/`) → `STORAGE-PROTECTION-001`
2. **Boot involvement** (`/boot`, `/boot/firmware`, …) → `STORAGE-PROTECTION-002`
3. **Foreign OS heuristics** (e.g. EFI/Microsoft/Boot, NTFS + EFI pattern on non-system disks) → `STORAGE-PROTECTION-003`
4. **Path not under configured write prefixes** → `STORAGE-PROTECTION-004`
5. **Paths under `/media/` or `/run/media/`** → `STORAGE-PROTECTION-005`

## Allowed write prefixes (default)

Configured in `core.safe_device` (override with env `SETUPHELFER_BACKUP_WRITE_PREFIXES`, comma-separated absolute paths):

- `/mnt/setuphelfer`
- `/mnt/pi-installer-usb`
- `/mnt/pi-installer-clone`
- `/mnt/setuphelfer-restore-live`
- `/tmp/setuphelfer-test` (tests)
- Rescue staging: `/tmp/setuphelfer-rescue-dryrun-staging`, `/tmp/setuphelfer-restore-test`, `/tmp/setuphelfer-rescue-restore-test`, `/tmp/setuphelfer-rescue-dryrun-state`

Rescue dry-run staging under `RESCUE_DRYRUN_WRITE_PREFIXES` skips block-device classification (sandbox paths may be tmpfs/overlay).

## API

- `GET /api/system/devices` — lsblk-based list with `is_system_disk`, `is_boot_disk`, `is_foreign_os_disk`, `is_write_allowed` (information only; no auto-selection).

## Diagnostics

Matcher signal: `storage_protection` with value `storage-protection-00x` (lowercase after signal normalisation). Use `protection_signal_map()` from `core.safe_device` when turning exceptions into analyse requests.

## Integration points

- `modules.storage_detection.validate_backup_target` — after mount/fstype checks
- `modules.backup_engine` — image backup + manifest partition device
- `modules.restore_engine` — partition table, image restore, file restore targets

## Related

- `core/block_device_allowlist.py` — whole-disk patterns for `/dev/sdX`, NVMe, mmc
- `docs/faq/STORAGE_PROTECTION_FAQ.md` — user-facing FAQ (DE/EN)
