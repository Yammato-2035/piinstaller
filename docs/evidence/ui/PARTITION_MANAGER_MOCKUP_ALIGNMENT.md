# Partitionsmanager – Mockup Alignment Evidence (Phase 2.3)

**Datum:** 2026-06-10  
**Version:** `1.7.12.3`  
**Scope:** Nur UI/UX – keine Backend-, API- oder Safety-Änderungen

## Vorher (Phase 2.2)

- 2-Spalten-Layout mit Restore/Dev-Strip in der rechten Spalte
- Horizontales Scrollen bei Datenträgerkarten
- Sicherheitsstatus als kompakte Liste
- Hardstops als kleine RiskWarningCards
- Restore-CTA im Sicherheitspanel, Panel erst nach Klick sichtbar
- Dev-Strip als Textliste rechts

## Nachher (Phase 2.3)

- **3-Spalten-Grid** (`xl:grid-cols-12`: 4+5+3) – Datenträger | Partitionen | Sicherheit
- **Restore-Handoff** volle Breite unterhalb der Spalten
- **Dev-Strip** volle Breite unten mit Status-Pills
- **Datenträgerkarten:** höher, große Icons, Rollenfarben (orange/grün/blau/grau), Glow bei Auswahl
- **Partitionsgrafik:** dominanter Balken (h-28–36), Hover-Detail, Tabelle sekundär
- **Sicherheit:** großes SICHER/PRÜFEN/BLOCKIERT-Badge, 2×2 Mini-Karten
- **Hardstops:** rote Hero-Warnbox mit großem Icon und Code
- **Restore:** große Aktionskarte, `restore_execution_allowed=false`, blauer „Aktualisieren“-Button
- **Zentrales Theme:** `frontend/src/lib/partition/partitionMockupTheme.ts`

## Geänderte Komponenten

| Datei | Änderung |
|-------|----------|
| `PartitionManager.tsx` | 3-Spalten-Layout, Restore unten, Dev-Strip unten |
| `PartitionOverviewCards.tsx` | Höhere Karten, Rollenfarben, kein Scroll |
| `PartitionGraphicLayout.tsx` | Dominante Grafik, Hover-Panel |
| `PartitionSafetyStatusPanel.tsx` | Mini-Karten, größeres Badge |
| `PartitionHardstopPanel.tsx` | Hero-Warnblock |
| `PartitionRestorePreviewPanel.tsx` | Aktionskarte + Refresh-CTA |
| `PartitionPageDevStrip.tsx` | Status-Pills |
| `PartitionSectionHeader.tsx` | Typografie |
| `partitionMockupTheme.ts` | Neu – zentrale Farben |

## Geschlossene Mockup-Abweichungen

- 3-Spalten-Wirkung
- Rollenfarben System/Backup/Rescue
- Grafik vor Tabelle
- Dominanter Sicherheitsbereich
- Hardstop als Warnmeldung
- Restore-Vorschau als eigene Sektion
- Dev-Strip als Pills

## Verbleibende Unterschiede

- App-Chrome (Sidebar, globaler Footer) außerhalb Partitions-Scope
- Exakte Pixel-Maße des Design-Mockups
- Entwicklungsmodus-Toggle im App-Header

## Runtime unverändert

- Keine neuen API-Aufrufe
- Kein Queue Apply
- Kein Restore Execute
- `write_allowed=false` sichtbar
- Safety-Logik unverändert

## Tests

```bash
cd frontend && npm run test -- --run src/components/PartitionManagerPhase2.test.ts
```

Pflicht-Assertions: Karten, Hardstop, Restore-Handoff, `write_allowed=false`, 3-Spalten-Grid, kein horizontaler Karten-Scroll.

## Screenshots

Manuell nach Build unter Port 3001/3002 auf `/partitions` (oder entsprechende Route) – statische Evidence via Komponenten-Tests und Build-Artefakt.
