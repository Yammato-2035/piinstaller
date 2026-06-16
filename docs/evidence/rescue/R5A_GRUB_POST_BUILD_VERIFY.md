# R.5A — GRUB Post-Build Verifikation

## verify-rescue-grub-theme.sh (Build-Tree)

Exit **5** — `grub.cfg` im Build-Tree fehlt (erwartet nach lb nur in ISO-Binary).

## ISO-Binary (manuell)

| Prüfung | Status |
|---------|--------|
| `/boot/grub/grub.cfg` | **FOUND** |
| `/boot/grub/themes/setuphelfer/theme.txt` | **FOUND** |
| `/boot/grub/themes/setuphelfer/setuphelfer-boot-menu-de.png` | **FOUND** |
| Theme in `grub.cfg` (`set theme=`) | **MISSING** |
| ISOLINUX `/isolinux/isolinux.cfg` | **FOUND** |
| `/EFI/BOOT/BOOTX64.EFI` | **FOUND** (3.1M) |
| UEFI validate script | **Exit 0** |

## grub.cfg Inhalt (Auszug)

```text
set timeout=5
set default=0
search --set=root --file /live/filesystem.squashfs
menuentry "Setuphelfer Rescue Live" { … }
```

Kein `set theme=/boot/grub/themes/setuphelfer/theme.txt`.

## Bewertung

| Aspekt | Ampel |
|--------|-------|
| Theme-Assets | **green** |
| Theme-Einbindung grub.cfg | **yellow** |
| UEFI BOOTX64 | **green** |
| ISOLINUX Fallback | **green** |
| Grafisches GRUB gesamt | **yellow** |

Assets vorhanden, Theme **nicht aktiviert** in grub.cfg.
