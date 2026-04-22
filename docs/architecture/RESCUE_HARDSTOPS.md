# Rescue Hard-Stops (serverseitig erzwungen)

Hard-Stops werden in `core/rescue_hardstop.py` gesammelt (`evaluate_restore_hardstops`) und in `modules/rescue_restore_execute.py` **vor** dem Schreib-Restore ausgewertet. CLI und UI können sie nicht umgehen.

## Übersicht

| Code | Bedingung |
|------|-----------|
| `rescue.hardstop.source_equals_target` | Backup-Datei und Ziel-Blockgerät liegen auf derselben Whole-Disk-Instanz (Kollisionsrisiko). |
| `rescue.hardstop.target_critical` | SMART kritisch auf dem Zielblockgerät (Re-Assessment). |
| `rescue.hardstop.target_identity_mismatch` | `target_device_identity` weicht vom Live-`lsblk`-Snapshot ab. |
| `rescue.hardstop.backup_corrupt` | Backup-Snapshot (Größe/mtime) weicht ab oder Lesen unmöglich. |
| `rescue.hardstop.invalid_key` | Entschlüsselung erforderlich/fehlgeschlagen. |
| `rescue.hardstop.session_invalid` | Authentifizierte Session passt nicht zum `remote_db`-Grant (`api/routes/rescue.py`). |
| `rescue.hardstop.no_valid_dryrun` | Spiegelung bestimmter Gate-Codes in der Restore-Antwort. |
| `rescue.hardstop.current_system_target` | Ziel ist das laufende Root-Blockgerät (`is_running_system_disk`). |

Ergänzende Detail-Codes unter `rescue.restore.*` (z. B. `backup_changed`, `key_missing`) werden parallel geliefert.

## Gate vs. Hard-Stop

- **Gate** (`rescue_restore_gate.validate_restore_preconditions`): Session, TTL, Entscheidung, Risiko-Ack, Pfad-Zeilenabgleich `backup_file` / `target_device`.
- **Hard-Stop**: frische technische Fakten (Snapshot, Identität, SMART, Mount-Herkunft des Backups).
