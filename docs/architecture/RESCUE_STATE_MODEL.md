# Rescue-State-Modell (Dry-Run-Grant + Session)

## Ziele

- Ein **echter Restore** darf nicht auf lose UI-Zustände oder veraltete Client-Daten vertrauen.
- Serverseitig persistierter **Grant** koppelt Token, Session, Backup-Snapshot und Zielidentität.

## Grant-Datei

- Pfad: `/tmp/setuphelfer-rescue-dryrun-state/<token>.json` (`RESCUE_DRYRUN_STATE_DIR`).
- Lebensdauer: TTL in `rescue_restore_gate.DRYRUN_GRANT_MAX_AGE_SECONDS` (Ablauf → `rescue.restore.session_stale`).

## Felder (Auszug)

| Feld | Bedeutung |
|------|-----------|
| `session_id` | Korrelations-ID: bei authentifizierter API = DB-`sessions.id`, sonst servergenerierte UUID (`ephemeral`). |
| `session_source` | `remote_db` \| `ephemeral` — steuert Zusatzprüfung in `api/routes/rescue.py`. |
| `backup_file` | Normalisierter Pfad, muss mit Restore-Request übereinstimmen. |
| `backup_snapshot` | `{size, mtime}` für Revalidierung vor Restore. |
| `backup_requires_decryption` | Wenn true: Restore-Request muss nutzbaren Schlüssel liefern. |
| `target_device` | Optional; muss mit Restore übereinstimmen. |
| `target_device_identity` | Snapshot aus `device_identity.build_device_identity`. |
| `restore_risk_level` / `restore_decision` | Aus Dry-Run-Entscheidungslogik. |
| `dryrun_mode` / `dryrun_simulation_status` | Nur `dryrun` + `DRYRUN_OK` erlaubt Restore. |

## Token-Verbrauch

- `consume_dry_run_grant` wird **nach erfolgreicher Daten-Extraktion** aufgerufen (`rescue_restore_execute`), damit fehlgeschlagene Läufe den Grant nicht verbrauchen.

## Remote-Session

- Dry-Run mit gültigem Bearer: `session_id` ist die Remote-Session; Restore muss mit **derselben** Session erfolgen (`session_source == remote_db`).
