# Rescue Startmenü UI-Blocker — Root Cause (2026-06-24)

**Version:** 1.9.16.2 (Symptom) → Fix in 1.9.16.3  
**Hardware:** MSI GE63 (1366×768 typisch)  
**Payload:** Dev-Rettungsstick SETUPHELFER + SETUP_LOGS

## Symptom

| Element | Erwartet | Ist | Ursache | Fix |
|---|---|---|---|---|
| Logo | groß links/markenkonform | minilogo oben | `RescueApp.tsx` nutzte `RescueStartCenter` + `RescueBrandingHeader` (zentriert, 120px) statt `RescueDashboard` mit `rescue-brand-row` (320px) | `RescueShellLayout` + `RescueDashboard`, `showToolbarBrand={false}` auf Menü |
| Buttons | begrenzte Kartenbreite | volle Breite | `.rescue-tile-grid { width: 100% }` + 1 Spalte bei `<800px`; fehlendes `max-width` auf Tiles | `max-width: min(1100px)` Grid, Tiles `max-width: 520px` |
| Sprache | sichtbar | unsichtbar | Keine Toolbar — `RescueShellLayout` nicht verdrahtet | `RescueLanguageSelect` in sticky Toolbar |
| Shutdown | sichtbar | unsichtbar | Keine Toolbar | `RescuePowerButton` in Toolbar |
| Bedienbarkeit | klickbar | blockiert | `RescueApp` übergab `onSelectItem`, `RescueStartCenter` erwartet `onSelectTile` → Handler nie aufgerufen | `onSelectTile={(id) => setView(id)}` |

## Technische Details

1. **Commit `b322c96`** reduzierte `RescueApp.tsx` auf Minimal-Splash + `RescueStartCenter` ohne Shell.
2. **CSS** `rescue-shell.css` war vorhanden, aber Layout-Komponenten nicht eingebunden.
3. **MSI 768px Höhe:** `@media (max-height: 768px)` verkleinerte `.rescue-hero-logo` global auf 140px — Override nur für `.rescue-brand-row` auf 220px.
4. **Overlay:** Kein pointer-events-Blocker; Klicks scheiterten an fehlendem Handler, nicht an z-index.

## Fix-Dateien

- `frontend/src/rescue/RescueApp.tsx` — Shell + Dashboard + Panel-Routing
- `frontend/src/rescue/rescue-shell.css` — Tile max-width, sticky Toolbar, Scroll
- `frontend/src/rescue/rescueSafeMode.ts` — Safe-Walk (`?safe_walk=1`, `RESCUE_UI_SAFE_WALK=1`)

## Nachweis

- Statische Contract-Tests: `backend/tests/test_rescue_ui_screenshot_v1.py`
- Live: Screenshot `start-menu` auf MSI (Operator Phase 10)

## Status

| Prüfung | Status |
|---|---|
| Root Cause dokumentiert | GRÜN |
| Code-Fix | GRÜN (Workspace) |
| MSI Live bestätigt | GELB (Operator ausstehend) |
