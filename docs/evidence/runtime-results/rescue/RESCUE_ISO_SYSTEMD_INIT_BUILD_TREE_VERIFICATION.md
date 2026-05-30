# Rescue ISO — systemd Init Build-Tree Verification

**prepare:** Exit 0

| Check | Status |
|-------|--------|
| `systemd`, `systemd-sysv`, `dbus` | ja |
| `init=/lib/systemd/systemd` in bootappend | ja |
| `multi-user.target.wants` Symlinks | ja |
| DE keyboard/locale/TZ | unverändert |

**Alte ISO:** Validator Exit **15** (`SYSTEMD_INIT_GAP`) — erwartet bis Rebuild.

JSON: `rescue_iso_systemd_init_build_tree_verification_latest.json`
