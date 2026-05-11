# Inspect Phase 2 (EN) – Classification & advice (CIAO: interpret + advise)

## Goal

On top of phase 0/1, phase 2 adds **interpretation** and **structured advice codes** — still **no writes**, no repair, no restore, no deploy.

## API

`GET /api/inspect/run` adds **without changing** existing fields:

- `classification`: `system_type`, `confidence`, `indicators` (codes), `risk_level`
- `advice`: `recommended_paths[]` with `code`, `priority`, `requires_confirmation`

## System types (`system_type`)

| Value | Short meaning |
|-------|----------------|
| `EMPTY` | No usable partitions / empty-disk style signal |
| `WINDOWS` | Only if **in addition to NTFS** the map shows a **stronger signal**: **vfat/fat32** (typical EFI) and/or **at least two NTFS** volumes. **NTFS alone** without such a pattern → **`PARTIAL_SYSTEM`** (not a reliable “Windows system” label). |
| `LINUX` | Linux-style FS (ext2/3/4, xfs, btrfs), no NTFS in detected set |
| `DUALBOOT` | NTFS **and** Linux FS together in `filesystems.detected` (confidence reduced when layout hints conflict) |
| `BROKEN_BOOT` | Boot analysis reports critical codes |
| `PARTIAL_SYSTEM` | Contradictory or incomplete signals |
| `UNKNOWN` | Defensive fallback |

## CIAO (phase 2)

- **C**ollect: phase 0/1 (unchanged).
- **I**nterpret: `backend/inspect/classifier.py` — from existing payload only.
- **A**dvise: `backend/inspect/advisor.py` — codes and priorities only, **no execution**.
- **O**perate: intentionally **out of scope** for Inspect.

## Web UI (note)

The **Inspect** page shows `indicators` as **technical codes** (no long free-text from the backend). There are **no** buttons that trigger repair/restore/deploy. `advice` is informational only.

## Runtime check (repo)

If `127.0.0.1:8000` is owned by the packaged service (`/opt/setuphelfer`), run the **repo** backend and verify, for example:

`PI_INSTALLER_BACKEND_PORT=8010 PI_INSTALLER_SKIP_SERVICE_CONFLICT_GUARD=1 ./scripts/start-backend.sh`

`curl -sS http://127.0.0.1:8010/api/inspect/run` must include `classification` and `advice`. Updating `/opt`: use existing `scripts/deploy-to-opt.sh` (no new deploy scripts).

## Risks

Classification may be **wrong** (an **NTFS-only data partition** is no longer classified as `WINDOWS` without extra signals from the map). The rescue host may not see the target disk. Prefer **`UNKNOWN`** / **`PARTIAL_SYSTEM`** or lower `confidence` when uncertain.

## Implementation

- `backend/inspect/classifier.py` — `classify_system`
- `backend/inspect/advisor.py` — `generate_advice`
- Wired from `backend/inspect/collector.py` after raw data assembly
