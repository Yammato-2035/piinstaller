# Rescue UI Testmatrix — Safe Walk (2026-06-24)

**Modus:** `RESCUE_UI_SAFE_WALK=1` oder URL `?safe_walk=1`  
**Regel:** Kein Backup, Restore, Partition-Schreiben, finaler Shutdown.

## Matrix

| Bereich | Element | Sichtbar | Klickbar | Aktion im Test | Erwartung | Status |
|---|---|---|---|---|---|---|
| Startmenü | Logo (groß) | — | — | Dashboard öffnen | `data-rescue-logo`, ≥220px @768h | Workspace |
| Startmenü | Titel/Untertitel | — | — | Dashboard | Wordmark + Subtitle | Workspace |
| Startmenü | Sprache DE/EN | — | — | Toolbar Select | Locale wechselt UI | Workspace |
| Startmenü | Shutdown | — | — | Button + Dialog | Dialog OK blockiert in Safe-Walk | Workspace |
| Startmenü | Analyse | — | — | Tile → Panel | SectionPage + Analyze | Workspace |
| Startmenü | Backup | — | — | Tile → Panel | Quelle/Ziel sichtbar, kein Execute | Workspace |
| Startmenü | Restore | — | — | über Backup/System | Dry-Guard | Workspace |
| Startmenü | Partitionen | — | — | Tile → Panel | Read-only Liste | Workspace |
| Startmenü | Netzwerk/WLAN | — | — | Tile → Panel | Scan sichtbar | Workspace |
| Startmenü | Einstellungen | — | — | Tile → Panel | Sprache/Expertenmodus | Workspace |
| Startmenü | Logs/Evidence | — | — | System-Menü / System-Tile | Evidence-Hinweise | Workspace |
| Startmenü | Zurück/Home | — | — | ← in SectionPage | zurück zu Dashboard | Workspace |
| Backup | Plan erstellen | — | — | Button | Plan-API erlaubt (read-only check) | Workspace |
| Backup | Execute | — | — | — | Nicht vorhanden / blockiert | Workspace |
| Restore | Preview | — | — | Dry-run only | Kein produktives Restore | Workspace |
| Partitionen | Schreibbuttons | — | — | — | Keine aktiven Schreibaktionen | Workspace |
| Netzwerk | Connect | — | — | Optional mock | Safe-Walk: kein Pflicht-Connect | Workspace |
| Shutdown | Final | — | — | Bestätigen | Safe-Walk blockiert API-Call | Workspace |

## Safe-Walk Ausführung (Operator)

```bash
# Chromium mit Safe-Walk (Beispiel)
export RESCUE_UI_SAFE_WALK=1
# oder URL: http://127.0.0.1:8000/rescue.html?safe_walk=1

# Screenshot Evidence
./scripts/rescue-live/capture-rescue-screenshot.sh start-menu
./scripts/rescue-live/capture-rescue-screenshot.sh backup-panel
./scripts/rescue-live/capture-rescue-screenshot.sh settings
```

## Screenshot-Ziele

- API: `POST /api/rescue/ui/screenshot` `{ "label": "start-menu" }`
- Pfad: `<SETUP_LOGS>/screenshots/rescue-ui-YYYYMMDD-HHMMSS-<label>.png` + `.json`

## Gesamtstatus

| Prüfung | Status |
|---|---|
| Matrix dokumentiert | GRÜN |
| Safe-Walk Code | GRÜN (Workspace) |
| Live Safe-Walk MSI | GELB (Operator) |
