# Rescue Boot-Menü & Branding

**Stand:** 2026-06-07 · Version **1.7.7.0**

## Umsetzung

| Ebene | Inhalt |
|-------|--------|
| **ISOLINUX** | `MENU TITLE Setuphelfer Rettungsstick`, `MENU BACKGROUND /bootlogo`, Einträge in `live.cfg.in` |
| **GRUB/UEFI** | Zusätzliche `menuentry`-Blöcke per Binary-Hook + Snippet-Referenz |
| **SquashFS** | ASCII-Branding `/usr/share/setuphelfer/rescue/boot-branding.txt` |
| **Start Assistant** | Willkommensdialog zeigt dasselbe ASCII-Logo |

## Menüeinträge (ISOLINUX/GRUB)

1. Setuphelfer Rettung starten (Default)  
2. Setuphelfer Rettung mit Netzwerk-Assistent  
3. Setuphelfer MSI/NVIDIA-Kompatibilitätsmodus (`pci=noaer nomodeset`)  
4. Setuphelfer Diagnosemodus ohne Änderungen  
5. Setuphelfer Start in RAM / Media-Check (`toram`)  
6. Neustart / Herunterfahren  

Quellen:

- `scripts/rescue-live/image/setuphelfer-rescue-boot-menu-snippet.cfg`
- `scripts/rescue-live/image/setuphelfer-rescue-grub-menu-snippet.cfg`
- Hook: `config/hooks/normal/020-setuphelfer-rescue-boot-menu.hook.binary` (im Build-Tree)

## Logo / PNG

SVG-Assets existieren unter `website/hotfix-upload/setuphelfer-theme/assets/branding/` — **kein** automatisches SVG→PNG im Build (rsvg-Abhängigkeit). Aktuell: **Text/ASCII + MENU TITLE** als robuste Lösung.

## Validator

Nach `prepare-controlled-live-build-tree.sh`:

- `live.cfg.in` enthält `label setuphelfer-rescue-default`
- Hook enthält `Setuphelfer Rettung starten`
- `boot-branding.txt` im chroot-Overlay

Siehe auch: [RESCUE_START_ASSISTANT_OVERVIEW.md](../knowledge-base/rescue/RESCUE_START_ASSISTANT_OVERVIEW.md)
