# Write safety (EN)

## Purpose

Protects future write paths (restore, deploy, partitioning) using **read-only** evaluation of existing Inspect data. **No** write operations and **no** override workflow in this phase.

## Modules

- `backend/safety/write_guard.py` — `evaluate_write_target(device, inspect_result)`, `build_write_safety_summary(inspect_result)`
- API: `GET /api/safety/targets` — per disk: `device`, `size`, `classification` (`allowed`|`warning`|`blocked`), `write_allowed`, `reason_code`
- Inspect: optional field `write_safety_summary` (targets include extra evaluation fields)

## Reason codes

| Code | Short meaning |
|------|----------------|
| `SAFETY_SYSTEM_DISK` | System disk / root mount |
| `SAFETY_LIVE_SYSTEM` | Live/install medium |
| `SAFETY_UNKNOWN_DEVICE` | Device missing or ambiguous |
| `SAFETY_WINDOWS_DETECTED` | NTFS-centric layout without clear backup pattern |
| `SAFETY_DUALBOOT` | NTFS and Linux FS on the same disk |
| `SAFETY_EMPTY_DISK` | Empty / unpartitioned (defensive allow) |
| `SAFETY_BACKUP_TARGET_OK` | All partitions marked `backup_candidate` |

## Limits

- No Microsoft-path probing; NTFS-only does **not** grant writes (`SAFETY_WINDOWS_DETECTED` keeps writes blocked).
- `requires_override` is informational only — **no** bypass UI in phase 1.

## Next phase

Wire into restore/deploy flows; still no silent writes.
