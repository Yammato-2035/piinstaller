# Partitionshelfer Workbench – Screenshot Review

**Datum:** 2026-06-10  
**Version:** `1.7.13.2` (Workspace, uncommitted)

## Vorher

`docs/evidence/ui/PARTITIONSHELFER_WORKBENCH_BEFORE.png`  
(3-Spalten-Layout, Karten oben/links, Tool-Shell)

## Nachher

`docs/evidence/ui/PARTITIONSHELFER_WORKBENCH_AFTER.png`  
(Workbench: linke Sidebar, Arbeitsbereich, Cockpit, Hardstop Center, Expertenmodus)

## Unterschiede

| Aspekt | Vorher | Nachher |
|--------|--------|---------|
| Shell | `PartitionToolShell` | `PartitionWorkbenchShell` mit Werkzeug-Header |
| Datenträger | Karten-Grid (xl:col-span-4) | Linke Sidebar, Rollenfarben |
| Layout | 12-Spalten 4/5/3 | Sidebar + Arbeitsbereich |
| Grafik | Standardhöhe | Größer (h-52) + Legende EFI/Root/… |
| Sicherheit | Mini-Karten-Grid | Cockpit-Zeilen (SMART, Rolle, Hardstops, …) |
| Hardstops | Panel unter Grafik | **Hardstop Center** mit Gründen |
| Expertenmodus | Inline in Mittelspalte | Ausklappbares Panel unten |
| Fehler-UI | Stille Leere + Toast | Sidebar-Fehler mit API-Hinweis |

## Neue Komponenten

- `frontend/src/components/partitions/PartitionWorkbenchShell.tsx`
- `frontend/src/components/partitions/PartitionDeviceSidebar.tsx`
- `frontend/src/components/partitions/PartitionHardstopCenter.tsx`
- `frontend/src/components/partitions/PartitionExpertModePanel.tsx`

## Tests & Build

- `PartitionManagerPhase2.test.ts`: **17/17** bestanden (inkl. Workbench-Tests)
- `npm run build`: **OK**

## Verbleibende Mängel

- Headless-Screenshot: API-Banner kann kurz erscheinen (Chrome-Timing); Produktiv mit Backend verbunden zeigt volle Sidebar
- Deploy auf `:3001` ausstehend (Operator)
- Globale App-Sidebar bleibt sichtbar (Setuphelfer-Chrome) — Workbench innerhalb der App, nicht Vollbild-Standalone

## Constraints bestätigt

- Keine neue API
- Keine Storage-Rollen-/Klassifikations-/Hardstop-Änderung
- Read-only, kein Queue Apply, kein Restore Execute
