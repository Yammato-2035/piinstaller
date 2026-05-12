# Priorisierte To-do-Liste – Sanierung Setuphelfer

Datum: 2026-03-20  
Prinzip: erst Reparaturbasis, dann Erweiterung

## Priorität A (kritisch, blockiert Release)

1. **Screenshot-Auslieferung verbindlich fixen** — **erledigt (2026-03-20)**
   - Screenshots unter `setuphelfer-theme/assets/screenshots/`, Snippets nutzen `assets/screenshots/...`; Legacy `/docs/screenshots/` wird im PHP-Renderer ersetzt.

2. **Download-CTAs funktionsfähig machen** — **erledigt (2026-03-20)**
   - Platzhalter `{{RELEASES_LATEST}}` → `https://github.com/VolkerGlienke/piinstaller/releases/latest` (filterbar via `setuphelfer_github_repo_url`).

3. **Sichtbare Platzhalter aus Hero entfernen**
   - `asset-slot` auf der Startseite aus Live-Ausgabe entfernen oder final ersetzen.
   - Erfolgskriterium: kein sichtbares „Asset-Slot“-Label mehr im produktiven Hero.

4. **Pre-Deploy Link-/Asset-Check einführen**
   - Prüfschritt für Bild- und Screenshot-Referenzen in die Release-Routine aufnehmen.
   - Erfolgskriterium: Build schlägt fehl bei defekten Asset-Links.

## Priorität B (wichtig, nach A)

1. **Startseite strukturell entschlacken**
   - redundante Teaserblöcke zusammenführen (Tutorials/Community/Download).
   - Erfolgskriterium: klare 7-8 Hauptsektionen mit eindeutiger Nutzerführung.

2. **Filterlogik klarstellen**
   - visuelle Filterchips als echte Filter implementieren oder als Sprunglinks explizit benennen.
   - Erfolgskriterium: Nutzererwartung entspricht tatsächlicher Funktion.

3. **Asset-Strategie konsolidieren**
   - Regelwerk für `icons`, `ui`, `images`, `illustrations`, `hero` festziehen.
   - Erfolgskriterium: neue Assets folgen konsistenter Ablagestruktur.

4. **Dokumentationsbereich funktional ausbauen**
   - statischen Index um echte Suchfunktion (WP-scope auf Doku) ergänzen.
   - Erfolgskriterium: dokumentierte Inhalte sind zielgerichtet auffindbar.

## Priorität C (Feinschliff)

1. **Codeblock-UX verbessern**
   - Copy-Buttons/Labels für `code-example` ergänzen.

2. **Mikrotypografie im Longform-Content vereinheitlichen**
   - Listen, Abstände, Unterüberschriften in Detailseiten angleichen.

3. **Content-Bereinigung vorbereiten**
   - veraltete oder doppelte Snippets in ein Archiv überführen.

---

## Reihenfolge für den nächsten Arbeitszyklus

1. A1 → A2 → A3 → A4  
2. Danach struktureller Umbau gemäß `startseite_restrukturierung.md`  
3. Erst dann visuelle/UX-Feinschliffe (Priorität C)
