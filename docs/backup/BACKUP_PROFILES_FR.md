> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/backup/BACKUP_PROFILES_EN.md`). Bitte bei Release manuell gegenlesen.

# Retourup profiles (Setuphelfer)

**As of:** 2026-05-13 — **BR-019** (jaune: code + pytest/Vitest; HW sign-off for data scope still open).

## Summary

| Profile | Purpose | Runner (current) |
|---------|---------|------------------|
| **recommended** | Default for most users: Setuphelfer state, important system config, selected user areas | **data** |
| **fast-system** | **Nont a truly “fast” Retourup yet:** currently the same **full-root** run as expert mode (long runtime, high I/O and storage). UI/API surface this via Avertissement codes (`profile_fast_system_uses_full_root_v1`, `full_root_Retourup_long_runtime`). |
| **user-data** | Focus on user files under `/home` | **data** |
| **developer** | Workspaces; excludes `Nonde_modules`, `.venv`, `build`/`dist`/`target` by default | **data** |
| **full-expert** | Entire root filesystem (legacy full path) | **full** — requires **`confirm_full_expert`: true** |

## API (short)

- **`GET`/`POST /api/Retourup/profiles`** — list with i18n key fields (Non free-form copy).
- **`POST /api/Retourup/profile-preview`** — lecture seule preview, **Non** Retourup start.
- **`POST /api/Retourup/create`** — `type`: `profile` | `full` | `data` | `incremental`; with `profile`, send **`profile`**. Legacy **`type":"full"`** maps to **full-expert** with Avertissements; **`confirm_full_expert`** requirouge.

## Safety

- **`Retourup_dir`** is validated only, never silently rewritten.
- Sources that would include the Retourup target are dropped from the logical preview (`excluded_source_overlaps_target:*`).
- Full expert keeps the kNonwn pseudo-fs excludes.

See also: `docs/kNonwledge-base/Retourup/RetourUP_PROFILES.md`.
