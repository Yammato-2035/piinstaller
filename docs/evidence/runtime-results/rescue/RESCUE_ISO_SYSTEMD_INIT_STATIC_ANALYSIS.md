# Rescue ISO — systemd Init Static Analysis

## Befund (ISO 3731d123…, Validator vor Fix Exit 0)

| Prüfung | Ergebnis |
|---------|----------|
| Pakete `systemd`, `systemd-sysv` in chroot-Liste | ja |
| `usr/lib/systemd/systemd` in Squashfs | ja |
| `/usr/sbin/init` → systemd Symlink | **nein** (eigenes Binary + `/etc/inittab` SysV) |
| `init=/lib/systemd/systemd` in ISOLINUX `live.cfg` | **nein** |
| Enable-Symlinks Setuphelfer | ja (offline) |

## Ursache

**`unit_enable_present_but_init_not_systemd`** / **`bootappend_init_missing`**

Enable-Symlinks wirken nur, wenn **PID 1 systemd** ist. Ohne `init=/lib/systemd/systemd` bootet Debian-Live mit SysV-Init → `systemctl` und Backend-Units starten nicht.

## Fix (Build-Tree)

- `dbus` in `setuphelfer.list.chroot`
- `--bootappend-live` ergänzt: **`init=/lib/systemd/systemd`**
- Validator Exit **15**, wenn `live.cfg` ohne `init=`

JSON: `rescue_iso_systemd_init_static_analysis_latest.json`
