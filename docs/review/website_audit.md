# Website Audit – Setuphelfer

Datum: 2026-03-20  
Modus: Strenger Frontend-Audit (kein Redesign, keine Schönfärbung)

## 1) Seitenbestand (aktuell im Theme)

### Kernseiten
- `index.html` (Startseite)
- `projects.html`
- `tutorials.html`
- `troubleshooting.html`
- `community.html`
- `download.html`
- `documentation.html`
- `guided-start.html`
- `sicherheit.html`
- `changelog.html`
- `kontakt.html`
- `about.html`
- `cookie-policy.html`

### Detailseiten (inhaltlich vorhanden)
- Projektdetails: `project-*.html`
- Tutorialdetails: `tutorial-*.html`
- Fehlerhilfe-Details: `issue-*.html`
- Doku-Details: `doc-*.html`

## 2) Startseite – vorhandene Sektionen

1. Hero
2. Warum SetupHelfer
3. Screenshots „So sieht SetupHelfer im Build aus“
4. Live-Status
5. Lernpfade
6. Funktionsübersicht
7. Visuelle Teaser-Bausteine
8. Beliebte Projekte
9. Tutorials/Community-Teaser
10. Download-Hinweis
11. Sicherheit

## 3) Audit-Liste (Bereich, Problem, Ursache, Schweregrad, Reparatur)

| Bereich | Problem | Ursache | Schweregrad | Konkrete Reparaturempfehlung |
|---|---|---|---|---|
| Startseite | Hohe Sektionstiefe, wirkt überladen | Viele Teaser in kurzer Folge, teils inhaltliche Wiederholung | Hoch | Sektionen auf 7-8 Kernblöcke reduzieren, „Visuelle Teaser-Bausteine“ in Funktionsübersicht integrieren |
| Startseite | Redundanz Tutorials/Community/Download | CTA-Cluster mehrfach mit ähnlicher Aussage | Mittel | CTA-Architektur konsolidieren: ein zentraler CTA-Block statt verteilter Teilblöcke |
| Hero | Drittelkarte „Asset-Slot“ sichtbar wie Platzhalter | `asset-slot` als sichtbares UI im produktiven Hero | Hoch | Slot nur im Dev-/Audit-Modus anzeigen oder durch finale Visual ersetzen |
| Screenshots (global) | Risiko nicht ladender Bilder im Live-Betrieb | Nutzung absoluter Pfade `/docs/screenshots/...` | Kritisch | Entweder `/docs` wirklich ins Webroot deployen oder auf Theme-/Upload-Pfade umstellen |
| Download | Download-Buttons ohne Ziel (`href="#"`) | Kein hinterlegter Paket-/Release-Link | Kritisch | echte Download-URLs/Release-Endpoints hinterlegen, sonst deaktivierter CTA mit klarer Statusmeldung |
| Download | FAQ technisch nur textuell, kein Fehlerpfad zur API | statisches FAQ ohne Health-/Status-Verknüpfung | Mittel | FAQ um „Backend erreichbar / nicht erreichbar“-Hinweis mit Link auf Live-Status ergänzen |
| Projekte/Tutorials | Filter sind visuelle Chips, keine echte Filterlogik | reine Anchor-Navigation | Mittel | Falls Filter-Anspruch bleibt: echtes clientseitiges Filtern oder klar als Sprungmarken labeln |
| Asset-System | Mischbetrieb aus `assets/icons`, `assets/ui`, `assets/images` | historisch gewachsen, nicht final konsolidiert | Mittel | verbindliche Asset-Rollen definieren und alte Bildpfade schrittweise auf Zielset migrieren |
| Dokumentation | Such-/Indexlogik nur vorbereitet, nicht funktional | `doc-index` ist statische Linkliste | Mittel | echte Such-/Index-Komponente (WP-Suche scoped auf `doc_entry`) ergänzen |
| Doku/Technikblöcke | CLI-/Config-Abschnitte ohne Copy-UX | reine `pre`-Blöcke | Niedrig | Copy-Button/Code-Label ergänzen, visuelle Konsistenz für technische Inhalte erhöhen |
| Content-Pflege | Sehr viele Detailsnippets mit heterogenem Reifegrad | parallele Content-Linien (alt/neu) | Mittel | „Active Content Set“ festlegen und veraltete Snippets archivieren |
| Release-Prozess | Keine harte Build-/Asset-Prüfung dokumentiert | fehlender automatischer Link-/Asset-Check im Deploy | Hoch | Pre-Deploy Checkscript für Assetpfade + Screenshot-Verfügbarkeit verbindlich machen |

## 4) Unfertig-/Unübersichtlichkeitsbefunde

- Die Website ist deutlich weiter als ein Rohbau, aber noch nicht durchgängig „release-clean“.
- Kritische Unfertigkeit liegt weniger im CSS als in **Asset- und CTA-Verbindlichkeit**:
  - Screenshots technisch riskant eingebunden (absoluter Pfad).
  - Download-CTAs ohne Ziel.
  - sichtbarer Hero-Asset-Slot als Platzhalter.

## 5) Hero-Komponente (Ist-Zustand)

- Eingebunden: `assets/hero/hero-setup-scene.svg`
- Ergänzt um Overlay und Screenshot-Frames.
- Zusätzlich sichtbar: `assets/visual-system/hero-scene-overlay.svg` als Slot-Kachel.

Bewertung:
- Positiv: Produktbezug ist vorhanden.
- Negativ: sichtbarer Slot wirkt im Live-Kontext unfertig.

## 6) Komponenten mit Platzhaltercharakter

- Hero: `asset-slot` mit Label „Asset-Slot“
- Dokumentation: Bild-Slot für weitere Doku-Grafiken
- Download-Buttons: `href="#"` (funktionaler Platzhalter, nicht nur visuell)

## 7) Strukturelle Redundanz/Überladung

- Startseite hat mehrere CTA-nahe Teaserblöcke mit ähnlicher Aussage.
- Der „Visuelle Teaser“-Block steht separat, obwohl er funktional in die Feature-Sektion gehört.
- Ohne Kürzung leidet Scanbarkeit auf Mobile trotz funktionierender Responsiveness.
