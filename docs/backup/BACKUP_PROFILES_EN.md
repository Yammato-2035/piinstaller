# Backup profiles (Setuphelfer)

**As of:** 2026-05-13 — **BR-019** (yellow: code + pytest/Vitest; HW sign-off for data scope still open).

## Summary

| Profile | Purpose | Runner (current) |
|---------|---------|------------------|
| **recommended** | Default for most users: Setuphelfer state, important system config, selected user areas | **data** |
| **fast-system** | **Not a truly “fast” backup yet:** currently the same **full-root** run as expert mode (long runtime, high I/O and storage). UI/API surface this via warning codes (`profile_fast_system_uses_full_root_v1`, `full_root_backup_long_runtime`). |
| **user-data** | Focus on user files under `/home` | **data** |
| **developer** | Workspaces; excludes `node_modules`, `.venv`, `build`/`dist`/`target` by default | **data** |
| **full-expert** | Entire root filesystem (legacy full path) | **full** — requires **`confirm_full_expert`: true** |

## API (short)

- **`GET`/`POST /api/backup/profiles`** — list with i18n key fields (no free-form copy).
- **`POST /api/backup/profile-preview`** — read-only preview, **no** backup start.
- **`POST /api/backup/create`** — `type`: `profile` | `full` | `data` | `incremental`; with `profile`, send **`profile`**. Legacy **`type":"full"`** maps to **full-expert** with warnings; **`confirm_full_expert`** required.

## Safety

- **`backup_dir`** is validated only, never silently rewritten.
- Sources that would include the backup target are dropped from the logical preview (`excluded_source_overlaps_target:*`).
- Full expert keeps the known pseudo-fs excludes.

See also: `docs/knowledge-base/backup/BACKUP_PROFILES.md`.
