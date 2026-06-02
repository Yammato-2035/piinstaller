# Rescue ISO Build-Tree Cleanup — Phase 0

**Stand:** 2026-06-02  
**HEAD:** `e77b83d`  
**Branch:** `main`

## Runtime (readonly)

| Feld | Wert |
|------|------|
| `install_profile` | **release** |
| `profile_gate_status` | **green** |

## Precheck vorher

| Feld | Wert |
|------|------|
| Precheck-Status | **review_required** |
| `chroot_mount_status` | **blocked_by_root_owned_leftovers** |
| `root_owned_count` (Preflight) | **31501** |
| Aktive Mounts | **keine** |

## Stale Artefakte vorher

| Artefakt | Anmerkung |
|----------|-----------|
| `binary.hybrid.iso` | ~512 MB, Prior-Build 2026-06-01 |
| `binary/live/filesystem.squashfs` | stale — validate FORBIDDEN |
| `chroot/`, `cache/`, `.build/`, `binary/` | root-owned Reste |

## Bewertung

**`cleanup_required=true`**

Log-Referenz (Operator-Terminal 6): Dry-Run + Clean 2026-06-02T20:44:56+02:00
