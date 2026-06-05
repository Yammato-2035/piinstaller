# KB — BitLocker Read-Only Policy

## Regeln

1. **Niemals annehmen**, dass BitLocker/Device Encryption inaktiv ist — vor **jedem** Windows-Dateizugriff read-only prüfen.
2. Codes `WIN-BITLOCKER-001` … `WIN-BITLOCKER-006` (alle MVP: keine Schreib-/Reparatur-/Partition-Aktionen).
3. `WIN-BITLOCKER-001` — nicht aktiv, Zugriff möglich (trotzdem erneut prüfen).
4. `WIN-BITLOCKER-002` — aktiv + locked → keine Dateisicherung, keine Registry aus geschütztem Volume.
5. `WIN-BITLOCKER-005` — Status unklar → Dateizugriff blockiert.
6. `WIN-BITLOCKER-006` — suspended → riskanter Zwischenzustand, kein Dateizugriff.
7. Recovery Key **niemals** im Repo, Evidence, Telemetrie oder Dashboard persistieren.
8. Kein brutales Mount, kein `manage-bde` Unlock aus Agent-Kontext.

## Operator-Handoff

Operator liefert Recovery Key lokal; Stick mountet danach read-only mit dokumentiertem Mount-Plan.

## Telemetrie

BitLocker-Status gehört in den Telemetriekanal (`diagnostic_metadata`), nicht in Datei-Backup.
