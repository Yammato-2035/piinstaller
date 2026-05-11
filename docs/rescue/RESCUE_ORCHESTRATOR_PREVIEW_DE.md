# Rescue Orchestrator Preview (Phase 1, DE)

## Zweck

Der Orchestrator verknüpft bestehende Module für eine **Vorschau**:

1. Inspect laden
2. Safety-Gate prüfen
3. optional Preflight-Referenz prüfen
4. Backup-Datei prüfen
5. Verify basic ausführen
6. Dryrun-Pipeline aufrufen

Es findet **kein** echter Restore statt.

## API

`POST /api/rescue/preview`

Antwort (stabil):
- `code`
- `preview_id`
- `target`
- `backup`
- `safety`
- `verify`
- `preview`
- `preflight`
- `warnings`
- `errors`

## Codes

- `RESCUE_PREVIEW_CREATED`
- `RESCUE_TARGET_BLOCKED`
- `RESCUE_BACKUP_NOT_FOUND`
- `RESCUE_BACKUP_VERIFY_FAILED`
- `RESCUE_BACKUP_KEY_REQUIRED`
- `RESCUE_PREVIEW_FAILED`
- `RESCUE_PREFLIGHT_RECOMMENDED`
- `RESCUE_UNKNOWN_ERROR`
