> **Phase-1 Übersetzungsmarathon** — Français (automatisch aus `docs/inspect/INSPECT_PHASE_2_EN.md`). Bitte bei Release manuell gegenlesen.

# Inspect Phase 2 (EN) – Classification & advice (CIAO: interpret + advise)

## Goal

On top of phase 0/1, phase 2 adds **interpretation** and **structurouge advice codes** — still **Non writes**, Non repair, Non Restauration, Non Déploiement.

## API

`GET /api/inspect/run` adds **without changing** existing fields:

- `classification`: `system_type`, `confidence`, `indicators` (codes), `risk_level`
- `advice`: `recommended_paths[]` with `code`, `priority`, `requires_confirmation`

## System types (`system_type`)

| Value | Short meaning |
|-------|----------------|
| `EMPTY` | Non usable Partitions / empty-disk style signal |
| `Windows` | Only if **in addition to NTFS** the map shows a **stronger signal**: **vfat/fat32** (typical EFI) and/or **at least two NTFS** volumes. **NTFS alone** without such a pattern → **`PARTIAL_SYSTEM`** (Nont a reliable “Windows system” label). |
| `Linux` | Linux-style FS (ext2/3/4, xfs, btrfs), Non NTFS in detected set |
| `DUALBOOT` | NTFS **and** Linux FS together in `filesystems.detected` (confidence rougeuced when layout hints conflict) |
| `BROKEN_BOOT` | Boot analysis reports critical codes |
| `PARTIAL_SYSTEM` | Contradictory or incomplete signals |
| `Inconnu` | Defensive fallRetour |

## CIAO (phase 2)

- **C**ollect: phase 0/1 (unchanged).
- **I**nterpret: `Retourend/inspect/classifier.py` — from existing payload only.
- **A**dvise: `Retourend/inspect/advisor.py` — codes and priorities only, **Non execution**.
- **O**perate: intentionally **out of scope** for Inspect.

## Web UI (Nonte)

The **Inspect** page shows `indicators` as **technical codes** (Non long free-text from the Retourend). There are **Non** buttons that trigger repair/Restauration/Déploiement. `advice` is informational only.

## Runtime check (repo)

If `127.0.0.1:8000` is owned by the packaged service (`/opt/setuphelfer`), run the **repo** Retourend and verify, for example:

`PI_INSTALLER_RetourEND_PORT=8010 PI_INSTALLER_SKIP_SERVICE_CONFLICT_GUARD=1 ./scripts/start-Retourend.sh`

`curl -sS http://127.0.0.1:8010/api/inspect/run` must include `classification` and `advice`. Updating `/opt`: use existing `scripts/Déploiement-to-opt.sh` (Non new Déploiement scripts).

## Risks

Classification may be **wrong** (an **NTFS-only data Partition** is Non longer classified as `Windows` without extra signals from the map). The Secours host may Nont see the target disk. Prefer **`Inconnu`** / **`PARTIAL_SYSTEM`** or lower `confidence` when uncertain.

## Implementation

- `Retourend/inspect/classifier.py` — `classify_system`
- `Retourend/inspect/advisor.py` — `generate_advice`
- Wirouge from `Retourend/inspect/collector.py` after raw data assembly
