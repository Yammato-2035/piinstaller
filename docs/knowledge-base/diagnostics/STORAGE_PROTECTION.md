# Storage Write Protection (SAFE-DEVICE-1)

## Purpose

Setuphelfer must **detect** all block devices but **must not write** to arbitrary media. `validate_write_target()` enforces fail-fast rules before backups, raw images, partition layout reads, and restore staging that passes through the restore engine.

## Rules (summary)

1. **System disk** (mount includes `/`) → `STORAGE-PROTECTION-001`
2. **Boot involvement** (`/boot`, `/boot/firmware`, …) → `STORAGE-PROTECTION-002`
3. **Foreign OS heuristics** (e.g. EFI/Microsoft/Boot, NTFS + EFI pattern on non-system disks) → `STORAGE-PROTECTION-003`
4. **Path not under configured write prefixes** → `STORAGE-PROTECTION-004`
5. **Paths under `/media/` or `/run/media/`** → `STORAGE-PROTECTION-005`

## FIX-7 (systemd-automount / autofs resolution)

- `validate_write_target()` resolves mount sources via `findmnt -J -T <path>` and handles layered output (e.g. `systemd-1 autofs` + real `/dev/sdX` mount on the same target).
- If `SOURCE` is `/dev/disk/by-uuid/<uuid>`, the code resolves symlink -> real device and verifies it is a block device before classification.
- Resolution remains conservative: if no unambiguous block source can be resolved, `STORAGE-PROTECTION-004` is still raised.
- `mapper`/LVM are **not** broadly enabled by this fix.

## FIX-8 (Runtime path verification)

- R10 zeigte, dass die reine Safe-Device-Aenderung nicht reicht, wenn der aktive Runtime-Pfad noch auf einem abweichenden Validator sitzt.
- Runtime-Pruefung muss daher beide Ebenen umfassen:
  1) `core.safe_device.validate_write_target()`
  2) `modules.storage_detection.validate_backup_target()` (Backup-Target-Gate im API-Flow)
- `validate_backup_target()` nutzt jetzt dieselbe Aufloesung (`resolve_mount_source_for_path`) wie Safe-Device, damit `autofs/systemd-automount` im aktiven Backup-Pfad konsistent bewertet wird.
- In sandboxed Services mit `PrivateDevices=yes` kann `/dev/sdX` per `stat` unsichtbar sein; deshalb gibt es einen konservativen lsblk-Fallback fuer bekannte Blockquellen, ohne mapper/LVM pauschal freizugeben.

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

For `STORAGE-PROTECTION-004`, details now include:

- `mount_source_seen`
- `resolved_source`
- `fstype`
- `target`
- `reason`

## Integration points

- `modules.storage_detection.validate_backup_target` — after mount/fstype checks
- `modules.backup_engine` — image backup + manifest partition device
- `modules.restore_engine` — partition table, image restore, file restore targets

## FIX-1 (Mount / systemd / kein sudo im Tar-Pfad)

- Installationspfade: `scripts/install-system.sh` und `debian/postinst` legen **`/mnt/setuphelfer/backups`** mit **root:setuphelfer** und **0770** an.
- Backend-Unit: **NoNewPrivileges=true**, **ReadWritePaths** inkl. `/mnt/setuphelfer`; Tar in `_do_backup_logic` **ohne sudo**.
- Optional weiterhin: `SETUPHELFER_FIX_PERMISSIONS=1` + sudo nur fuer das **einmalige** Rechte-Fix (Test-VMs), nicht fuer den Normalpfad.

## Related

- `core/block_device_allowlist.py` — whole-disk patterns for `/dev/sdX`, NVMe, mmc
- `docs/faq/STORAGE_PROTECTION_FAQ.md` — user-facing FAQ (DE/EN)
