# Phase 4 – Screenshots aus aktuellem Build (setuphelfer.de)

Datum: 2026-03-17
Prinzip: Keine Fake-Mockups. Echte Build-Screenshots haben Vorrang.

## 1) Ergebnis der Pruefung

- Im Repository sind aktuell **keine echten Build-Screenshots (PNG/JPG/WEBP)** hinterlegt.
- Vorhanden ist nur:
  - `frontend/public/docs/screenshots/README.md`
- Bisher in Website/Doku gezeigte "Screenshots" waren SVG-Platzhalter aus dem Theme-Assetbestand.

## 2) Technische Moeglichkeit zur Screenshot-Erstellung

Im Projekt existiert ein funktionierender Screenshot-Workflow fuer die Tauri-Desktop-App:

- Komponente: `frontend/src/components/ScreenshotDocCard.tsx`
- Nur in Tauri verfuegbar (nicht im Browser-Stub):
  - `frontend/src/lib/tauri-screenshots-stub.ts`
- Ablauf:
  - Einstellungen -> Screenshots
  - Button "Screenshots erstellen"
  - Ausgabe laut UI:
    - `Dokumente/PI-Installer/docs/screenshots/`
- Erzeugte Dateinamen:
  - `screenshot-dashboard.png`, `screenshot-wizard.png`, ...

Damit ist die Erstellung **halbautomatisiert** vorbereitet, aber die Dateien sind noch nicht ins Repo uebernommen.

## 3) Umsetzungen in der Website

### 3.1 Download-Bereich bereinigt

Datei: `website/setuphelfer-theme/snippets/download.html`

- Screenshot-Block mit pseudo-Screens wurde entfernt.
- Ersetzt durch transparenten Statusblock:
  - Aktuell keine echten Build-Screenshots im Repo
  - Workflow zur Erstellung klar benannt
  - Zielablage fuer spaetere Einbindung dokumentiert

### 3.2 Startseite ergaenzt

Datei: `website/setuphelfer-theme/snippets/index.html`

- Produktvorschau-Hinweis eingefuegt:
  - Screenshot-Erstellung vorhanden
  - Derzeit keine hinterlegten Build-Screens
  - Bewusst keine Fake-Live-Screens

## 4) Warum so umgesetzt

- Vorgabe eingehalten: Keine Fantasie-Screenshots vortaeuschen.
- Produktnaehe wird sauber vorbereitet statt simuliert.
- Nachlieferung ist technisch klar und ohne Umbau moeglich.

## 5) Nächster Trigger fuer echte Einbindung

Sobald die erzeugten PNGs in

- `frontend/public/docs/screenshots/`

hinterlegt sind, koennen sie direkt in Hero/Produktbereich/Download eingebunden werden.

## 6) Selbstpruefung Phase 4

- Echte Build-Screens gesucht: Ja.
- Erzeugungsweg im Projekt geprueft: Ja.
- Kein Fake-Mockup verwendet: Ja.
- Fehlender Stand transparent dokumentiert: Ja.
- Website-Bereiche entsprechend angepasst: Ja.

