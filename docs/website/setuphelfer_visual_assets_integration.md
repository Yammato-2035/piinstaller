# Setuphelfer – Visuelle Assets (Integration)

Stand: 2026-03-20  
Grundlage: `docs/review/asset_manifest.md` + Ergänzungen in diesem Dokument.

## Leitlinien

- Keine Platzhalter-Slots mit „Asset-Slot“-Label auf der Live-Startseite.
- Produkt-Screenshots aus `assets/screenshots/` (Tauri-Build) haben Vorrang vor abstrakten Grafiken.
- Icon-Familie **Kachel 256×256** (Beginner/Advanced/Download/Expert): gleiche Gradient-Hintergründe und `fill="#4F7FAE"`-Karten.
- Zusätzliche **Fenster-Chrome**-SVG nur für technische Komposition, Druck oder externe Präsentationen; Standard-Webseite nutzt HTML/CSS `.shot-frame`.

## Dateien und Verwendung

| Datei | Pfad | Komponente / Verwendung |
|-------|------|-------------------------|
| Hero-Szene | `assets/hero/hero-setup-scene.svg` | `snippets/index.html` – Hero-Basis; technische GPIO-Leiste am Board, A11y-`title`/`desc` |
| UI-Raster (optional) | `assets/visual-system/hero-scene-overlay.svg` | Nicht mehr als Platzhalter im Hero; optional für Layout-Prototypen / `asset-slots.json` |
| Screenshot-Chrome | `assets/visual-system/screenshot-container-desktop.svg` | Neutrales Desktop-Fenster-Motiv; optional für Marketing-PDF, Keynote, **nicht** zwingend im Theme eingebunden |
| Icon Experte | `assets/icons/icon-expert.svg` | `snippets/index.html` – Lernpfad „Experte“ |
| Icon Download | `assets/icons/icon-download.svg` | `asset-slots.json` (Feature-Visual „Download“); gleiche Stilsprache wie Beginner/Advanced |
| App-Screenshots | `assets/screenshots/*.png` | Hero-Drittelreihe, Dokumentation, Tutorials, Download – siehe Manifest |

## Hero-Zeile (drei App-Fenster)

`index.html`: drei `shot-frame`-Kacheln mit echten PNGs:

1. `screenshot-wizard.png`
2. `screenshot-settings.png`
3. `screenshot-documentation.png`

## Dokumentations-Sektion

`documentation.html`: drei `.shot`-Kacheln mit `screenshot-documentation.png`, `screenshot-dashboard.png`, `screenshot-presets.png` (kein Platzhalter-Slot).

## JSON-Register

`assets/visual-system/asset-slots.json`:
- `hero.app_screens` inkl. `screenshot-documentation.png`
- `screenshot_chrome.desktop_window` → `screenshot-container-desktop.svg`

## Synchronisation

Screenshots nach App-Build aktualisieren: `theme/assets/screenshots/README.md`.
