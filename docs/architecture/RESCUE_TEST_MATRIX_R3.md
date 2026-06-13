# Rescue Test Matrix (R.3)

## Zweck

Maschinenlesbare Ampel-Matrix bei jedem Boot/Menüstart — direkt auf dem Stick.

## Dateien

```
setuphelfer-evidence/matrix/
  rescue_test_matrix_latest.json
  rescue_test_matrix_latest.md
  rescue_test_matrix_history.jsonl
```

## Modul

`backend/core/rescue_test_matrix.py` — `RESCUE_TEST_MATRIX_VERSION = 3`.

## Testbereiche (20)

1. Boot  
2. Bootloader  
3. Stick-Persistenz  
4. TUI-Menü  
5. Grafisches Menü  
6. Browser/Kiosk  
7. React Rescue UI  
8. WLAN-Scan  
9. Netzwerk allgemein  
10. Telemetrie-Spool  
11. Telemetrie-Ingest  
12. Hardware-Erkennung MSI  
13. Interne Datenträger read-only  
14. Backup-Ziel-Erkennung  
15. Restore-Gate  
16. Partitionshelfer read-only  
17. Logs vollständig  
18. Evidence schreibbar  
19. Fehlerzusammenfassung  
20. Nächste empfohlene Aktion  

## Statuswerte

`green` | `yellow` | `red` | `gray` | `blocked` | `unknown`

## Eintrags-Schema

```json
{
  "id": "R3-BOOT-001",
  "area": "boot",
  "title": "...",
  "status": "green",
  "observed": "...",
  "evidence_path": "...",
  "risk": "low",
  "next_action": "..."
}
```

## API

- `build_rescue_test_matrix_entries()` — Einzeleinträge mit Live-Checks
- `build_rescue_test_matrix_document()` — inkl. `status_counts`
- `write_rescue_test_matrix()` — schreibt JSON, MD, JSONL
