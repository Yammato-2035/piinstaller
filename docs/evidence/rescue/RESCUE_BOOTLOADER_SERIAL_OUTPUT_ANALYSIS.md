# Rescue Bootloader Serial Output — IST Analysis

**Profil:** `developer-qemu` (ISO `be016f2a…`, Build 2026-06-01)

## ISOLINUX / BIOS-Pfad (QEMU `-boot d`)

| Prüfung | IST (vor Fix) |
|---------|----------------|
| `isolinux.cfg` | `include menu.cfg` / `default vesamenu.c32` / `prompt 0` / **`timeout 0`** |
| `SERIAL 0 115200` | **fehlt** |
| `CONSOLE 0` | **fehlt** |
| Auto-Boot | **nein** (`timeout 0` = unbegrenzt warten) |
| Headless + `-display none` | **hängt im Menü** |

## Kernel-Cmdline (live.cfg / ISO)

| Prüfung | IST |
|---------|-----|
| `console=tty0` | **yes** |
| `console=ttyS0,115200n8` | **yes** |
| `loglevel=7` / systemd debug | **yes** |
| `quiet splash` im Live-append | **no** |

**Fazit:** Kernel-Cmdline allein reicht nicht, wenn der Bootloader nie zum Kernel kommt.

## GRUB / UEFI-Pfad

Aktuelles `binary.hybrid.iso` (7z-Listing): primär **ISOLINUX**-Layout; kein separates `EFI/…/grub.cfg` im ISO9660-Baum sichtbar. QEMU-Smoke mit `-cdrom` nutzt typisch **BIOS/ISOLINUX**.

GRUB-Serial-Hook ist für künftige EFI-Ausgaben vorbereitet (`095-developer-qemu-grub-serial.hook.binary`).

## Auto-Boot / Timeout

| | IST | Soll (developer-qemu) |
|---|-----|------------------------|
| Menü-Timeout | 0 (∞) | 30 (3 s) |
| Default | vesamenu.c32 | `live-` |
| vesamenu | yes | umgangen (direkt `live.cfg`) |

## Bootmenü-Risiko mit neuem ISO

Selbst mit korrekter Kernel-Cmdline im ISO blieb Serial **0 B**, weil der Gast vermutlich **nie** aus dem ISOLINUX-Menü bootete.
