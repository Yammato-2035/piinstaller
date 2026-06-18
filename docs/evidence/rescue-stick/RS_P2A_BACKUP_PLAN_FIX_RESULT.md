# RS-P2A Backup Plan Fix Result

- Repack rsynct jetzt vollständiges `backend/` + alle Rescue-Scripts
- `disk-discovery.py` schreibt immer JSON (auch bei Fehler)
- `plan-builder.py` liefert `disk_discovery_missing` statt Crash
- `build_rescue_backup_plan`: `disk_discovery_null_with_devices` Fehlercode
- **runtime_validated:** yellow — MSI-Retest RS-P2B
