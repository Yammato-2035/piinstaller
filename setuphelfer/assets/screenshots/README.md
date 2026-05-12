# Screenshots (Theme-Auslieferung)

Diese PNGs werden von der WordPress-Website unter  
`…/wp-content/themes/<theme>/assets/screenshots/` ausgeliefert.

## Darstellung auf der Website

Snippets nutzen **`{{TAURI_SHOT:…}}`** (siehe `SCREENSHOTS.md` im Theme).  
**Fehlende oder leere Dateien:** einheitliche Box mit dem Titel *„Screenshot wird automatisch aus Tauri erzeugt“* und dem erwarteten **Dateinamen** — dazu der Hinweis *„Screenshots werden aus der laufenden App generiert (kein Mockup)“* (`{{TAURI_SHOT_POLICY}}`).

## Synchronisation aus dem PI-Installer-Repo

Quelle (eine der beiden, inhaltlich abgleichen):

- `docs/screenshots/*.png`
- `frontend/public/docs/screenshots/*.png`

Nach Aktualisierung der App-Oberfläche die Dateien hier erneut kopieren.

## Startseite (Hero + Screenshot-Sektion)

1. `screenshot-dashboard.png` — Dashboard (auch Hero)  
2. `screenshot-monitoring.png` — Diagnose (Monitoring)  
3. `screenshot-wizard.png` — Projekte & Setup (Assistent)

```bash
# Beispiel (Pfad zum Repo anpassen)
cp /pfad/zum/piinstaller/docs/screenshots/*.png ./assets/screenshots/
```
