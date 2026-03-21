# Visuelle Assets — Integration (2026-03-21)

## Verwendete Bilder (Raster)

| Pfad | Inhalt |
|------|--------|
| `website/setuphelfer-theme/assets/images/hero/hero-raspberry-pi-laptop-setup.jpg` | Foto: Raspberry Pi + Motorola Lapdock (CC BY 2.0) |
| `website/setuphelfer-theme/assets/images/hero/hero-linux-laptop-workstation.jpg` | Foto: Laptop am Schreibtisch (CC0) |
| `website/setuphelfer-theme/assets/images/setup/setup-raspberry-pi-real.jpg` | Kopie Hero-Pi (About) |
| `website/setuphelfer-theme/assets/images/setup/setup-linux-workstation.jpg` | Kopie Hero-Laptop (About) |
| `website/setuphelfer-theme/assets/images/projects/project-raspberry-pi-hardware.jpg` | Foto: Raspberry Pi 4 Board (CC BY-SA 4.0) |

## Einbindung

- **Startseite Hero** (`snippets/index.html`): beide Hero-JPEGs im Raster, darunter App-Rahmen mit `{{TAURI_SHOT:screenshot-dashboard.png|…}}`; Bildnachweise `home-photo-credits`; Markenhinweis `home-brand-notice`.
- **Über** (`snippets/about.html`): beide Setup-JPEGs.
- **Projekt Medienserver** (`snippets/project-media-server.html`): `project-raspberry-pi-hardware.jpg` + Captions.

## Ersetzt

- Hero-Seiten-Illustrationen (`hero-pi-desktop.svg`, `hero-tux-linux-laptop.svg`) in der **Hero-Section** und in **About** durch die obigen Fotos.

## Symlink

- `assets/images/screenshots` → `../screenshots` (kanonische App-PNGs bleiben unter `assets/screenshots/`).

## Lizenzen

Siehe `assets/images/ASSET_SOURCES.md`.

## Selbstprüfung (Kurz)

| Prüfpunkt | Erfüllt |
|-----------|---------|
| Hero: echte Fotos, Pi + Laptop-Kontext | Ja |
| Keine Comic-Flächen im Hero/About/Projekt-Block | Ja |
| Echte App-Screenshots (PNG) im Repo | **Nein** — siehe `assets/screenshots/STATUS-FEHLT.md` |
| Einheitliche Bildsprache über **alle** Unterseiten | Teilweise — viele Snippets nutzen weiterhin SVG-Illustrationen unter `assets/images/*.svg`. |

**Ergebnis:** **Nicht abgeschlossen – weitere Korrektur erforderlich** (mindestens: PNG-Screenshots aus der App einspielen; optional: weitere Projektseiten mit Fotos statt generischer SVGs).
