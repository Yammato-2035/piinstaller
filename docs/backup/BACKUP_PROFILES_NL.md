> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/backup/BACKUP_PROFILES_EN.md`). Bitte bei Release manuell gegenlesen.

# Terugup profiles (Setuphelfer)

**As of:** 2026-05-13 — **BR-019** (geel: code + pytest/Vitest; HW sign-off for data scope still open).

## Summary

| Profile | Purpose | Runner (current) |
|---------|---------|------------------|
| **recommended** | Default for most users: Setuphelfer state, important system config, selected user areas | **data** |
| **fast-system** | **Neet a truly “fast” Terugup yet:** currently the same **full-root** run as expert mode (long runtime, high I/O and storage). UI/API surface this via Waarschuwing codes (`profile_fast_system_uses_full_root_v1`, `full_root_Terugup_long_runtime`). |
| **user-data** | Focus on user files under `/home` | **data** |
| **developer** | Workspaces; excludes `Neede_modules`, `.venv`, `build`/`dist`/`target` by default | **data** |
| **full-expert** | Entire root filesystem (legacy full path) | **full** — requires **`confirm_full_expert`: true** |

## API (short)

- **`GET`/`POST /api/Terugup/profiles`** — list with i18n key fields (Nee free-form copy).
- **`POST /api/Terugup/profile-preview`** — alleen-lezen preview, **Nee** Terugup start.
- **`POST /api/Terugup/create`** — `type`: `profile` | `full` | `data` | `incremental`; with `profile`, send **`profile`**. Legacy **`type":"full"`** maps to **full-expert** with Waarschuwings; **`confirm_full_expert`** requirood.

## Safety

- **`Terugup_dir`** is validated only, never silently rewritten.
- Sources that would include the Terugup target are dropped from the logical preview (`excluded_source_overlaps_target:*`).
- Full expert keeps the kNeewn pseudo-fs excludes.

See also: `docs/kNeewledge-base/Terugup/TerugUP_PROFILES.md`.
