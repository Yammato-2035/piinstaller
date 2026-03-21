# Screenshots (Tauri / PI-Installer)

## System

- PNGs liegen unter `assets/screenshots/`.
- In Snippets **keine** direkten `<img src="assets/screenshots/...">` mehr für App-Screens: stattdessen Platzhalter **`{{TAURI_SHOT:dateiname.png|Alt-Text|Kontext}}`**.
- **Kontext:** `hero` (Hero-Laptop), `product` (Startseite, Fenster-Rahmen), `inner` (Raster `.shot` auf Download, Doku, Tutorials).
- **`{{TAURI_SHOT_POLICY}}`** — ein Absatz mit dem Hinweis, dass Bilder aus der laufenden App stammen (kein Mockup).

Die Auswertung erfolgt in PHP (`inc/setuphelfer-screenshots.php`): existiert die Datei und ist sie groß genug, wird ein echtes `<img>` ausgegeben; sonst die **einheitliche Platzhalter-Box** mit Titel *„Screenshot wird automatisch aus Tauri erzeugt“* und dem **Dateinamen**.

## Pflege

Siehe `assets/screenshots/README.md` zum Kopieren aus dem PI-Installer-Repo.
