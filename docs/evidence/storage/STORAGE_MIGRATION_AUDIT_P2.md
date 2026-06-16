# Storage Migration Audit — P.2

## Metriken app.py (Treffer)

| Befehl | vorher (subprocess in app) | nachher |
|--------|---------------------------|---------|
| lsblk | 4 (`_lsblk_tree`×2 + `backup/targets`×2) | **0** |
| findmnt | 1 (`_findmnt_mounts`) | **0** |
| blkid | 3 (clone/disk-info) | **3** (sudo-Risiko, offen) |

## Migriert

- `_lsblk_tree` → `storage_discovery.discover_lsblk_json_tree`
- `_findmnt_mounts` → `storage_discovery.discover_findmnt_mounts_flat`
- `_flatten_findmnt_filesystems` → delegiert
- `GET /api/backup/targets` nutzt `_lsblk_tree()` statt inline lsblk

## Offen (Risiko)

- Nested `_get_fstype` in clone/disk-info (blkid + sudo)
- `_find_lsblk_by_*` Helfer (nutzen `_lsblk_tree` — indirekt migriert)
