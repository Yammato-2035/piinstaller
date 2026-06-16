# Grafische Boot-Menü-Integration — Ergebnisbericht

**Datum:** 2026-06-08  
**HEAD (vorher):** `27b0829`  
**Branch:** `main`  
**Runtime-Gate:** Exit 20 (dev-dashboard 404) — **nur statische Integration**, kein Runtime-Smoke

## Verwendete Assets

| Asset | Workspace-Pfad |
|-------|----------------|
| Logo2 | `assets/rescue/logo/setuphelfer-logo2.png` |
| Bootmenü DE | `assets/rescue/boot-menu/setuphelfer-boot-menu-de.png` |
| Bootmenü EN | `assets/rescue/boot-menu/setuphelfer-boot-menu-en.png` |
| Splash | `assets/rescue/splash/setuphelfer-splash.png` |
| Icon | `assets/rescue/icons/setuphelfer-icon.png` |

## Zielpfade (Live-System, vorbereitet)

- `/opt/setuphelfer-rescue/assets/{logo,boot-menu,splash,icons}/`
- `/usr/share/setuphelfer/rescue/assets/…` (Spiegel)
- `/opt/setuphelfer-rescue/i18n/{de,en}.json`
- `/usr/share/setuphelfer/rescue/ui/` (nach React-Build)
- GRUB-Theme: `boot/grub/themes/setuphelfer/` (binary includes)

## Integrationsstatus

| Bereich | Status |
|---------|--------|
| Asset-Struktur `assets/rescue/` | **done** |
| Staging-Skript + Manifest | **done** |
| `prepare-controlled-live-build-tree.sh` Hook | **done** |
| GRUB-Theme-Stub | **done** (partial — Theme staged, Bootlogik unverändert) |
| Live-Startcenter (React) | **done** (Workspace; nicht im Stick-SquashFS bewiesen) |
| i18n DE/EN | **done** |
| Version 1.7.11.0 | **done** |

## Tests

- `backend/tests/test_rescue_graphical_assets_v1.py` — Assets, i18n, verbotene Phrasen, Menü-Safety
- Bestehend: `backend/tests/test_rescue_react_ui_contract_v1.py`

Kein ISO-Build, kein QEMU, kein USB-Write.

## Was funktioniert jetzt (statisch)

- Kanonische Assets liegen unter `assets/rescue/` mit dokumentierter Herkunft
- Staging kopiert Assets + i18n in Live-Build-Tree-Overlay
- `build/rescue/asset-manifest.json` mit SHA256/Größe/Zweck
- React-Startcenter mit grafischem Hintergrund und datengetriebenen Menüpunkten
- High-Risk-Aktionen (`backup_create`, `restore`, `cloudserver_manage`) sind `enabled: false`

## Was noch nicht bewiesen ist

- Echter ISO-Build mit GRUB-Theme im Bootmenü
- Hardware-Boot mit grafischem Hintergrund auf `/dev/sdb`
- React-UI im Stick-SquashFS (RS-001 bleibt gelb bis Rebuild/Repack)
- Plymouth/Splash im Live-Start

## Offene Punkte

- ISOLINUX `MENU TITLE Setuphelfer Rettungsstick` (Legacy, unverändert)
- JPEG-in-PNG-Dateien: funktional lesbar, semantisch PNG-Endung
- Operator-Rebuild: `prepare-controlled-live-build-tree.sh` + kontrollierter `lb build` ausstehend

## Push

Nicht durchgeführt (nur Workspace-Integration).
