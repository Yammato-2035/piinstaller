# Kontrollierter echter Restore (Phase 3 + Nachschärfung 3.N)

## Ablauf (Überblick)

1. **Dry-Run** (`POST /api/rescue/restore-dryrun`, Modus `dryrun`) → Antwort enthält bei Erfolg `dry_run_token`, `allow_restore: true` und **`session_id`** (Bindung, siehe `docs/architecture/RESCUE_STATE_MODEL.md`).
2. **Ziel vorbereiten**: Leeres Verzeichnis unter einem erlaubten Live-Präfix (`core/rescue_allowlist.RESCUE_LIVE_RESTORE_PREFIXES`), optional Blockgerät gemountet.
3. **Restore** (`POST /api/rescue/restore`) mit **`session_id`**, Token, `confirmation: true`, Bestätigungs-`phrase`, bei YELLOW `risk_acknowledged: true`.
4. **Logging / Audit**: Append-Log `/tmp/setuphelfer-rescue-restore.log`; JSON `/tmp/setuphelfer-rescue-restore-report.json` und Markdown `/tmp/setuphelfer-rescue-restore-report.md` mit **Stages**, Hard-Stops, Session-Metadaten (keine Secrets).

## Interne Stufen (`rescue_restore_execute`)

| Stage | Inhalt |
|-------|--------|
| `PRECONDITION_CHECK` | Gate (`validate_restore_preconditions`), Phrase, System-Disk-Schutz, Allowlist-Pfade |
| `TARGET_REVALIDATION` | Leerheit, Mount↔`target_device` |
| `BACKUP_REVALIDATION` | `verify_basic` (Kurzprüfung) |
| `HARDSTOP_EVALUATION` | `core/rescue_hardstop.evaluate_restore_hardstops` (Snapshot, Identität, SMART, Quelle=Ziel, Schlüsselpflicht) |
| `TARGET_PREPARATION` | Entschlüsselung ggf. in Arbeitsverzeichnis |
| `DATA_RESTORE` | `restore_engine.restore_files` |
| `BOOT_PREPARATION_OR_REPAIR` | `rescue_boot_repair.run_boot_repair_pipeline` (modular, siehe `BOOT_REPAIR.md`) |
| `POST_RESTORE_VALIDATION` | Verzeichnisse + `analyze_boot_status` |
| `FINAL_RESULT` | Ergebnisklassifikation |

Fehler in einer Stage **stoppen** den weiteren Ablauf (kein stilles Weiterlaufen).

## API

- `POST /api/rescue/restore-dryrun` — optional mit Remote-Session (`Authorization: Bearer`); dann wird `session_id` = DB-Session-ID gesetzt und im Grant `session_source: remote_db` vermerkt.
- `POST /api/rescue/restore` — Body `RescueRestoreRequest` inkl. **`session_id`**. Bei `remote_db`-Grant muss dieselbe authentifizierte Session den Restore aufrufen.
- `RescueRestoreResponse.result`: `RESTORE_SUCCESS` | `RESTORE_SUCCESS_WITH_WARNINGS` | `RESTORE_PARTIAL` | `RESTORE_FAILED` | **`RESTORE_BLOCKED`**.

## Zielidentität

- Beim Dry-Run wird `target_device_identity` per `core/device_identity.build_device_identity` im Grant gespeichert.
- Vor Restore: erneuter Abgleich — Abweichung → `rescue.hardstop.target_identity_mismatch` / `rescue.restore.target_*`.

## Sicherheits-Geländer

- Kein Start ohne gültigen Grant + passende **`session_id`** (TTL `DRYRUN_GRANT_MAX_AGE_SECONDS` in `rescue_restore_gate.py`).
- Hard-Stops: `docs/architecture/RESCUE_HARDSTOPS.md`.
- **Token-Verbrauch** erst nach **erfolgreichem** `DATA_RESTORE` (kein Verlust bei Extraktionsfehler).
- Boot-Reparatur nur mit `target_device` und nur auf dem Ziel-Root.

## CLI

```bash
python3 scripts/rescue_mode.py --restore-dryrun-backup /pfad/archiv.tar.gz --json-stdout   # session_id aus JSON lesen

python3 scripts/rescue_mode.py --restore-live --restore-dryrun-backup /pfad/archiv.tar.gz \
  --restore-target-dir /tmp/setuphelfer-rescue-restore-test/leer \
  --dry-run-token '<token>' --session-id '<session_id>' \
  --phrase RESTORE_NO_BLOCK_DEVICE --yes [--risk-ack] [--perform-boot-repair]
```

## Grenzen

- Kein vollautomatisches Rollback bei Teilfehlern.
- Bootfähigkeit und Boot-Reparatur bleiben heuristisch; siehe `BOOT_COMPATIBILITY_LIMITATIONS.md`.
