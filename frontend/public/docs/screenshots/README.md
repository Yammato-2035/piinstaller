# Dokumentations-Screenshots (`doc-*.png`)

Die Handbuch-Seite verweist auf Dateien unter `/docs/screenshots/` (Vite `public/`).

## Neu erzeugen

1. Frontend starten, z. B. `npm run dev` (Port 3001) oder Tauri/Vite (5173).
2. Basis-URL setzen, falls nicht Standard 3001:

   ```bash
   export DOCS_SCREENSHOT_BASE=http://127.0.0.1:5173
   ```

3. Aus `frontend/`:

   ```bash
   npm run screenshots:docs
   ```

Voraussetzung: `npx playwright install chromium` (einmalig).

## Dateinamen

| Datei | Inhalt |
|-------|--------|
| `doc-dashboard.png` | `?page=dashboard` |
| `doc-wizard.png` | `?page=wizard` |
| … | siehe `scripts/capture-documentation-screenshots.mjs` |
| `doc-settings-general.png` | Einstellungen, Tab Allgemein |
| `doc-settings-cloud.png` | Einstellungen, Tab Cloud-Backup |

Veraltete Namen `screenshot-*.png` werden beim Lauf des Skripts gelöscht.
