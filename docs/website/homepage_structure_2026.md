# Startseite Setuphelfer — Struktur (Stand 2026-03-20, v3)

Quelle: `website/setuphelfer-theme/snippets/index.html`, Wrapper `home-page` in `front-page.php`.

## Reihenfolge (verbindlich)

1. **Hero** — `home-hero` / `hero--home`: Textspalte + **Produkt-Szene** (`hero-laptop`): Laptop-Rahmen (CSS), darin **echter** Dashboard-Screenshot per `<object data="assets/screenshots/screenshot-dashboard.png">` mit **markiertem Slot** als Fallback, falls die PNG fehlt. Kein Illustrations-Hintergrund, kein kleines Overlay-Thumbnail.
2. **So funktioniert SetupHelfer** — `#ablauf`: **4 nummerierte Schritte** (`ol.home-steps`).
3. **Screenshots** — `#screenshots` / `section--product`: genau **drei** gleich grosse Haupt-Screenshots (`product-shots-trio`), nebeneinander ab Desktop, untereinander mobil: **Dashboard** (`screenshot-dashboard.png`), **Diagnose** (`screenshot-monitoring.png`), **Projekte & Setup** (`screenshot-wizard.png`). App-Fenster-Rahmen `shot-frame--product`, Fallback-Text „Screenshot fehlt – muss aus Tauri erzeugt werden“ pro `<object>`.
4. **Problem & Nutzen** — `#nutzen` / `section--band`.
5. **Funktionsübersicht** — `#funktionen`.
6. **Zielgruppen** — `#zielgruppen` / `section--band`.
7. **Tutorials & Hilfe** — `#hilfe`.
8. **Projekte** — `#projekte` / `section--band`.
9. **Community** — `#community`.
10. **Download** — `#download` / `section--download` (ohne Hinweistext zu Live-Systemstatus).

**11. Footer** — `footer.php` (nach dem Snippet).

## Live-Systemstatus

- Kein Block `#setuphelfer-live-status` im Snippet.
- Kein Erwähnungstext auf der Startseite.
- Skript `live-status.js` wird auf der **Front Page** per `setuphelfer_dequeue_front_page_scripts` nicht geladen (andere Seiten unverändert).

## Abstand zwischen Sektionen

- Global: `.section + .section` hatte zu wenig `padding-top` (10px).
- Startseite: `.home-page .section + .section { padding-top: 48px }` setzt ausreichend Abstand.

## Assets

Referenzierte Pfade zeigen auf bestehende Theme-Dateien.
