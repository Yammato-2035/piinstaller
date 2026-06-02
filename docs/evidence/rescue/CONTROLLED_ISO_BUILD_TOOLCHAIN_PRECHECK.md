# Controlled ISO Build — Toolchain Precheck

**Stand:** 2026-06-02  
**Status:** **ok**

## Tools (read-only)

| Tool | Pfad |
|------|------|
| `lb` / `live-build` | `/usr/bin/lb` — 3.0~a57-1 |
| `debootstrap` | `/usr/sbin/debootstrap` |
| `mksquashfs` | 4.6.1 |
| `xorriso` | 1.5.6 |
| `genisoimage` | 1.1.11 |
| `isohybrid` | 0.12 |
| `syslinux` | `/usr/bin/syslinux` |
| `rsvg-convert` | 2.58.0 |
| `grub-mkrescue` | vorhanden |

## Bekannte Themen

| ID | Bewertung |
|----|-----------|
| RESCUE-BUILD-TOOL-001 | **ok** — `rsvg-convert` vorhanden |
| RESCUE-BUILD-RSVG-001 | **ok** — `/usr/bin/rsvg` fehlt, **Compat-Wrapper** `build/rescue/tool-compat/bin/rsvg` vorhanden; `prepare-controlled-live-build-tree.sh` seedet `config/includes.chroot/usr/local/bin/rsvg` |
| RESCUE-BUILD-ISOHYBRID-001 | **ok** — `isohybrid` vorhanden |

## Nicht ausgeführt

Kein `apt install/upgrade`.
