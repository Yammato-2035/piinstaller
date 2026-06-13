# Storage Discovery Audit — P.1

**Datum:** 2026-06-10  
**HEAD (Start):** 23462c1  
**Referenz G.10:** lsblk/findmnt/blkid-Duplikate

## Inventar (backend, ohne tests/venv)

| Befehl | Dateien | Treffer (Zeilen) |
|--------|---------|------------------|
| `lsblk` | 29 | 12 in `app.py`, 3 in `storage_detection`, 2 in `storage_facade`, … |
| `findmnt` | 23 | 8 in `app.py`, 7 in `safe_device`, 2 in `mount_facade`, … |
| `blkid` | 14 | 3 in `app.py`, 4 in `storage_detection`, 6 in `storage_facade`, … |

## Canonical Owner (neu)

`backend/core/storage_discovery.py` — `STORAGE_DISCOVERY_VERSION = 1`

Delegiert an:
- `modules.storage_detection` (lsblk, blkid)
- `core.mount_facade` (findmnt)

## Sichere Migrationen (durchgeführt)

| Datei | Änderung |
|-------|----------|
| `storage_facade.py` | `detect_block_devices`/`detect_filesystems` → `storage_discovery.discover_*` |

## Nicht migriert (Risiko)

| Datei | Grund |
|-------|-------|
| `app.py` (_lsblk_tree, _findmnt_mounts, blkid) | großer Monolith-Block, Backup/Partition-Routen |
| `safe_device.py` | Safety-kritisch, eigener Owner |
| `rescue_*` / `deploy/runner_*` | Rescue/Deploy-Scope, nicht P.1 |
| `modules/inspect_storage.py` | Inspect-Pipeline, separates Slice |

## Matrix

Siehe `docs/architecture/STORAGE_DISCOVERY_OWNERSHIP_MATRIX.md`

## Tests

`test_storage_discovery_v1`
