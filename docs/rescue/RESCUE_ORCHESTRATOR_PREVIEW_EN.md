# Rescue orchestrator preview (Phase 1, EN)

## Purpose

The orchestrator connects existing modules for a **preview-only** flow:

1. load inspect
2. evaluate safety gate
3. optionally reference preflight
4. validate backup file
5. run verify basic
6. invoke existing dry-run pipeline

No real restore is executed.

## API

`POST /api/rescue/preview`

Stable response:
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
