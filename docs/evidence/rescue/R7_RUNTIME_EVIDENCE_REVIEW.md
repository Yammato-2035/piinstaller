# R.7 — Stick Runtime Evidence Review

**Datum:** 2026-06-10  
**Mount:** `/media/gabriel/SETUPHELFER` (read-only Auswertung)

## `/setuphelfer-evidence/`

| Check | Status |
|-------|--------|
| Verzeichnis vorhanden | **nein** |

## Erwartete Unterverzeichnisse (nach Live-Boot)

| Verzeichnis | Status |
|-------------|--------|
| `boot/` | **fehlt** |
| `menu/` | **fehlt** |
| `hardware/` | **fehlt** |
| `telemetry/` | **fehlt** |
| `matrix/` | **fehlt** |
| `summaries/` | **fehlt** |

## Vorhanden (Write-Time, nicht Runtime)

| Pfad | Status |
|------|--------|
| `EFI/BOOT/BOOTX64.EFI` | vorhanden |
| `boot/grub/grub.cfg` | vorhanden |
| `live/vmlinuz`, `live/initrd.img`, `live/filesystem.squashfs` | vorhanden |
| `setuphelfer/rescue/evidence.json` | vorhanden |
| `setuphelfer/rescue/version.json` | vorhanden |

## Inventar-Methode

```bash
find /media/gabriel/SETUPHELFER/setuphelfer-evidence -type f
# → leer / nicht vorhanden
```
