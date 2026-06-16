# R.8 — Boot Path Static Check

**Datum:** 2026-06-13  
**ISO:** `binary.hybrid.iso` (SHA256 `18d613e5…`)

## ISO-Dateien

| Pfad | Status |
|------|--------|
| `EFI/BOOT/BOOTX64.EFI` | **FOUND** |
| `boot/grub/grub.cfg` | **FOUND** |
| `boot/grub/themes/setuphelfer/theme.txt` | **FOUND** |
| `live/vmlinuz` | **FOUND** |
| `live/initrd.img` | **FOUND** |
| `live/filesystem.squashfs` | **FOUND** (~1,2 GiB) |
| `isolinux/isolinux.bin` | **FOUND** (BIOS-Fallback) |

## GRUB / Theme

| Check | Ergebnis |
|-------|----------|
| `theme.txt` | vorhanden — `desktop-image: setuphelfer-boot-menu-de.png` |
| Theme-PNG auf ISO `/boot/grub/themes/` | **nicht separat** (PNG in Squashfs `usr/share/.../boot-menu/`) |
| `set theme=` in ISO-internem `grub.cfg` | **nein** (7-Zeilen-Minimalmenü) |
| `setuphelfer_start_assistant=1` in ISO-grub cmdline | **nein** (FAT32-Writer/ESP-Layout patcht erweitertes grub.cfg beim USB-Write) |

Hinweis: ISO-internes GRUB ist **minimal**; vollständiges Branding-Menü wird beim **FAT32-ESP-USB-Write** aus `includes.binary` auf den Stick gespiegelt (wie R.5B). Squashfs enthält alle Runtime-Komponenten inkl. R.6-Hook.

## UEFI-Validierung

```
validate-rescue-iso-uefi-boot.sh → Exit 0
BOOTX64=true EFI_ELTORITO=true HYBRID=true
```

## Ampel

| Bereich | Status |
|---------|--------|
| UEFI / Live-Payload | **grün** |
| ISO-internes GRUB-Branding | **gelb** (minimal; Stick-Layout separat) |
| Blocker für USB-Write | **nein** |
