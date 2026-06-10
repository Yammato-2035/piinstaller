# Partitionshelfer Workbench – Ist-Analyse (Phase 3.0)

**Datum:** 2026-06-10  
**HEAD:** `3266d8f` (vor Workbench-Implementierung)  
**Version:** `1.7.13.2`  
**Branch:** `main`

## Git-Status (Auszug)

Viele unabhängige Rescue/DCC-Evidence-Änderungen im Workspace; Partitionshelfer-Code vor diesem Lauf auf Commit `a0a9469` (Modal-Defer) + Evidence `3266d8f`.

## Vergleich Ist → Ziel

| Bereich | Aktuell (vor Workbench) | Ziel (Workbench) |
|---------|-------------------------|------------------|
| Branding | `PartitionToolShell`, 3-Spalten-Grid | Eigenständige Workbench-Shell, Werkzeug-Header |
| Navigation | Datenträger oben/links als Karten-Grid | Dauerhafte linke Seitenleiste |
| Datenträger | `PartitionOverviewCards` (Karten, „Details“-Button) | `PartitionDeviceSidebar` (kompakt, Rollenfarbe) |
| Grafik | Mittlere Spalte, h-36 | Dominantes Arbeitsbereich-Element + Legende |
| Sicherheit | Rechte Spalte, Mini-Karten | Diagnose-Cockpit mit Zeilen-Dashboard |
| Restore | Unten, volle Breite | Große Handoff-Karte im Arbeitsbereich |
| Hardstops | `PartitionHardstopPanel` unter Grafik | **Hardstop Center** mit Gründen/Empfehlung |
| Expertenmodus | Toggle in Mittelspalte | Ausklappbares Panel unten (UUID, Evidence, …) |
| Layout | 12-Spalten 4/5/3 | Sidebar + Arbeitsbereich + Expertenmodus |

## Phase 0.5 – Browser-Laufwerkserkennung

### API (direkt)

| Endpunkt | HTTP | Ergebnis |
|----------|------|----------|
| `http://127.0.0.1:8000/api/partitions/scan` | 200 | 4 Datenträger (`disks[]`, `storage_roles`) |
| `http://127.0.0.1:8000/api/partitions/storage-roles` | 200 | Rollen korrekt (`backup_target`, …) |

### Browser-Port

| Port | Dienst | Bundle |
|------|--------|--------|
| `:3001` | nginx (statisch `/opt`) | `index-dS9YjSk4.js` — kann älter als Workspace sein |
| `:5174` | vite preview (Workspace-Build) | aktueller Stand |

### API-Mapping Frontend

| Prüfschritt | Ergebnis | Ursache | Maßnahme |
|-------------|----------|---------|----------|
| Backend liefert `disks` | **OK** | `fetchDisks()` nutzt `r.disks` | Keine Änderung nötig |
| Backend liefert `storage_role` auf Disk | **OK** | Feld `storage_role` in `DiskInfo` | Keine Änderung |
| CORS `:3001` → `:8000` | **OK** | `access-control-allow-origin: http://127.0.0.1:3001` | — |
| `localStorage pi-installer-api-base` | **Risiko** | Abweichende/stale URL → leere Antwort oder Timeout | Hinweis in Sidebar-Fehler |
| Fehler nur als Toast | **Bug** | Kein sichtbarer Fehlerzustand in UI | **Behoben:** `DiskLoadState` + Sidebar-Error |
| Leere API ohne Fehlertext | **Bug** | „Keine Datenträger erkannt“ ohne Kontext | **Behoben:** explizite Meldungen |
| Auto-Auswahl erster Datenträger | **Fehlte** | `selectedDisk` initial null | **Behoben:** erster Disk nach Scan |
| nginx-Bundle vs. Workspace | **Drift** | Deploy ausstehend | Operator-Deploy nach Freigabe |

### Fazit Laufwerkserkennung

**Kein API-/Klassifikationsproblem.** Backend und Mapping sind korrekt. Die Browseroberfläche wirkte leer wegen:

1. Fehlender/fehlgeschlagener API-Fetch (Timeout, stale `pi-installer-api-base`) ohne klare UI-Meldung  
2. Keine Auto-Auswahl → Arbeitsbereich blieb leer trotz geladener Disks  
3. Optional: altes nginx-Bundle auf `:3001`

## Constraints

- Keine Storage-Rollen-/Klassifikations-/Hardstop-Änderung
- Keine neue API
- Read-only Phase 3
