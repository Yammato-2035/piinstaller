# Rescue Controlled Live Build — Tool Check

**Datum:** 2026-05-24 (ISO-Build-Session)
**Git HEAD:** `e7e2e07`

## Ergebnis

**Status:** **ok** — alle erforderlichen Build-Tools vorhanden.

| Tool | vorhanden | Pfad | Bemerkung |
|------|-----------|------|-----------|
| lb | **ja** | `/usr/bin/lb` | live-build |
| xorriso | **ja** | `/usr/bin/xorriso` | ISO-Erzeugung |
| mksquashfs | **ja** | `/usr/bin/mksquashfs` | Squashfs |
| sha256sum | **ja** | `/usr/bin/sha256sum` | Prüfsummen |
| tar | **ja** | `/usr/bin/tar` | Archiv |
| rsync | **ja** | `/usr/bin/rsync` | Bundle-Kopie |

**Hinweise:** PackageKit irrelevant; Chrome-i386-APT-Warnung nicht build-blockierend.

**real_iso_build_allowed_for_task:** true (expliziter Auftrag)  
**usb_write_allowed:** `false`
