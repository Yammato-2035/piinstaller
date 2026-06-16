# Grafische Boot-Menü-Assets (Setuphelfer Rescue)

**Stand:** 2026-06-08 · Version **1.7.11.0**

## Verwendete Assets

| Asset | Quelle | Ziel (Workspace) | Ziel (Live-System) | Format | Auflösung | Zweck |
|-------|--------|------------------|--------------------|--------|-----------|-------|
| Logo2 | `setuphelfer/assets/branding/logo/logo-mascot.png` | `assets/rescue/logo/setuphelfer-logo2.png` | `/opt/setuphelfer-rescue/assets/logo/` + `/usr/share/setuphelfer/rescue/assets/logo/` | PNG (JPEG-Inhalt) | 1024×819 | Logo, Splash, Icon-Basis |
| Bootmenü DE | `scripts/rescue-live/image/branding/bootmenu-de.png` | `assets/rescue/boot-menu/setuphelfer-boot-menu-de.png` | `…/boot-menu/` | PNG (JPEG-Inhalt) | 1024×819 | GRUB-Hintergrund, Startcenter-Hintergrund (DE) |
| Bootmenü EN | `scripts/rescue-live/image/branding/bootmenu-en.png` | `assets/rescue/boot-menu/setuphelfer-boot-menu-en.png` | `…/boot-menu/` | PNG (JPEG-Inhalt) | 1024×819 | GRUB-Hintergrund, Startcenter-Hintergrund (EN) |
| Splash | Ableitung Logo2 | `assets/rescue/splash/setuphelfer-splash.png` | `…/splash/` | PNG (JPEG-Inhalt) | 1024×819 | Plymouth/Splash-Vorbereitung |
| Icon | Ableitung Logo2 | `assets/rescue/icons/setuphelfer-icon.png` | `…/icons/` | PNG (JPEG-Inhalt) | 1024×819 | Favicon/Desktop-Icon-Vorbereitung |

**Hinweis:** Die Dateien tragen `.png`-Endungen, enthalten aber JPEG-Daten (bewusst unverändert übernommen). Validierung akzeptiert PNG- und JPEG-Magic-Bytes.

## Staging & Manifest

- Staging-Skript: `scripts/rescue-live/stage-rescue-graphical-assets.sh`
- Einbindung in Build-Tree: `prepare-controlled-live-build-tree.sh` → `write_rescue_graphical_assets_overlay()`
- Manifest: `build/rescue/asset-manifest.json` (SHA256, Größe, `purpose`, `locale`, `required`)

## GRUB-Theme

- Stub: `build/rescue/theme/grub/setuphelfer/theme.txt`
- Binary-Overlay (vorbereitet): `config/includes.binary/boot/grub/themes/setuphelfer/`
- **Wichtig:** Das grafische Menübild ist **Hintergrund/Branding**. Echte Boot-Einträge bleiben in `grub.cfg` / ISOLINUX-Snippets unverändert.
- **Fallback:** Fehlen Theme-Dateien, bleibt das Textmenü über bestehende Setuphelfer-`menuentry`-Einträge aktiv.

## Live-Startcenter (React)

- UI: `frontend/src/rescue/RescueStartCenter.tsx`
- Menüdefinition: `frontend/src/rescue/rescueMenuItems.ts`
- Vite public assets: `frontend/vite.rescue.config.ts` → `publicDir: assets/rescue`
- Build-Ausgabe: `build/rescue/ui/` (wird bei Staging nach `usr/share/setuphelfer/rescue/ui/` kopiert)

## i18n-Strategie

- UI-Texte in `frontend/src/rescue/i18n/de.json` und `en.json`
- Keine hart kodierten Menütexte in TSX
- Locale-Umschaltung im Startcenter (DE/EN)
- Staging kopiert i18n nach `/opt/setuphelfer-rescue/i18n/`

## Bekannte Einschränkungen

- Kein automatischer SVG→PNG-Build (rsvg-Abhängigkeit bewusst vermieden)
- GRUB-Theme ist vorbereitet, **nicht** im echten ISO/Stick bewiesen (kein ISO-Build in diesem Auftrag)
- React-Startcenter ist im Workspace gebaut, **nicht** im Stick-SquashFS verifiziert
- ISOLINUX `MENU TITLE` enthält weiterhin „Setuphelfer Rettungsstick“ (bestehend, nicht geändert)
