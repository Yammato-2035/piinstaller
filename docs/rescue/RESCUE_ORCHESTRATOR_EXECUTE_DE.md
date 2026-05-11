# Rescue Orchestrator Execute (Phase 2, DE)

## Ziel

Echter Restore ist möglich, aber nur aus gültiger Preview-Session mit tokengebundener Bestätigung und erneuter Safety/Verify-Prüfung.

## Session-Regeln

Preview speichert:
- `preview_id`
- `confirmation_token`
- `backup_path`
- `target_device`
- `target_path`
- `safety_fingerprint`
- `verify_result`
- `preview_result`
- `created_at`
- `expires_at` (15 Minuten)

## Execute-API

`POST /api/rescue/execute`

Response stabil:
- `code`
- `preview_id`
- `target`
- `backup`
- `safety`
- `verify`
- `restore`
- `post_verify`
- `warnings`
- `errors`

## Hard-Stop-Codes

- `RESCUE_PREVIEW_SESSION_NOT_FOUND`
- `RESCUE_PREVIEW_TOKEN_INVALID`
- `RESCUE_PREVIEW_SESSION_EXPIRED`
- `RESCUE_PREVIEW_MISMATCH`
- `RESCUE_TARGET_BLOCKED`
- `RESCUE_SAFETY_CHANGED`
- `RESCUE_BACKUP_VERIFY_FAILED`
- `RESCUE_RESTORE_ENGINE_FAILED`
- `RESCUE_POST_VERIFY_FAILED`

## Genutzter Restore-Pfad

`modules.restore_engine.restore_files` auf einem durch `assert_restore_live_target_directory` erlaubten Zielpfad.

Begründung: bestehende, allowlist-geschützte Restore-Logik ohne automatische Partitionierung/Boot-Repair.
