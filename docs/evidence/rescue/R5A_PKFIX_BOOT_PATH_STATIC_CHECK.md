# R.5A PKFix — Boot Path Static Check

**ISO:** `binary.hybrid.iso`  
**Methode:** `xorriso -ls` (read-only)

## Pflichtpfade

| Pfad | Status |
|------|--------|
| `/EFI/BOOT/BOOTX64.EFI` | **FOUND** |
| `/boot/grub/grub.cfg` | **FOUND** |
| `/isolinux/isolinux.cfg` | **FOUND** |
| `/live/vmlinuz` | **FOUND** |
| `/live/initrd.img` | **FOUND** |
| `/live/filesystem.squashfs` | **FOUND** |

## Boot-Record (xorriso)

```
El Torito, MBR isohybrid cyl-align-off GPT
Volume id: SETUPHELFER_RESCUE
```

## bootappend (grub.cfg / live)

`init=/lib/systemd/systemd` + `setuphelfer_rescue=1` + `locales=de_DE.UTF-8` + `timezone=Europe/Berlin` — **FOUND**

## Bewertung

**green** — UEFI + BIOS-Hybrid + Live-SquashFS vollständig.
