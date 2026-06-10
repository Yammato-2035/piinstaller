# RS-001 GRUB Branding Analysis

**Datum:** 2026-06-10  
**Hardware-Befund:** GRUB startet ohne Setuphelfer-Logo/grafisches Bootmenü

---

## Pflichtbefund

| Prüfung | Ergebnis |
|---------|----------|
| Logo asset vorhanden (Workspace) | **yes** (`assets/rescue/boot-menu/setuphelfer-boot-menu-de.png`) |
| GRUB theme.txt vorhanden (Workspace) | **yes** (`build/rescue/theme/grub/setuphelfer/theme.txt` via Staging-Skript) |
| Theme wird in grub.cfg referenziert | **no** (auf Stick) / **yes** (Fix 1.7.10.2 Generator) |
| Theme in BOOTX64.EFI standalone eingebettet | **no** (Bootstrap lädt externe `grub.cfg`; Theme liegt auf ESP) |
| FAT32-ESP enthält Theme-Dateien | **no** (`boot/grub/themes/setuphelfer/` fehlt auf `/dev/sdb1`) |
| BOOTX64 gfx-Module | **no** auf Stick (`gfxterm`, `png`, `all_video` fehlen in evidence.json) |

---

## Warum Hardware-GRUB ohne Logo startet

1. **Theme nie auf ESP gestaged** — `extract_iso_files()` schrieb nur `grub.cfg`, vmlinuz, initrd, squashfs; kein `boot/grub/themes/setuphelfer/`.
2. **`grub.cfg` ohne Branding** — kein `set theme=`, kein `insmod gfxterm/png`.
3. **BOOTX64.EFI minimal** — Module-Liste ohne Grafik-Module (`gfxterm`, `png`, `all_video`, `efi_gop`).
4. **ISO-binary Theme vs. FAT32-ESP** — `stage-rescue-graphical-assets.sh` staged Theme in live-build `includes.binary`, gilt nicht automatisch für FAT32-ESP-Writer.

---

## Fix decision (1.7.10.2)

| Änderung | Ziel |
|----------|------|
| `stage_grub_theme_to_fat32_staging()` in FAT32-Writer | Theme + PNG auf ESP |
| `generate_grub_cfg_branding_lines()` in `grub.cfg` | gfxterm + `set theme=` |
| `BOOTX64_MKSTANDALONE_MODULES` erweitert | Grafikmodule in EFI-Loader |
| Kein USB-Rewrite in diesem Lauf | Hardware-Retest nach separatem ESP-Update |

**Hardwarestatus:** bleibt **yellow** bis Retest mit Theme auf ESP.
