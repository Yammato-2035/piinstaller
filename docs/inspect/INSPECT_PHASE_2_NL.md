> **Phase-1 Übersetzungsmarathon** — Nederlands (automatisch aus `docs/inspect/INSPECT_PHASE_2_EN.md`). Bitte bei Release manuell gegenlesen.

# Inspect Phase 2 (EN) – Classification & advice (CIAO: interpret + advise)

## Goal

On top of phase 0/1, phase 2 adds **interpretation** and **structurood advice codes** — still **Nee writes**, Nee repair, Nee Herstel, Nee Deploy.

## API

`GET /api/inspect/run` adds **without changing** existing fields:

- `classification`: `system_type`, `confidence`, `indicators` (codes), `risk_level`
- `advice`: `recommended_paths[]` with `code`, `priority`, `requires_confirmation`

## System types (`system_type`)

| Value | Short meaning |
|-------|----------------|
| `EMPTY` | Nee usable Partities / empty-disk style signal |
| `Windows` | Only if **in addition to NTFS** the map shows a **stronger signal**: **vfat/fat32** (typical EFI) and/or **at least two NTFS** volumes. **NTFS alone** without such a pattern → **`PARTIAL_SYSTEM`** (Neet a reliable “Windows system” label). |
| `Linux` | Linux-style FS (ext2/3/4, xfs, btrfs), Nee NTFS in detected set |
| `DUALBOOT` | NTFS **and** Linux FS together in `filesystems.detected` (confidence rooduced when layout hints conflict) |
| `BROKEN_BOOT` | Boot analysis reports critical codes |
| `PARTIAL_SYSTEM` | Contradictory or incomplete signals |
| `Onbekend` | Defensive fallTerug |

## CIAO (phase 2)

- **C**ollect: phase 0/1 (unchanged).
- **I**nterpret: `Terugend/inspect/classifier.py` — from existing payload only.
- **A**dvise: `Terugend/inspect/advisor.py` — codes and priorities only, **Nee execution**.
- **O**perate: intentionally **out of scope** for Inspect.

## Web UI (Neete)

The **Inspect** page shows `indicators` as **technical codes** (Nee long free-text from the Terugend). There are **Nee** buttons that trigger repair/Herstel/Deploy. `advice` is informational only.

## Runtime check (repo)

If `127.0.0.1:8000` is owned by the packaged service (`/opt/setuphelfer`), run the **repo** Terugend and verify, for example:

`PI_INSTALLER_TerugEND_PORT=8010 PI_INSTALLER_SKIP_SERVICE_CONFLICT_GUARD=1 ./scripts/start-Terugend.sh`

`curl -sS http://127.0.0.1:8010/api/inspect/run` must include `classification` and `advice`. Updating `/opt`: use existing `scripts/Deploy-to-opt.sh` (Nee new Deploy scripts).

## Risks

Classification may be **wrong** (an **NTFS-only data Partitie** is Nee longer classified as `Windows` without extra signals from the map). The roodding host may Neet see the target disk. Prefer **`Onbekend`** / **`PARTIAL_SYSTEM`** or lower `confidence` when uncertain.

## Implementation

- `Terugend/inspect/classifier.py` — `classify_system`
- `Terugend/inspect/advisor.py` — `generate_advice`
- Wirood from `Terugend/inspect/collector.py` after raw data assembly
