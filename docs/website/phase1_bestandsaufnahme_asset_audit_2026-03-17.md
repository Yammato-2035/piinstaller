# Phase 1 – Bestandsaufnahme und Asset-Audit (setuphelfer.de)

Datum: 2026-03-17
Scope: Nur Analyse, keine gestalterische Neuinterpretation.

## 1) Aktueller technischer Stand (Website)

- Theme-Basis vorhanden und funktionsfaehig: `website/setuphelfer-theme/`
- Startseite wird ueber Snippet-Mechanik gerendert:
  - `front-page.php` -> `snippets/index.html`
- Inhalte sind als Snippets organisiert (`snippets/*.html`) und ueber Mapping/Renderer verbunden.
- CPTs vorhanden:
  - `projekt`, `tutorial`, `fehlerhilfe`, `doc_entry`
- Die Seite ist inhaltlich bereits weit ausgebaut, aber asset-seitig und produktseitig noch nicht durchgaengig konsolidiert.

## 2) Asset-Inventar (Ist)

### 2.1 Hero/Illustrationen/Icons

- Neue Sets vorhanden:
  - `assets/hero/*` (4 SVG)
  - `assets/illustrations/*` (6 SVG)
  - `assets/icons/*` (projekt-/tutorial-spezifische SVG)
  - `assets/ui/*` (UI-SVG)
- Gleichzeitig sind alte Sets weiterhin im Einsatz:
  - `assets/images/*` (u. a. fruehere Hero-/Bereichsgrafiken, pseudo-screenshot SVGs)
  - `assets/icons/icon-*` (gemischtes altes Icon-Set)
- Ergebnis: Doppeltes Asset-System (neu + alt), teilweise gemischte Nutzung in Snippets.

### 2.2 Logo/Branding

- Aktuell vorhanden:
  - `assets/images/logo-app.svg`
  - `assets/images/logo-symbol.svg`
- Beide Dateien sind inhaltlich identisch (kein getrenntes Rollenmodell fuer Wortmarke/Signet/App-Icon).
- Kein dediziertes Favicon-Asset im Theme gefunden.
- Kein dokumentiertes, verbindliches Mini-Branding-System mit klarer Rollenverteilung aktiv im Theme.

### 2.3 Screenshots (echter Build)

- Im Theme werden "Screenshots" derzeit als SVG-Platzhalter aus `assets/images/` verwendet (z. B. `screenshot-dashboard.svg`).
- In der App-Ablage existiert nur:
  - `frontend/public/docs/screenshots/README.md`
- Es wurden keine echten PNG/JPG/WEBP-Build-Screenshots im Repo gefunden.
- Ergebnis: Derzeit kein belegbarer Bestand echter aktueller Build-Screenshots.

## 3) Inhaltslage Tutorials (Ist)

- Tutorial-Snippets vorhanden in zwei Gruppen:
  - Neuere, integrierte Tutorials (z. B. `tutorial-pi-os-install.html`, `tutorial-wlan-setup.html`, `tutorial-ssh-enable.html`, ...)
  - Aeltere Tutorials weiterhin vorhanden (z. B. `tutorial-first-setup.html`, `tutorial-linux-basics.html`, `tutorial-backup-basics.html`, `tutorial-network-basics.html`)
- Ergebnis: Potenzielle Dubletten bzw. parallele Tutorial-Linien im Bestand, Konsolidierung erforderlich.

## 4) Live-Daten/Backend-Anbindung (Ist)

- Im Website-Code wurde keine aktive Fetch-/Polling-Anbindung an Backend-Endpunkte gefunden.
- Backend ist sehr umfangreich vorhanden in `backend/app.py` mit relevanten Endpunkten, u. a.:
  - `/health`
  - `/api/status`
  - `/api/system-info`
  - `/api/system/resources`
  - `/api/system/network`
  - weitere status-/installationsnahe Endpunkte
- Ergebnis: Technische Basis fuer Live-Daten ist vorhanden, aber auf der Website derzeit nicht eingebunden.

## 5) Abgleich mit den genannten Defiziten

1. Echte Hero-Section mit Produktwirkung:
   - Teilweise vorhanden (Headline + CTA + Hero-Grafik), aber ohne echte App-Screens und ohne klaren Live-/Produktbeweis.
2. Konsistente produktnahe Hero-Grafiken:
   - Neue Hero-SVGs vorhanden, Qualitaet gemischt durch parallele alte Assets.
3. Farbnaehe zum PI-Installer:
   - Dokumentiert, aber in der Umsetzung noch nicht klar app-nah vereinheitlicht.
4. Verbindliches Logo-System:
   - Nicht abgeschlossen (aktuell nur zwei identische Logo-Dateien, kein Favicon-Set).
5. Icon-Qualitaet:
   - Teilweise gut, aber gemischte alte/neue Icon-Systeme.
6. Aktuelle Build-Screenshots:
   - Nicht vorhanden, nur Platzhalter-SVGs.
7. Vollstaendige Tutorial-Einbindung:
   - Bestand breit, aber mit Konsolidierungsbedarf (alt/neu parallel).
8. Live-Daten auf Website:
   - Noch nicht umgesetzt.

## 6) Risiken fuer die naechsten Phasen

- Asset-Mix (alt/neu) kann zu inkonsistenter Wahrnehmung fuehren.
- Fehlende echte Screenshots verhindern glaubwuerdige Produktnaehe.
- Tutorial-Dubletten koennen Informationsarchitektur verwaessern.
- Ohne Healthcheck/Fallback-Konzept fuer Live-Daten drohen fragile Frontend-Zustaende.

## 7) Phase-1-Ergebnis (freigegeben fuer Phase 2)

- Bestandsaufnahme abgeschlossen.
- Defizite sind technisch verifiziert und auf Dateien/Verzeichnisse rueckfuehrbar.
- Naechster Schritt gemaess Reihenfolge:
  - Phase 2: Branding-System festziehen (auf Basis vorhandener Logo-/Asset-Referenzen, ohne freie Neuerfindung).

