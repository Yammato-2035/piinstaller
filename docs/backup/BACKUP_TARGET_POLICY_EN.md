# Backup target policy (Setuphelfer) — English

## Principles

- Backups should **preferably be stored on external media**, not on the root, boot, or system volume.
- Setuphelfer **does not destroy existing data**, **does not format drives automatically**, and **does not partition** on behalf of the user.
- If no **unambiguously safe external** target can be determined, backup stays **blocked** (`blocked` / `review_required`).
- If the service user **cannot traverse** or **cannot write** the chosen path, there is **no** silent fallback to internal space — an **explicit operator/user approval** is required (see diagnosis **STORAGE-PROTECTION-006** / API code **`backup.target_traverse_denied`** after the backend is updated).

## External media priority (highest first)

1. External **NVMe** (e.g. USB-NVMe enclosure; infer from `TRAN`/model where reasonable)
2. External **SSD** (SATA/NVMe in USB enclosure)
3. External **HDD**
4. **USB flash drive** (typically smaller/slower; only if clearly acceptable and enough free space)
5. **SD card** (only if clearly external, rw, suitable filesystem, enough free space)

**Not** acceptable as backup targets: the root filesystem (`/`), internal system NVMe, boot/EFI, Windows system partitions, paths that live only under `/tmp`, `/home`, `/var` without a dedicated external block device, **readonly** media, media without sufficient **free** space.

## Strategic mount path (documentation)

**`/media/setuphelfer/setuphelfer-back`** is a **conventional target path** **only** when it resides on a **chosen external block device** (mount resolves to a `/dev/...` device that is not the system disk).

- **Forbidden:** creating that path as a normal directory on the root filesystem or using internal NVMe as its backing store.
- **No automatic bind mounts** and **no** automatic ACL/permission changes without explicit approval.
- If the volume is already mounted elsewhere (e.g. **`/media/<user>/setuphelfer-back`**), there is **no** automatic path rewrite — agree with the operator whether the strategic path requires move/mount/bind.

## API note

**target-check** validates mount source, device classification, and (under `/media` / `/run/media`) traversability. Without a safe external target: **blocked**, no backup start.

## Related documents

- `docs/backup/BACKUP_TARGET_POLICY_DE.md`
- `docs/knowledge-base/backup/BACKUP_TARGET_SELECTION.md`
- `docs/faq/BACKUP_RESTORE_FAQ_EN.md`
