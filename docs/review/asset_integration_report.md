# Asset-Integration — Bericht

## Struktur `assets/images/`

Unterordner: `hero/`, `setup/`, `about/`, `community/`, `documentation/`, `download/`, `projects/`, Symlink `screenshots` → `../screenshots`.

## Eingebundene Bilder (Auswahl)

| Pfad | Verwendung |
|------|------------|
| `images/hero/hero-raspberry-pi-desk.jpg` | Start Hero |
| `images/hero/hero-linux-laptop.jpg` | Start Hero |
| `images/hero/hero-product-composition.png` | Start Hero, Projekte-Masthead |
| `images/hero/linux-tux-official.png` | Linux-Sichtbarkeit (Tux) |
| `images/about/*.jpg` | Über |
| `images/community/community-hero-real-setup.jpg` | Community-Masthead |
| `images/documentation/documentation-hero-workspace.jpg` | Doku + Tutorials-Masthead |
| `images/download/download-hero-product.jpg` | Download-Masthead |
| `images/projects/project-*.jpg` | Projektübersicht + Medienserver |
| `screenshots/screenshot-dashboard.png` | TAURI / Komposition |
| `screenshots/screenshot-diagnose.png` | Start „Diagnose“ |
| `screenshots/screenshot-projects.png` | Start „Projekte & Setup“ |

## Seiten angepasst

Startseite, Download, Tutorials, Community, Dokumentation, Projekte, Über, Projekt Medienserver.

## Technik

- Pfade `src="assets/..."` werden von `setuphelfer_render_snippet` auf Theme-URL gemappt.
- Keine 404 für oben gelistete Dateien (lokal geprüft mit `test -f`).
