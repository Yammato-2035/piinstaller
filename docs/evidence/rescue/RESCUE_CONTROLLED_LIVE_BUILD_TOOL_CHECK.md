# Rescue Controlled Live Build — Tool Check

**Datum:** 2026-05-25 (Pre-Build-Ready)
**Git HEAD:** `27d790a`

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
| lsblk | **ja** | `/usr/bin/lsblk` | Geräte-Identifikation |
| findmnt | **ja** | `/usr/bin/findmnt` | Systemdisk-Schutz |
| wipefs | **ja** | `/usr/sbin/wipefs` | Read-only Signatur-Check bei Bedarf |
| isohybrid | **ja** (Host) | `/usr/bin/isohybrid` | Paket `syslinux-utils`; **Binary-Chroot** braucht `setuphelfer.list.binary` |

**Hinweise:** Host-`isohybrid` allein reicht nicht — `lb_binary_iso` ruft `isohybrid` im Binary-Chroot auf (`RESCUE-BUILD-ISOHYBRID-001`).

**Hinweise (allgemein):** PackageKit irrelevant; Chrome-i386-APT-Warnung nicht build-blockierend. Alle für ISO- und USB-Gate relevanten Prüftools sind vorhanden.

**real_iso_build_allowed_for_task:** true (expliziter Auftrag)  
**usb_write_allowed:** `false`
