# Internal disk no-touch evidence

- Root before/after: `/dev/nvme1n1p2` on `nvme1n1`
- Internal disks before/after: `nvme0n1`, `nvme1n1` only
- No new partitions/filesystems/mounts on internal disks
- Updater target only `/dev/sda` / `/dev/sda1`
- See `lsblk_before.txt`, `lsblk_after.txt`, `internal_disks_before.json`, `internal_disks_after.json`
