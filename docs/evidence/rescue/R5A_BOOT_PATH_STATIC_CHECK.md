# R.5A — Boot-Pfad Statische Prüfung

**ISO:** `binary.hybrid.iso` (SHA256 `4f511322…`)

## ISO9660 / Hybrid

| Pfad | Status |
|------|--------|
| `/EFI/BOOT/BOOTX64.EFI` | **FOUND** |
| `/boot/grub/grub.cfg` | **FOUND** |
| `/boot/grub/themes/setuphelfer/theme.txt` | **FOUND** |
| `/boot/grub/themes/setuphelfer/setuphelfer-boot-menu-de.png` | **FOUND** |
| `/isolinux/isolinux.cfg` | **FOUND** |
| `/isolinux/isolinux.bin` | **FOUND** |
| `/live/vmlinuz` | **FOUND** |
| `/live/initrd.img` | **FOUND** |
| `/live/filesystem.squashfs` | **FOUND** (530.9M) |
| `/live/filesystem.packages` | **FOUND** |

## UEFI Validator

```text
OK: rescue ISO UEFI-x64 — BIOS=true EFI_ELTORITO=true PLAIN_UEFI=true HYBRID=true BOOTX64=true
```

## Bewertung

**green** — Boot-Pfad vollständig (BIOS + UEFI + Live-SquashFS).
