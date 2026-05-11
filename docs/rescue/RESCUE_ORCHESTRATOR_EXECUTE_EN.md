# Rescue Orchestrator Execute (Phase 2, EN)

## Goal

Real restore is allowed only from a valid preview session with token-bound confirmation and repeated safety/verify checks.

## Session rules

Preview stores:
- `preview_id`
- `confirmation_token`
- `backup_path`
- `target_device`
- `target_path`
- `safety_fingerprint`
- `verify_result`
- `preview_result`
- `created_at`
- `expires_at` (15 minutes)

## Execute API

`POST /api/rescue/execute`

Stable response:
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

## Hard-stop codes

- `RESCUE_PREVIEW_SESSION_NOT_FOUND`
- `RESCUE_PREVIEW_TOKEN_INVALID`
- `RESCUE_PREVIEW_SESSION_EXPIRED`
- `RESCUE_PREVIEW_MISMATCH`
- `RESCUE_TARGET_BLOCKED`
- `RESCUE_SAFETY_CHANGED`
- `RESCUE_BACKUP_VERIFY_FAILED`
- `RESCUE_RESTORE_ENGINE_FAILED`
- `RESCUE_POST_VERIFY_FAILED`

## Selected restore path

`modules.restore_engine.restore_files` with target path constrained by `assert_restore_live_target_directory`.

Reason: existing allowlisted restore logic, no automatic partitioning/boot-repair.
