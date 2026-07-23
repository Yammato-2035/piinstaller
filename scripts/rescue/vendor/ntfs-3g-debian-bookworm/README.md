Debian bookworm ntfs-3g + fuse3 (amd64) for rescue live squashfs inject.

Do NOT inject host Ubuntu 24.04 ntfs-3g — it requires GLIBC_2.38 while the
Debian 12 live image ships an older glibc. Kernel CONFIG_NTFS3_FS is unset.
