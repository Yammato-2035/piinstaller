# Partitionsmanager – Mockup Gap-Analyse (Phase 2.3)

**Datum:** 2026-06-10  
**Referenz:** Freigegebenes Mockup (Setuphelfer Partitionshelfer)  
**Basis:** Runtime Phase 2.2 (`1.7.12.2`)

## Vergleichstabelle

| Bereich | Mockup | Aktuell (2.2) | Abweichung | Phase 2.3 Maßnahme |
|---------|--------|---------------|------------|-------------------|
| Seitenlayout | 3-Spalten: Datenträger \| Partitionen \| Sicherheit | 2-Spalten, Restore/Dev rechts unten | Keine echte 3-Spalten-Wirkung | Grid 12-Spalten (4+5+3) |
| Kartenlayout | Hohe Karten, große Icons, klare Rollenfarben | Horizontales Scroll, kleinere Karten | Zu technisch, Scroll | Grid ohne Scroll, höhere Karten |
| Farbwirkung | System=orange, Backup=grün, Rescue=blau | Teal/Sky-Mix | Rollenfarben uneinheitlich | `partitionMockupTheme.ts` |
| Schriftgrößen | Große Namen, kleine UUID | Mittelgroß überall | Hierarchie flach | Typo-Skala in Komponenten |
| Partitionendarstellung | Dominanter Balken, Tabelle sekundär | Balken + Tabelle gleichwertig | Grafik nicht Hauptelement | Balken h-28–32, Hover-Detail |
| Sicherheitsbereich | Großes SICHER-Badge, Status-Karten | Badge + Liste | Liste zu technisch | 2×2 Mini-Karten |
| Hardstops | Große rote Warnbox | RiskWarningCard klein | Zu dezent | Hero-Warnblock |
| Restore-Vorschau | Volle Breite, große Aktionskarte | Nur nach Klick sichtbar | Zu versteckt | Immer sichtbar wenn Disk gewählt |
| Buttons | Großer blauer CTA in Restore-Bereich | CTA im Sicherheitspanel | Falsche Position | CTA in Restore-Panel |
| Dev-Strip | Status-Pills unten | Textliste rechts | Stil/Position | Pills, volle Breite unten |
| Informationshierarchie | Einsteiger zuerst | Gut, aber UUID früh | Experten-Details zu früh | Tabelle UUID nur advanced |

## Geschlossen in Phase 2.3

- Zentrales Farbkonzept (grün/gelb/rot/blau)
- 3-Spalten-Layout ab `xl`
- Datenträgerkarten ohne horizontalen Scroll
- Dominante Partitionsgrafik
- Sicherheits-Mini-Karten
- Hardstop-Hero-Block
- Restore-Panel mit Aktualisieren-Button
- Dev-Strip als Pills

## Verbleibende Mockup-Unterschiede (bewusst)

- Globale Setuphelfer-Sidebar/Top-Bar (App-Chrome) – nicht Partitions-Scope
- Entwicklungsmodus-Toggle im Header – App-Level
- Systemstatus-Leiste unten (Kernel/IP) – globales Footer-Widget
- Exakte Schriftart/Pixel-Maße des Design-Tools

## Unverändert (Pflicht)

- Keine API-/Backend-Änderung
- `write_allowed=false` / `restore_execution_allowed=false`
- Keine Schreib-/Execute-Aktionen
